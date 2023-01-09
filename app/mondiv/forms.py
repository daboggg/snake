from bootstrap_datepicker_plus.widgets import DatePickerInput
from django import forms
from django.contrib.auth.models import User

from mondiv.models import Dividend, Company, Report


class AddDividendForm(forms.ModelForm):
    class Meta:
        model=Dividend
        fields = ('company','date_of_receipt', 'payoff', 'currency','account')
        widgets = {
            'company': forms.Select(attrs={'class': 'form-select'}),
            'date_of_receipt': DatePickerInput(format='%dd:%mm:%YYYY', attrs={'class': 'form-control'}),
            # 'amount_of_shares': forms.NumberInput(attrs={'class': 'form-control'}),
            # 'quantity_per_share': forms.NumberInput(attrs={'class': 'form-control'}),
            'payoff': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
        }


class SearchCompanyForm(forms.Form):
    ticker = forms.CharField(max_length=10, label='Тикер')


class DividendPeriodForm(forms.Form):
    start = forms.DateField(widget=DatePickerInput(format='%dd:%mm:%YYYY', attrs={'class': 'form-control', 'placeholder': 'start'}))
    end = forms.DateField(widget=DatePickerInput(format='%dd:%mm:%YYYY', attrs={'class': 'form-control', 'placeholder': 'end'}))


class ChangeUserInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class AddReportForm(forms.ModelForm):
    class Meta:
        model=Report
        fields = ('account','currency', 'report_date', 'amount')
        widgets = {
            'report_date': DatePickerInput(format='%dd:%mm:%YYYY'),
        }