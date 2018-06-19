import json
from dateutil.parser import parse as parse_date
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .view_helper import *
from .models import CoinbaseEvent, PriceData, StripeCharge
from .coinbase import *
from django.http import JsonResponse
from django.utils import timezone
    
def index(request):
    user_uuid = request.session.get('uuid')
    if user_uuid:
        purchases = Purchase.objects.filter(user_uuid=user_uuid).order_by('-created_at')
    else:
        purchases = []
    return render(request, "buy/index.html", {
        'purchases': purchases,
        'price_usd': get_account_price_usd(),
    })
    
# Create your views here.
def choose(request):
    return render(request, "buy/choose.html")
    
@require_POST
def submit_account_name(request):
    account_name = request.POST['account_name']
    # test if valid eos account name
    if not is_valid_account_name(account_name):
        return redirect('account_name_invalid', account_name=account_name)
    
    # check if eos account name is still free
    if not is_eos_account_available(account_name):
        return redirect('account_not_available', account_name=account_name)
    
    # add chosen account name to session
    request.session['account_name'] = account_name
    
    # if successful, redirect to /keys/
    return redirect("/keys/")

@require_account_name    
def keys(request):
    return render(request, "buy/keys.html", {
        'account_name': request.account_name,
    })
    
@require_account_name
def submit_public_key(request):
    public_key = request.POST['public_key']
    request.session['public_key'] = public_key
    
    p, created = Purchase.objects.get_or_create(
        account_name=request.account_name, 
        defaults=dict(
            public_key=public_key, 
            user_uuid=request.session['uuid'],
            price_cents=get_account_price_usd_cents(),
            currency='usd',
        )
    )
    
    return redirect("/purchase/")
    
@require_account_name
@require_public_key
@require_purchase
def purchase(request):
    return render(request, "buy/purchase.html", {
        'purchase': request.purchase,
    })
    
@require_account_name
@require_public_key
@require_purchase
def buy_action(request):
    j = create_charge(request.account_name, request.public_key, request.purchase.price_cents)
    hosted_url = j['data']['hosted_url']
    request.session['coinbase_code'] = j['data']['code']
    return redirect(hosted_url)
    
@csrf_exempt
def webhook(request):
    check_coinbase_signature(request)
    
    j = json.loads(request.body.decode('utf-8'))
    event = j['event']
    CoinbaseEvent.objects.update_or_create(
        uuid=event['id'],
        defaults=dict(
            event_type=event['type'],
            created_at=parse_date(event['created_at']),
            api_version=event['api_version'],
            data=json.dumps(event['data']),
        )
    )
    
    if event['type'] == 'charge:confirmed':
        metadata = event['data']['metadata']
        public_key = metadata['public_key']
        account_name = metadata['account_name']
        code = event['data']['code']
        try:
            p = Purchase.objects.get(
                account_name=account_name,
                public_key=public_key,
                coinbase_code=code,
            )
            if not p.payment_received:
                p.payment_received = True
                p.payment_received_at = timezone.now()
                p.save()
            if not p.account_created:
                p.complete_purchase_and_save()
        except Purchase.DoesNotExist:
            pass
        
    
    return HttpResponse("thanks")

@require_account_name
@require_public_key
@require_purchase
def success(request):
    return render(request, "buy/success.html", {
        'purchase': request.purchase,
    })

@csrf_exempt
@require_account_name
@require_public_key
@require_purchase
def check_progress(request):
    return JsonResponse({
        'purchase': request.purchase.as_json(),
    })


@require_POST
@require_account_name
@require_public_key
@require_purchase
def stripe_charge(request):
    import stripe
    token = request.POST['token']
    stripe.api_key = settings.STRIPE_API_KEY
    charge = stripe.Charge.create(
        amount=request.purchase.price_cents,
        currency=request.purchase.currency,
        description="Your personal EOS account: %s" % request.purchase.account_name,
        source=token,
        metadata={
            'account_name': request.purchase.account_name,
            'public_key': request.purchase.public_key,
        },
    )
    sc = StripeCharge.objects.create(
        price_cents = request.purchase.price_cents,
        currency=request.purchase.currency,
        response = str(charge),
        purchase = request.purchase,
        user_uuid = request.session['uuid']
    )
    assert charge['amount'] == request.purchase.price_cents
    assert charge['currency'] == request.purchase.currency
    assert charge['metadata']['account_name'] == request.purchase.account_name
    
    if charge["paid"] and charge["outcome"]["type"] == "authorized":
        p = request.purchase
        if not p.payment_received:
            p.payment_received = True
            p.payment_received_at = timezone.now()
            p.save()
        if not p.account_created:
            p.complete_purchase_and_save()
    else: # Credit Card was declined
        redirect("/card_declined/", stripe_charge=sc.id)        
    return HttpResponse("ok")
    
def card_declined(request, stripe_charge):
    stripe_charge = StripeCharge.objects.get(id=stripe_charge, user_uuid=request.session['user_uuid'])
    j = json.loads(stripe_charge.response)
    j['outcome']['seller_message']
    return render(request, "buy/card_declined.html", {
        'seller_message': seller_message,
    })