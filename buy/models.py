from django.conf import settings
from django.utils import timezone
from django.db import models
import eosapi
import time
import json
import secrets
import base58
import hashlib
from django.db.models.signals import pre_save
from django.dispatch import receiver
from decimal import Decimal

def get_nonce():
    return base58.b58encode(secrets.token_bytes(8)).decode('utf-8')

# Create your models here.
class Purchase(models.Model):
    account_name = models.CharField(max_length=12, primary_key=True)    
    owner_key = models.CharField(max_length=53)
    active_key = models.CharField(max_length=53)
    created_at = models.DateTimeField(auto_now_add=True)
    payment_received = models.BooleanField(default=False)
    payment_received_at = models.DateTimeField(null=True)
    account_created = models.BooleanField(default=False)
    coinbase_charge = models.TextField()
    coinbase_code = models.CharField(max_length=settings.ML)
    user_uuid = models.UUIDField(null=True)
    
    price_cents_crypto = models.IntegerField(null=True)
    price_cents_credit = models.IntegerField(null=True)
    price_eos_eos = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    
    # for eos payment method
    nonce = models.CharField(max_length=53, default=get_nonce)
    
    # cost of goods sold
    cogs_cents = models.IntegerField(null=True)
    profit = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    currency = models.CharField(max_length=settings.ML)
    stripe = models.DateTimeField(null=True)
    coinbase = models.DateTimeField(null=True)
    
    def __str__(self):
        return self.account_name
        
    def price_usd_crypto(self):
        if not self.price_cents_crypto:
            self.update_price()
        return self.price_cents_crypto/100.0

    def price_usd_credit(self):
        if not self.price_cents_credit:
            self.update_price()
        return self.price_cents_credit/100.0

    @staticmethod
    def cogs():
        return PriceData.ram_kb_usd() * settings.NEWACCOUNT_RAM_KB + (settings.NEWACCOUNT_NET_STAKE + settings.NEWACCOUNT_CPU_STAKE) * PriceData.price_eos_usd()
        
    @staticmethod
    def get_prices_usd_crypto():
        return (Purchase.cogs() + 3) * 1.2

    @staticmethod
    def get_prices_usd_credit():
        return (Purchase.cogs() + 4) * 1.4
        
    @staticmethod
    def get_prices_eos_eos():
        return 0.1

    def update_price(self):
        self.cogs_cents = round(Purchase.cogs()*100)
        self.price_cents_crypto = round(Purchase.get_prices_usd_crypto()*100)
        self.price_cents_credit = round(Purchase.get_prices_usd_credit()*100)
        self.price_eos_eos = Purchase.get_prices_eos_eos()
        

    def complete_purchase_and_save(self):
        import subprocess
        if self.did_registration_work():
            self.account_created = True
            self.save()
        else:
            subprocess.run(["/usr/bin/env", "node", "buy/gen_account.js", self.account_name, self.owner_key, self.active_key], check=True)
            time.sleep(1)
            if self.did_registration_work():
                self.account_created = True
                self.save()

    def did_registration_work(self):
        c = eosapi.Client(nodes=settings.EOS_API_NODES)
        try:
            x = c.get_account(self.account_name)
            for p in x['permissions']:
                if p['perm_name'] == 'active':
                    if p['required_auth']['keys'][0]['key'] != self.active_key:
                        return False
                if p['perm_name'] == 'owner':
                    if p['required_auth']['keys'][0]['key'] != self.owner_key:
                        return False
            return True
        except eosapi.exceptions.HttpAPIError:
            return False
                    
    def memo(self):
        return '%s%s' % (self.account_name, self.nonce)
        
    def hash(self):
        return hashlib.sha256(self.memo().encode('utf-8')).hexdigest()
    
    def regaccount(self):
        import subprocess
        subprocess.run(["/usr/bin/env", "node", "buy/regaccount.js", self.hash(), self.owner_key, self.active_key], check=True)
        
    def as_json(self):
        return {
            'account_name': self.account_name,
            'owner_key': self.owner_key,
            'active_key': self.active_key,
            'coinbase_code': self.coinbase_code,
            'payment_received': self.payment_received,
            'account_created': self.account_created,
        }
        
class CoinbaseEvent(models.Model):
    uuid = models.UUIDField(primary_key=True)
    event_type = models.CharField(max_length=settings.ML)
    created_at = models.DateTimeField()
    locally_created_at = models.DateTimeField(auto_now_add=True)
    api_version = models.CharField(max_length=settings.ML)
    data = models.TextField()
    
    def process(self):
        if self.event_type == 'charge:confirmed':
            data = json.loads(self.data)
            metadata = data['metadata']
            account_name = metadata['account_name']
            code = data['code']
            p = Purchase.objects.get(
                account_name=account_name,
                coinbase_code=code,
            )
            if not p.payment_received:
                p.payment_received = True
                p.payment_received_at = timezone.now()
                p.save()
            if not p.account_created:
                p.complete_purchase_and_save()
    
class PriceData(models.Model):
    updated_at = models.DateTimeField(auto_now=True)
    eos_usd = models.FloatField()
    ram_kb_eos = models.FloatField()
    
    @staticmethod
    def _get_ram_price_kb_eos():
        c = eosapi.Client(nodes=settings.EOS_API_NODES)
        x = c.get_table_rows(True, 'eosio', 'eosio', 'rammarket', 'id', 0, -1, 1)['rows'][0]
        base_balance = x['base']['balance'].rsplit(' ')[0]
        quote_balance = x['quote']['balance'].rsplit(' ')[0]
        return 1024 * float(quote_balance)/float(base_balance)
        
    @staticmethod
    def _get_eos_price():
        import requests
        url = 'https://rest.coinapi.io/v1/exchangerate/EOS/USD'
        headers = {'X-CoinAPI-Key' : settings.COINAPI_KEY}
        response = requests.get(url, headers=headers)
        return response.json()['rate']

    
    @staticmethod
    def update():
        PriceData.objects.update_or_create(id=1, defaults=dict(eos_usd=PriceData._get_eos_price(), ram_kb_eos=PriceData._get_ram_price_kb_eos()))
        
    @staticmethod
    def ram_kb_usd():
        p = PriceData.objects.get(id=1)
        return p.ram_kb_eos * p.eos_usd
        
    @staticmethod
    def price_eos_usd():
        p = PriceData.objects.get(id=1)
        return p.eos_usd
        
    @staticmethod
    def minimum_amount_sac():
        p = PriceData.objects.get(id=1)
        return p.ram_kb_eos * (settings.NEWACCOUNT_RAM_KB + 0.256) * 1.05 + settings.NEWACCOUNT_NET_STAKE + settings.NEWACCOUNT_CPU_STAKE + settings.SMART_ACCOUNT_CREATOR_FEE + 0.1
        

@receiver(pre_save, sender=Purchase)
def purchase_saved(sender, instance, **kwargs):
    if not instance.cogs_cents or not instance.price_cents_credit or not instance.price_cents_crypto:
        print ("Updating price from signal")
        instance.update_price()



class StripeCharge(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    price_cents = models.IntegerField()
    currency = models.CharField(max_length=settings.ML)
    response = models.TextField()
    user_uuid = models.UUIDField(null=True)
    purchase = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True)
    
    