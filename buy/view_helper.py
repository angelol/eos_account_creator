from django.conf import settings
from functools import wraps
from django.shortcuts import redirect
from buy.models import Purchase, PriceData
import eosapi
import uuid
import re
import json
import base64

def set_uuid(request):
    if not request.session.get('uuid'):
        request.session['uuid'] = str(uuid.uuid4())

def require_account_name(func):
    @wraps(func)
    def inner(request, *args, **kwargs):
        set_uuid(request)
        request.account_name = None
        d = request.GET.get('d')
        if d:
            try:
                j = json.loads(base64.b64decode(d))
                account_name = j['n']
                if is_valid_account_name(account_name) and is_eos_account_available(account_name):
                    request.purchase, created = Purchase.objects.update_or_create(
                        account_name=j['n'],
                        defaults=dict(
                            owner_key=j['o'],
                            active_key=j['a'],
                            user_uuid=request.session['uuid'],
                            currency='usd',
                        )
                    )
                    if not created:
                        request.purchase.update_price()
                        request.purchase.save()
                    request.session['account_name']= j['n']
                    request.account_name = j['n']
                    request.session['owner_key'] = j['o']
                    request.session['active_key'] = j['a']
            except Exception:
                pass
        else:
            request.account_name = request.session.get('account_name')
        if request.account_name:
            return func(request, *args, **kwargs)
        return redirect("/choose/")
    return inner

def require_public_keys(func):
    @wraps(func)
    def inner(request, *args, **kwargs):
        set_uuid(request)
        request.owner_key = request.session.get('owner_key')
        request.active_key = request.session.get('active_key')
        if request.owner_key and request.active_key:
            return func(request, *args, **kwargs)
        return redirect("/keys/")
    return inner

def require_purchase(func):
    @wraps(func)
    def inner(request, *args, **kwargs):
        try:
            request.purchase = Purchase.objects.get(
                account_name = request.account_name,
                user_uuid = request.session['uuid'],
            )
            return func(request, *args, **kwargs)
        except Purchase.DoesNotExist:
            return redirect("/keys/")
    return inner


def is_valid_account_name(account_name):
    return re.match("^([a-z1-5]){12}$", account_name)
    
def is_valid_public_key(key):
    blacklist = (
        'EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV',
    )
    return key not in blacklist

def is_eos_account_available(account_name):
    c = eosapi.Client(nodes=settings.EOS_API_NODES)
    try:
        c.get_account(account_name)
        return False
    except eosapi.exceptions.HttpAPIError:
        return True

