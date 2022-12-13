from django.contrib import admin
from django.utils.safestring import mark_safe

from mondiv.models import Company, Account, Currency, Dividend

class DividendAdmin(admin.ModelAdmin):
    list_display = (
        'company','date_of_receipt',
        'amount_of_shares','quantity_per_share'
        ,'currency','account')
    list_display_links = ('company',)
    search_fields = ('company',)
    list_filter = ('date_of_receipt',)


class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'ticker', 'time_create', 'get_html_photo')
    list_display_links = ('ticker', 'name')
    search_fields = ('name', 'ticker')
    list_filter = ('time_create',)

    def get_html_photo(self, object):
        if object.icon_image:
            return mark_safe(f'<img src="{object.icon_image.url}" width=50>')

    get_html_photo.short_description = 'логотип'

admin.site.register(Company, CompanyAdmin)
admin.site.register(Account)
admin.site.register(Currency)
admin.site.register(Dividend, DividendAdmin)