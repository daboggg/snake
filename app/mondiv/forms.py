from bootstrap_datepicker_plus.widgets import DatePickerInput
from django import forms
from django.contrib.auth.models import User
from mondiv.models import Dividend


class AddDividendForm(forms.ModelForm):
    class Meta:
        model=Dividend
        fields = ('company','date_of_receipt','amount_of_shares','quantity_per_share','currency','account')
        widgets = {
            'date_of_receipt': DatePickerInput(format='%dd:%mm:%YYYY')
        }


class SearchCompanyForm(forms.Form):
    ticker = forms.CharField(max_length=10, label='Тикер')


class ChangeUserInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')