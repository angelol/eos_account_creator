from django.contrib import admin
from buy.models import Purchase

admin.site.disable_action('delete_selected')

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'account_name', 'payment_received', 'account_created')
    ordering = ('-created_at', )
    fields = ('account_name', 'public_key', 'payment_received', 'account_created', 'coinbase_code', 'price_usd', 'currency')
    readonly_fields = fields