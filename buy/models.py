from django.conf import settings
from django.utils import timezone
from django.db import models
from django_countries.fields import CountryField
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
    ip = models.GenericIPAddressField(null=True, blank=True)
    country_from_ip = CountryField(null=True)
    country_given = CountryField(null=True)
    
    # final prices on invoice
    payment_method = models.CharField(max_length=settings.ML, choices=(('credit',)*2, ('crypto',)*2), null=True)
    price_net = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    vat_percentage = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    vat = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    price_gross = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    
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

    @staticmethod
    def cogs():
        return PriceData.ram_kb_usd() * settings.NEWACCOUNT_RAM_KB + (settings.NEWACCOUNT_NET_STAKE + settings.NEWACCOUNT_CPU_STAKE) * PriceData.price_eos_usd()
        
    @staticmethod
    def get_prices_usd_crypto():
        return (Purchase.cogs() + 3) * 1.2

    @staticmethod
    def get_prices_usd_credit():
        return (Purchase.cogs() + 4) * 1.2
        
    @staticmethod
    def get_prices_eos_eos():
        return 0.1

    def price_gross_cents(self):
        if self.price_gross:
            return round(self.price_gross*100)
        else:
            return None
        
    def price_cents_credit(self):
        return round(Purchase.get_prices_usd_credit()*100)
        
    def price_cents_crypto(self):
        return round(Purchase.get_prices_usd_crypto()*100)
        
    def cogs_cents(self):
        return round(Purchase.cogs()*100)
    
    def update_price(self):    
        assert self.payment_method, "No payment method set"
        # assert self.country_from_ip , "No country from IP"        
        # assert self.country_given , "No country given"
        if self.country_from_ip:
            assert self.country_from_ip == self.country_given, "Countries don't match"
        
        if self.payment_method == 'credit':
            self.price_net = Purchase.get_prices_usd_credit()
        elif self.payment_method == 'crypto':
            self.price_net = Purchase.get_prices_usd_crypto()
        else:
            self.price_net = 0
        
        self.vat_percentage = VATRates.get(self.country_given.code) / 100
        self.vat = self.price_net * self.vat_percentage
        print("self.payment_method: ", self.payment_method)
        print("update_price self.vat: ", self.vat)
        self.price_gross = self.price_net + self.vat
        self.profit = self.price_net - Purchase.cogs()
            
    def update_registration_status(self):
        if self.did_registration_work():
            self.account_created = True
            self.save()

    def complete_purchase_and_save(self):
        import subprocess
        self.update_registration_status()
        if not self.account_created:
            subprocess.run(["/usr/bin/env", "node", "buy/gen_account.js", self.account_name, self.owner_key, self.active_key], check=True)
            time.sleep(1)
            self.update_registration_status()

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
    pass
    # if not instance.cogs_cents or not instance.price_cents_credit or not instance.price_cents_crypto:
    #     print ("Updating price from signal")
    #     instance.update_price()



class StripeCharge(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    price_cents = models.IntegerField()
    currency = models.CharField(max_length=settings.ML)
    response = models.TextField()
    user_uuid = models.UUIDField(null=True)
    purchase = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True)
    
class VATRates(models.Model):
    updated_at = models.DateTimeField(auto_now=True)
    data = models.TextField()
    
    @staticmethod
    def update():
        import requests
        url = 'https://vatapi.com/v1/vat-rates'
        headers = {'Apikey' : settings.VATAPI_APIKEY}
        response = requests.get(url, headers=headers)
        response_data = response.json()['countries']
        data = {}
        for d in response_data:
            country = list(d.keys())[0]
            value = list(d.values())[0]
            data[country] = value
        
        VATRates.objects.update_or_create(id=1, defaults=dict(
            data=json.dumps(data),
        ))
    
    @staticmethod
    def get(country):
        data = json.loads(VATRates.objects.all()[0].data)
        try:
            return data[country]['rates']['standard']['value']
        except KeyError:
            return 0
    
    @staticmethod
    def all():
        data = json.loads(VATRates.objects.all()[0].data)
        return {x: data[x]['rates']['standard']['value'] for x in data}
        
    
    
    
    