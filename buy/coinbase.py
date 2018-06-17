from django.conf import settings
import requests
from urllib.parse import urljoin

def create_charge(account_name, public_key, price_usd):
    url = 'https://api.commerce.coinbase.com/charges'
    headers = {
        'X-CC-Api-Key' : settings.COINBASE_API_KEY,
        'X-CC-Version': settings.COINBASE_API_VERSION,
    }    
    payload = {
        "name": "EOS Account",
        "description": "EOS Account creation service",
        "local_price": {
            "amount": "%.2f" % price_usd,
            "currency": "USD"
        },
        "pricing_type": "fixed_price",
        "metadata": {
            "account_name": account_name,
            "public_key": public_key,
        },
        "redirect_url": urljoin(settings.CANONICAL_BASE_URL, '/success/')
    }
    
    r = requests.post(url, headers=headers, json=payload)
    
    
    return r.json()
    
def create_sha256_signature(key, message):
    byte_key = key.encode()
    return hmac.new(byte_key, message, hashlib.sha256).hexdigest()

def check_coinbase_signature(request):
    signature = request.META['HTTP_X_CC_WEBHOOK_SIGNATURE']
    assert signature == create_sha256_signature(settings.COINBASE_SECRET, request.body), "Signature mismatch"