from django import forms
from django.contrib.auth.models import User


class SearchCompanyForm(forms.Form):
    ticker = forms.CharField(max_length=10, label='Тикер')


class ChangeUserInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')