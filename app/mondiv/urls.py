from django.urls import path

from mondiv.views import *

urlpatterns = [
    path('add_company/', add_company, name='add_company'),
    path('add_dividend/', add_dividend, name='add_dividend'),
    path('', index, name='index'),

]
