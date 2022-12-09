from django.contrib import admin

from mondiv.models import Company, Account, Currency, Dividend

admin.site.register(Company)
admin.site.register(Account)
admin.site.register(Currency)
admin.site.register(Dividend)