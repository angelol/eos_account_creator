from time import time
from django import template
from django.conf import settings
from buy.models import Purchase

register = template.Library()

@register.simple_tag
def cachebuster():
    if settings.DEBUG:
        return "?" + str(time())
    else:
        return ""
        
@register.simple_tag
def price():
    return '%.2f' % Purchase.get_prices_usd()[1]
    