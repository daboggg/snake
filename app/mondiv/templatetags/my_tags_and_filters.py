import os

from django import template

from mondiv.models import Company

register = template.Library()

@register.simple_tag()
def companies():
    return Company.objects.all()

@register.filter()
def url_and_apikey(url):
    return url+'?apiKey='+ os.environ.get('POLYGON_API_KEY')