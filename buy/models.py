from django.conf import settings
from django.db import models
import eosapi

# Create your models here.
class Purchase(models.Model):
    account_name = models.CharField(max_length=12, primary_key=True)
    public_key = models.CharField(max_length=53)
    created_at = models.DateTimeField(auto_now_add=True)
    payment_received = models.BooleanField(default=False)
    account_created = models.BooleanField(default=False)
    coinbase_charge = models.TextField()
    coinbase_code = models.CharField(max_length=settings.ML)
    
    def __str__(self):
        return self.account_name
        
    def complete_purchase_and_save(self):
        pass
        
class CoinbaseEvent(models.Model):
    uuid = models.UUIDField(primary_key=True)
    event_type = models.CharField(max_length=settings.ML)
    created_at = models.DateTimeField()
    locally_created_at = models.DateTimeField(auto_now_add=True)
    api_version = models.CharField(max_length=settings.ML)
    data = models.TextField()
    
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