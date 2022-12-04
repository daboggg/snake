from django.contrib import messages
from django.shortcuts import render
from polygon import BadResponse

from mondiv.forms import SearchCompanyForm
from mondiv.models import Company
from mondiv.utils import client, get_upl_and_apiKey


def add_dividend(request):
    return render(request, 'mondiv/main/add_dividend.html')

def add_company(request):
    if request.method == 'POST':
        form = SearchCompanyForm(request.POST)
        if form.is_valid():
            ticker = form.cleaned_data['ticker'].upper()
            if Company.objects.filter(ticker=ticker).exists():
                messages.add_message(request, messages.INFO, "Такая компания уже добавлена")
                return render(request, 'mondiv/main/add_company.html', {'form': SearchCompanyForm()})
            else:
                try:
                    res = client.get_ticker_details(ticker)
                    company = Company()
                    company.name = res.name
                    company.ticker = res.ticker
                    company.description = res.description
                    company.icon_url = res.branding.icon_url
                    company.logo_url = res.branding.logo_url
                    company.get_remote_image()
                    # Company.objects.create(
                    #     name=res.name,
                    #     ticker=res.ticker,
                    #     description=res.description,
                    #     icon_url=res.branding.icon_url,
                    #     logo_url=res.branding.logo_url
                    # )
                    messages.add_message(request, messages.INFO, f"Компания: {res.name}, с тикером: {ticker} успешно добавлена")
                    return render(request, 'mondiv/main/add_dividend.html', {'form': SearchCompanyForm()})
                except Exception as e:
                    messages.add_message(request, messages.ERROR, e)
                    return render(request, 'mondiv/main/add_company.html', {'form': SearchCompanyForm()})
        else:
            return render(request, 'mondiv/main/add_company.html', {'form': form})
    else:
        return render(request, 'mondiv/main/add_company.html', {'form': SearchCompanyForm()})


def index(request):
    return render(request, 'mondiv/main/index.html')
