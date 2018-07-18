from time import time
from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def cachebuster():
    if settings.DEBUG:
        return "?" + str(time())
    else:
        return ""