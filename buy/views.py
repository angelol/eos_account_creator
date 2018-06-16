import json
from dateutil.parser import parse as parse_date
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .view_helper import *
from buy.models import CoinbaseEvent
    
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
    # purchase, created = Purchase.objects.get_or_create(account_name=request.account_name, defaults=dict( public_key=request.public_key))
    return render(request, "buy/purchase.html", {
        'account_name': request.account_name,
        'public_key': request.public_key,
    })
    
@require_account_name
@require_public_key
def buy_action(request):
    pass
    
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
    return HttpResponse("thanks")
    