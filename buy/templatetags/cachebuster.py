from time import time
from django import template

register = template.Library()

@register.simple_tag
def cachebuster():
    return str(time())