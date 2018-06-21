from django.contrib import admin
from buy.models import Purchase, PriceData, CoinbaseEvent
import json

admin.site.disable_action('delete_selected')

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'account_name', 'payment_received', 'account_created')
    ordering = ('-created_at', )
    fields = ('account_name', 'public_key', 'payment_received', 'account_created', 'coinbase_code', 'price_usd', 'currency', 'stripe', 'coinbase')
    readonly_fields = fields
    
@admin.register(PriceData)
class PriceDataAdmin(admin.ModelAdmin):
    list_display = ('updated_at', 'eos_usd', 'ram_kb_eos', 'ram_kb_usd')
    readonly_fields = list_display
    
    def ram_kb_usd(self, instance):
        return PriceData.ram_kb_usd()
        
        
@admin.register(CoinbaseEvent)
class CoinbaseEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'code', 'event_type', 'code', 'account_name', 'public_key' )
    
    
    def code(self, instance):
        data = json.loads(instance.data)
        return data['code']
        
    def public_key(self, instance):
        data = json.loads(instance.data)
        metadata = data['metadata']
        return metadata['public_key']

    def account_name(self, instance):
        data = json.loads(instance.data)
        metadata = data['metadata']
        return metadata['account_name']
        