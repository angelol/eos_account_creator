from django.conf import settings
from functools import wraps
from django.shortcuts import redirect
from buy.models import Purchase, PriceData
import eosapi
import uuid
import re

def set_uuid(request):
    if not request.session.get('uuid'):
        request.session['uuid'] = str(uuid.uuid4())

def require_account_name(func):
    @wraps(func)
    def inner(request, *args, **kwargs):
        set_uuid(request)
        request.account_name = request.session.get('account_name')
        if request.account_name:
            return func(request, *args, **kwargs)
        return redirect("/choose/")        
    return inner

def require_public_key(func):
    @wraps(func)
    def inner(request, *args, **kwargs):
        set_uuid(request)
        request.public_key = request.session.get('public_key')
        if request.public_key:
            return func(request, *args, **kwargs)
        return redirect("/keys/")        
    return inner
    
def is_valid_account_name(account_name):
    return re.match("^([a-z1-5]){12}$", account_name)
    
def is_eos_account_available(account_name):
    c = eosapi.Client(nodes=settings.EOS_API_NODES)
    try:
        c.get_account(account_name)
        return False
    except eosapi.exceptions.HttpAPIError:
        return True
        
def get_account_price_usd():
    return (PriceData.ram_kb_usd() * settings.NEWACCOUNT_RAM_KB + (settings.NEWACCOUNT_NET_STAKE + settings.NEWACCOUNT_CPU_STAKE) * PriceData.price_eos_usd())*3
    
    
    