from django.conf import settings
from django.utils import timezone
from django.db import models
import eosapi
import time
import json
from django.db.models.signals import pre_save
from django.dispatch import receiver
from decimal import Decimal

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
    price_cents = models.IntegerField(null=True)

    # cost of goods sold
    cogs_cents = models.IntegerField(null=True)
    profit = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=settings.ML)
    stripe = models.DateTimeField(null=True)
    coinbase = models.DateTimeField(null=True)
    
    def __str__(self):
        return self.account_name
        
    def price_usd(self):
        return self.price_cents/100.0

    @staticmethod
    def get_prices_usd():
        cogs = PriceData.ram_kb_usd() * settings.NEWACCOUNT_RAM_KB + (settings.NEWACCOUNT_NET_STAKE + settings.NEWACCOUNT_CPU_STAKE) * PriceData.price_eos_usd()
        price = cogs * 1.2 + 3
        return cogs, price

    def update_price(self):
        print("update_price called")
        self.cogs_cents, self.price_cents = [round(x*100) for x in Purchase.get_prices_usd()]
        cogs = Decimal(str(self.cogs_cents)) / 100
        price = Decimal(str(self.price_cents)) / 100
        self.profit = price - cogs


    def complete_purchase_and_save(self):
        import subprocess
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

@receiver(pre_save, sender=Purchase)
def purchase_saved(sender, instance, **kwargs):
    if not instance.cogs_cents or not instance.price_cents or not instance.profit:
        print ("Updating price from signal")
        instance.update_price()



class StripeCharge(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    price_cents = models.IntegerField()
    currency = models.CharField(max_length=settings.ML)
    response = models.TextField()
    user_uuid = models.UUIDField(null=True)
    purchase = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True)
    
    