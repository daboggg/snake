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
    path('proba/', proba, name='proba'),
    path('last_year/', last_year, name='last_year'),
    path('last_three_years/', last_three_years, name='last_three_years'),
    path('add_company/', add_company, name='add_company'),
    path('add_dividend/', AddDividendView.as_view(), name='add_dividend'),
    path('dividends_received/', DividendsReceivedView.as_view(), name='dividends_received'),
    path('', index, name='index'),
]