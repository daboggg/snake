from django.urls import path

from mondiv.views import index

urlpatterns = [
    path('', index, name='index'),
]