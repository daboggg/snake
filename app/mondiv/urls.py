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
    path('company/<int:company_pk>/', ShowCompany.as_view(), name='company'),
    path('proba/', proba, name='proba'),
    path('last_year/', last_year, name='last_year'),
    path('last_n_years/', last_n_years, name='last_n_years'),
    path('total_for_each_year/', total_for_each_year, name='total_for_each_year'),
    path('total_for_each_ticker/', total_for_each_ticker, name='total_for_each_ticker'),
    path('total_for_each_account/', total_for_each_account, name='total_for_each_account'),
    path('dividend_history/', dividend_history, name='dividend_history'),
    path('all_reports/', all_reports, name='all_reports'),
    path('report_in_currency/', report_in_currency, name='report_in_currency'),
    path('add_company/', add_company, name='add_company'),
    path('add_dividend/', AddDividendView.as_view(), name='add_dividend'),
    path('add_report/', AddReportView.as_view(), name='add_report'),
    path('report_update/<int:report_pk>/', ReportdUpdateView.as_view(), name='report_update'),
    path('dividend_update/<int:div_pk>/', DividendUpdateView.as_view(), name='dividend_update'),
    path('report_delete/<int:report_pk>/', ReportDeleteView.as_view(), name='report_delete'),
    path('dividend_delete/<int:div_pk>/', DividendDeleteView.as_view(), name='dividend_delete'),
    path('dividends_received/', DividendsReceivedView.as_view(), name='dividends_received'),
    path('report_list/', ReportListView.as_view(), name='report_list'),
    path('', index, name='index'),
]
