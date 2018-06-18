import json
from dateutil.parser import parse as parse_date
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .view_helper import *
from .models import CoinbaseEvent, PriceData
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
    return redirect("/purchase/")
    
@require_account_name
@require_public_key
def purchase(request):
    return render(request, "buy/purchase.html", {
        'account_name': request.account_name,
        'public_key': request.public_key,
        'price_usd': get_account_price_usd(),
    })
    
@require_account_name
@require_public_key
def buy_action(request):
    j = create_charge(request.account_name, request.public_key, get_account_price_usd())
    hosted_url = j['data']['hosted_url']
    p, created = Purchase.objects.get_or_create(
        account_name=request.account_name, 
        defaults=dict(
            public_key=request.public_key, 
            coinbase_charge=json.dumps(j),
            coinbase_code=j['data']['code'],
            user_uuid=request.session['uuid'],
        )
    )
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
def success(request):
    p = Purchase.objects.get(
            account_name=request.account_name, 
            public_key=request.public_key,
            coinbase_code=request.session['coinbase_code'],
        )
    return render(request, "buy/success.html", {
        'purchase': p,
    })

@csrf_exempt
@require_account_name
@require_public_key
def check_progress(request):
    p = Purchase.objects.get(
        account_name=request.account_name, 
        public_key=request.public_key,
        coinbase_code=request.session['coinbase_code'],
    )
    return JsonResponse({
        'purchase': p.as_json(),
    })

@require_POST
def delete(request):
    account_name = request.POST['account_name']
    user_uuid = uuid.UUID(request.session['uuid'])
    Purchase.objects.filter(account_name=account_name, user_uuid=user_uuid).delete()
    return HttpResponse("okay")
