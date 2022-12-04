from django import forms


class SearchCompanyForm(forms.Form):
    ticker = forms.CharField(max_length=10, label='Тикер')