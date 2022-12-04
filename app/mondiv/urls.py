from django.urls import path

from mondiv.views import *

app_name = 'mondiv'

urlpatterns = [
    path('accounts/register/done/', RegisterDoneView.as_view(), name='register_done'),
    path('accounts/register/', RegisterUserView.as_view(), name='register'),
    path('accounts/logout/', MDLogoutView.as_view(), name='logout'),
    path('accounts/password/change/', MDPasswordChangeView.as_view(), name='password_change'),
    path('accounts/profile/change/', ChangeUserInfoView.as_view(), name='profile_change'),
    path('accounts/profile/', profile, name='profile'),
    path('accounts/login/', MDLoginView.as_view(), name='login'),
    path('add_company/', add_company, name='add_company'),
    path('add_dividend/', add_dividend, name='add_dividend'),
    path('', index, name='index'),
]