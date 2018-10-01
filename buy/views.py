import json
from django.conf import settings
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
from django.views.decorators.cache import cache_page

def add_price_context_processor(request):
    return {
        'price_usd_crypto': '%.2f' % Purchase.get_prices_usd_crypto(),
        'price_usd_credit': '%.2f' % Purchase.get_prices_usd_credit(),
        'price_eos_eos': '%.1f' % PriceData.minimum_amount_sac(),
        'eos_endpoint': settings.EOS_API_NODES[0],
    }

# @cache_page(settings.CACHING_DURATION)
def index(request):
    return render(request, "buy/index.html")

def update_permissions(request):
    return render(request, "buy/update_permissions.html")
    
# @cache_page(settings.CACHING_DURATION)
def choose(request):
    return render(request, "buy/choose.html", {
        'breadcrumbs_account_name': True,
    })

# csrf disabled so we can cache the choose view (this view is not security-relevant)
@csrf_exempt
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
        'breadcrumbs_public_keys': True,
        'breadcrumbs_choose_finished': True,
        'blacklist': json.dumps(settings.BURNED_KEYS),
    })
    
@require_account_name
def submit_public_key(request):
    active_key = request.POST['active_key']
    owner_key = request.POST['owner_key']
    active_key = request.POST['active_key'].strip()
    owner_key = request.POST['owner_key'].strip()
    
    assert (is_valid_public_key(owner_key) and is_valid_public_key(active_key)), "Invalid public keys provided"
    
    request.session['active_key'] = active_key
    request.session['owner_key'] = active_key

    p, created = Purchase.objects.update_or_create(
        account_name=request.account_name, 
        defaults=dict(
            owner_key=owner_key, 
            active_key=active_key, 
            user_uuid=request.session['uuid'],
            currency='usd',
        )
    )
    if not created:
        p.update_price()
        p.save()
    return redirect("/purchase/")
    
@require_account_name
@require_public_keys
@require_purchase
def purchase(request):
    return render(request, "buy/purchase.html", {
        'purchase': request.purchase,
        'uuid': request.session['uuid'],
        'breadcrumbs_payment': True,
        'breadcrumbs_choose_finished': True,
        'breadcrumbs_keys_finished': True,
    })


@require_POST
def buy_action(request):
    purchase, created = Purchase.objects.update_or_create(
        account_name=request.POST['account_name'], 
        defaults=dict(
            owner_key=request.POST['owner_key'], 
            active_key=request.POST['active_key'], 
            user_uuid=request.POST['uuid'],
        )
    )
    if request.POST['payment'] == 'crypto':
        j = create_charge(purchase.account_name, purchase.owner_key, purchase.active_key, purchase.price_usd_crypto())
        hosted_url = j['data']['hosted_url']
        request.session['coinbase_code'] = j['data']['code']
        purchase.coinbase_code = j['data']['code']
        purchase.coinbase = timezone.now()
        purchase.save()
        return redirect(hosted_url)
    elif request.POST['payment'] == 'eos':
        return redirect('/eos/')
        
@csrf_exempt
def webhook(request):
    check_coinbase_signature(request)
    
    j = json.loads(request.body.decode('utf-8'))
    event = j['event']
    c, created = CoinbaseEvent.objects.update_or_create(
        uuid=event['id'],
        defaults=dict(
            event_type=event['type'],
            created_at=parse_date(event['created_at']),
            api_version=event['api_version'],
            data=json.dumps(event['data']),
        )
    )
    
    c.process()
        
    
    return HttpResponse("thanks")

@require_account_name
@require_public_keys
@require_purchase
def success(request):
    return render(request, "buy/success.html", {
        'purchase': request.purchase,
        'breadcrumbs_choose_finished': True,
        'breadcrumbs_keys_finished': True,
        'breadcrumbs_purchase_finished': True,
    })

@csrf_exempt
@require_account_name
@require_public_keys
@require_purchase
def check_registration_status(request):
    request.purchase.update_registration_status()
    return HttpResponse("ok")

@csrf_exempt
@require_account_name
@require_public_keys
@require_purchase
def check_progress(request):
    return JsonResponse({
        'purchase': request.purchase.as_json(),
    })

@require_POST
@require_account_name
@require_public_keys
@require_purchase
def stripe(request):
    request.purchase.stripe = timezone.now()
    request.purchase.save()
    return HttpResponse("ok")
    
@require_POST
def stripe_charge(request):
    import stripe
    request.purchase, created = Purchase.objects.update_or_create(
        account_name=request.POST['account_name'], 
        defaults=dict(
            owner_key=request.POST['owner_key'], 
            active_key=request.POST['active_key'], 
            user_uuid=request.POST['uuid'],
        )
    )
    token = request.POST['token']
    stripe.api_key = settings.STRIPE_API_KEY
    charge = stripe.Charge.create(
        amount=request.purchase.price_cents_credit,
        currency='usd',
        description="Your personal EOS account: %s" % request.purchase.account_name,
        source=token,
        metadata={
            'account_name': request.purchase.account_name,
            'owner_key': request.purchase.owner_key,
            'active_key': request.purchase.active_key,
        },
    )
    sc = StripeCharge.objects.create(
        price_cents = request.purchase.price_cents_credit,
        currency=request.purchase.currency,
        response = str(charge),
        purchase = request.purchase,
        user_uuid = request.session['uuid']
    )
    assert charge['amount'] == request.purchase.price_cents_credit
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
    
@require_account_name
@require_public_keys
@require_purchase
def eos(request):
    request.purchase.regaccount()
    return render(request, "buy/eos.html", {
        'purchase': request.purchase,
        'minimum': PriceData.minimum_amount_sac(),
    })
    
    