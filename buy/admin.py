from django.contrib import admin
from buy.models import Purchase, PriceData, CoinbaseEvent
import json
from decimal import Decimal
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import calendar

admin.site.disable_action('delete_selected')

class DateListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'Date'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'date'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        from datetime import date
        return (
            ('today', 'Today'),
            ('yesterday', 'Yesterday'),
            ('day_before_yesterday', 'Day before yesterday'),
            ('past_7_days', 'This week'),
            ('this_month', "This Month"),
            ('last_month', "Last Month"),
            ('month_before_last_month', "Month before last Month"),
            
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if timezone.is_aware(now):
            now = timezone.localtime(now)

        today = now.date()

        def last_month_range(today):
            first_of_current_month = today.replace(day=1)
            first_of_last_month = first_of_current_month - relativedelta(months=1)
            last_of_last_month = first_of_last_month.replace(day=calendar.monthrange(first_of_last_month.year, first_of_last_month.month)[1])
            return (first_of_last_month, last_of_last_month)

        def month_before_last_month(today):
            first_of_last_month, last_of_last_month = last_month_range(today)
            return (first_of_last_month - relativedelta(months=1), first_of_last_month - relativedelta(days=1))

        return {
            None: queryset,
            'today': queryset.filter(created_at__date=today),
            'yesterday': queryset.filter(created_at__date=today-relativedelta(days=1)),
            'day_before_yesterday': queryset.filter(created_at__date=today-relativedelta(days=2)),
            'past_7_days': queryset.filter(created_at__date__range=(today-relativedelta(days=7), today)),
            'this_month': queryset.filter(created_at__date__range=(today.replace(day=1), today)),
            'last_month': queryset.filter(created_at__date__range=last_month_range(today)),
            'month_before_last_month': queryset.filter(created_at__date__range=month_before_last_month(today)),
        }[self.value()]
        
def process(modeladmin, request, queryset):
    for x in queryset:
        x.complete_purchase_and_save()

process.short_description = 'Process'

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'account_name', 'payment_received', 'account_created', 'price_crypto', 'profit')
    ordering = ('-created_at', )
    fields = ('account_name', 'owner_key', 'active_key', 'payment_received', 'account_created', 'coinbase_code', 'price_usd_crypto', 'currency', 'stripe', 'coinbase')
    readonly_fields = fields
    actions = [process]
    search_fields = ('account_name', 'owner_key', 'active_key')
    list_filter = ('payment_received', 'account_created', DateListFilter)
    
    def price_crypto(self, instance):
        if instance.price_cents_crypto:
            return Decimal(str(instance.price_cents_crypto))/100
        else:
            return ""

@admin.register(PriceData)
class PriceDataAdmin(admin.ModelAdmin):
    list_display = ('updated_at', 'eos_usd', 'ram_kb_eos', 'ram_kb_usd')
    readonly_fields = list_display

    def ram_kb_usd(self, instance):
        return PriceData.ram_kb_usd()


@admin.register(CoinbaseEvent)
class CoinbaseEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'code', 'event_type', 'account_name', 'owner_key', 'active_key' )
    ordering = ('-created_at', )
    search_fields = ('code', 'account_name', 'owner_key', 'active_key')
    list_filter = ('created_at', )

    def code(self, instance):
        data = json.loads(instance.data)
        return data['code']

    def owner_key(self, instance):
        try:
            data = json.loads(instance.data)
            metadata = data['metadata']
            return metadata['owner_key']
        except Exception:
            return ''

    def active_key(self, instance):
        try:
            data = json.loads(instance.data)
            metadata = data['metadata']
            return metadata['active_key']
        except Exception:
            return ''

    def account_name(self, instance):
        try:
            data = json.loads(instance.data)
            metadata = data['metadata']
            return metadata['account_name']
        except Exception:
            return ""
