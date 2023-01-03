import os

from bootstrap_datepicker_plus.widgets import DatePickerInput
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import F, Count, Sum, DateField, Min, Subquery
from django.db.models.functions import TruncMonth, TruncYear
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils.http import urlencode
from django.views.generic import UpdateView, CreateView, TemplateView, ListView, DeleteView

import requests
from polygon import RESTClient

from mondiv.forms import SearchCompanyForm, ChangeUserInfoForm, AddDividendForm, DividendPeriodForm
from mondiv.models import Company, Dividend
from mondiv.utils import client, get_month_list

from datetime import datetime, timedelta, date


class AddDividendView(LoginRequiredMixin, CreateView):
    form_class = AddDividendForm
    template_name = 'mondiv/main/add_dividend.html'
    success_url = reverse_lazy('mondiv:dividends_received')

    def form_valid(self, form):
        fields = form.save(commit=False)
        fields.user = self.request.user
        fields.save()
        return super().form_valid(form)


class DividendUpdateView(LoginRequiredMixin, UpdateView):
    model = Dividend
    form_class = AddDividendForm
    template_name = 'mondiv/main/dividend_update.html'
    pk_url_kwarg = 'div_pk'
    success_url = reverse_lazy('mondiv:dividends_received')

    def get_queryset(self):
        return Dividend.objects.filter(pk=self.kwargs[self.pk_url_kwarg], user=self.request.user)

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, 'Данные исправлены')
        return super().form_valid(form)


class DividendDeleteView(LoginRequiredMixin, DeleteView):
    model = Dividend
    pk_url_kwarg = 'div_pk'
    success_url = reverse_lazy('mondiv:dividends_received')
    template_name = 'mondiv/main/dividend_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.user == request.user:
            self.object.delete()
            messages.add_message(request, messages.SUCCESS, 'Запись удалена')
            return HttpResponseRedirect(self.success_url)
        else:
            messages.add_message(request, messages.ERROR, 'Удаление невозможно, это не ваша запись')
            return HttpResponseRedirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = self.object.company
        return context


class DividendsReceivedView(LoginRequiredMixin, ListView):
    model = Dividend
    context_object_name = 'dividends'
    template_name = 'mondiv/main/dividends_received.html'

    def get_queryset(self):
        # Фильтрация по диапазону дат
        if self.request.GET and self.request.GET['start'] and self.request.GET['end']:
            start = self.request.GET['start']
            end = self.request.GET['end']
            return Dividend.objects.filter(user=self.request.user, date_of_receipt__range=[start,end])

        # Возвращает по умолчанию 50 последних записей
        limit = self.request.GET.get('limit', 50)
        return Dividend.objects.filter(user=self.request.user) \
                   .order_by('-id')[:int(limit):-1]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET and self.request.GET['start'] and self.request.GET['end']:
            context['start'] = datetime.strptime(self.request.GET['start'], '%Y-%m-%d').date()
            context['end'] = datetime.strptime(self.request.GET['end'], '%Y-%m-%d').date()
        context['form'] = DividendPeriodForm()
        return context


@login_required
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
                    company.get_remote_image()
                    saved_company = Company.objects.get(name=res.name)
                    messages.add_message(request, messages.INFO,
                                         f"Компания: {res.name}, с тикером: {ticker} успешно добавлена")

                    # редирект на урл с гет параметрами сохраненной компании
                    return redirect('{}?{}'.format(reverse('mondiv:add_dividend'), urlencode(
                        {'company_name': f'{saved_company.name} ({saved_company.ticker})', 'id': saved_company.id})))

                except Exception as e:
                    messages.add_message(request, messages.ERROR, e)
                    return render(request, 'mondiv/main/add_company.html', {'form': SearchCompanyForm()})
        else:
            return render(request, 'mondiv/main/add_company.html', {'form': form})
    else:
        return render(request, 'mondiv/main/add_company.html', {'form': SearchCompanyForm()})


def index(request):
    return render(request, 'mondiv/main/index.html')


# подробно про компанию (дивиденты и инфо)
def company(request, company_pk):
    try:
        company = Company.objects.get(pk=company_pk)
    except Exception as e:
        messages.add_message(request, messages.ERROR, e)
    return render(request, 'mondiv/main/company.html', {'company': company})


##########  AUTH  #############################################################
class MDLoginView(LoginView):
    template_name = 'mondiv/auth/login.html'


@login_required
def profile(request):
    res = Dividend.objects \
        .filter(user=request.user)

    total = res.values('currency__name') \
        .annotate(total=Sum('payoff'))
    ctx = {}
    if total.count() == 0:
        ctx['RUB'] = 0
        ctx['USD'] = 0
    else:
        for item in total:
            ctx[item['currency__name']] = item['total']

    # минимальная и максимальная выплата в рублях по тикеру
    payout_ticker_rub = res.filter(currency__name='RUB') \
        .values('company__name', 'payoff') \
        .order_by('payoff')
    minimum_payout_ticker_rub = payout_ticker_rub.first()
    maximum_payout_ticker_rub = payout_ticker_rub.last()

    # минимальная и максимальная выплата в долларах по тикеру
    payout_ticker_usd = res.filter(currency__name='USD') \
        .values('company__name', 'payoff') \
        .order_by('payoff')
    minimum_payout_ticker_usd = payout_ticker_usd.first()
    maximum_payout_ticker_usd = payout_ticker_usd.last()

    # количество выплат
    number_payments = res.values('currency__name') \
                        .annotate(number_payments=Count('id'))

    # контекст
    ctx['minimum_payout_ticker_rub'] = minimum_payout_ticker_rub
    ctx['maximum_payout_ticker_rub'] = maximum_payout_ticker_rub
    ctx['minimum_payout_ticker_usd'] = minimum_payout_ticker_usd
    ctx['maximum_payout_ticker_usd'] = maximum_payout_ticker_usd
    for n in number_payments:
        ctx[n['currency__name'] + '_p'] = n

    return render(request, 'mondiv/auth/profile.html', ctx)


class MDLogoutView(LoginRequiredMixin, LogoutView):
    template_name = 'mondiv/auth/logout.html'


class ChangeUserInfoView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'mondiv/auth/change_user_info.html'
    form_class = ChangeUserInfoForm
    success_url = reverse_lazy('mondiv:profile')
    success_message = 'Данные пользователя изменены'

    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)


class MDPasswordChangeView(SuccessMessageMixin, LoginRequiredMixin, PasswordChangeView):
    template_name = 'mondiv/auth/password_change.html'
    success_url = reverse_lazy('mondiv:profile')
    success_message = 'Пароль пользователя изменен'


class RegisterUserView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('mondiv:register_done')
    template_name = 'mondiv/auth/register_user.html'


class RegisterDoneView(TemplateView):
    template_name = 'mondiv/auth/register_done.html'


###########  Charts json ######################################
def proba(request):
    currency = request.GET.get('currency', 'RUB')
    res = Dividend.objects \
        .filter(user=request.user, currency__name=currency) \
        .annotate(year=TruncYear('date_of_receipt')) \
        .values('year') \
        .annotate(total=Sum('payoff')) \
        .order_by('year')

    return render(request, 'mondiv/main/proba.html', {'res': res})


@login_required()
def last_year(request):
    currency = request.GET.get('currency', 'USD')
    res = Dividend.objects \
        .filter(user=request.user, currency__name=currency, date_of_receipt__gt=datetime.now() - relativedelta(years=1)) \
        .annotate(month=TruncMonth('date_of_receipt')) \
        .values('month') \
        .annotate(total=Sum('payoff')) \
        .order_by('month')

    labels = [r['month'].strftime("%B") for r in res]
    data = [r['total'] for r in res]
    return JsonResponse({
        'type': 'bar',
        'data': {
            'labels': labels,
            'datasets': [
                {
                    'data': data,
                    'label': 'Дивиденды за последний год в ' + currency,
                },
            ]
        },
        'options': {
            'plugins': {
                'legend': {
                    'labels': {
                        'font': {
                            'size': 18
                        }
                    },
                },
                'tooltip': {
                    'titleFont': {
                        'size': 20
                    },
                    'titleAlign': 'center',
                    'boxPadding': 10
                },
                'title': {
                    'font': {
                        'size': 30
                    },
                    'display': 'true',
                    'text': f'Дивиденды за последний год в {currency}'
                },
            }
        }
    })


@login_required()
def last_n_years(request):
    year_now = datetime.now().year
    for_n_years = request.GET.get('for_n_years', 3)
    currency = request.GET.get('currency', 'USD')
    res = Dividend.objects \
        .filter(user=request.user, date_of_receipt__gt=f'{year_now - (for_n_years - 1)}-01-01', currency__name=currency) \
        .annotate(month=TruncMonth('date_of_receipt')) \
        .annotate(year=TruncYear('date_of_receipt')) \
        .values('month', 'year') \
        .annotate(total=Sum('payoff')) \
        .order_by('month')

    res = [{'month': r['month'].strftime("%B"), 'year': r['year'].year, 'total': r['total']} for r in res]

    # формирует список по годам
    list_by_year = []
    count = 0
    for y in range(year_now - (for_n_years - 1), year_now + 1):
        list_by_year.append([])
        for r in res:
            if str(y) == str(r['year']):
                list_by_year[count].append(r)
        count = count + 1

    # готовый список
    ready_list = []
    cnt = 0
    for y in list_by_year:
        ready_list.append([])
        for month in get_month_list():
            flg = True
            for m in y:
                if month == m['month']:
                    ready_list[cnt].append(m['total'])
                    flg = False
                    break
            if flg:
                ready_list[cnt].append(0)
        cnt = cnt + 1

    return JsonResponse({
        'type': 'bar',
        'data': {
            'labels': get_month_list(),
            'datasets': [
                {
                    'data': ready_list[n],
                    'label': 'Нет дивидендов' if len(list_by_year[n]) == 0 else 'Дивиденды за ' + str(
                        list_by_year[n][0]["year"]) + ' год в ' + str(currency),
                }
                for n in range(for_n_years)
            ]
        },
        'options': {
            'plugins': {
                'legend': {
                    'labels': {
                        'font': {
                            'size': 18
                        }
                    },
                },
                'tooltip': {
                    'titleFont': {
                        'size': 20
                    },
                    'titleAlign': 'center',
                    'boxPadding': 10
                },
                'title': {
                    'font': {
                        'size': 30
                    },
                    'display': 'true',
                    'text': f'Дивиденды за три последних года в {currency}'
                },
            }
        }
    })


@login_required()
def total_for_each_ticker(request):
    currency = request.GET.get('currency', 'USD')
    res = Dividend.objects \
        .filter(user=request.user, currency__name=currency) \
        .values('company__name') \
        .annotate(total=Sum('payoff'))

    return JsonResponse({
        'type': 'doughnut',
        'data': {
            'labels': [r['company__name'] for r in res],
            'datasets': [
                {
                    'data': [r['total'] for r in res],
                    'label': f'Всего в  {currency}',
                    'hoverOffset': 8
                },
            ]
        },
        'options': {
            'plugins': {
                'legend': {
                    'display': 0,
                    'labels': {
                        'font': {
                            'size': 18
                        }
                    },
                },
                'title': {
                    'font': {
                        'size': 30
                    },
                    'display': 'true',
                    'text': f'Дивиденды по компаниям в {currency}'
                },
                'tooltip': {
                    'titleFont': {
                        'size': 20
                    },
                    'titleAlign': 'center',
                    'boxPadding': 10
                }
            }
        }
    })


@login_required()
def total_for_each_account(request):
    currency = request.GET.get('currency', 'USD')
    res = Dividend.objects \
        .filter(user=request.user, currency__name=currency, ) \
        .values('account__name') \
        .annotate(total=Sum('payoff'))

    return JsonResponse({
        'type': 'polarArea',
        'data': {
            'labels': [r['account__name'] for r in res],
            'datasets': [
                {
                    'data': [r['total'] for r in res],
                    'label': f'Всего в  {currency}',
                    'hoverOffset': 8
                },
            ]
        },
        'options': {
            'plugins': {
                'legend': {
                    'labels': {
                        'font': {
                            'size': 18
                        }
                    },
                },
                'title': {
                    'font': {
                        'size': 30
                    },
                    'display': 'true',
                    'text': f'Дивиденды на счетах в {currency}'
                },
                'tooltip': {
                    'titleFont': {
                        'size': 20
                    },
                    'titleAlign': 'center',
                    'boxPadding': 10
                }
            }
        }
    })


@login_required()
def dividend_history(request):
    ticker = request.GET.get('ticker')
    limit = request.GET.get('limit', 40)
    apiKey = os.environ.get("POLYGON_API_KEY") or 'slfhowwfy'

    url = f'https://api.polygon.io/v3/reference/dividends?ticker={ticker}&limit={limit}&apiKey={apiKey}'

    res = requests.get(url)
    if len(res.json()['results']) != 0:
        res = res.json()['results']
        res = [[r['cash_amount'] for r in reversed(res)], [r['ex_dividend_date'] for r in reversed(res)]]
    else:
        url = f'http://iss.moex.com/iss/securities/{ticker}/dividends.json'
        res = requests.get(url)
        res = res.json()['dividends']['data']
        res = [[r[3] for r in res], [r[2] for r in res]]
    return JsonResponse({
        'type': 'bar',
        'data': {
            'labels': res[1],
            'datasets': [
                {
                    'data': res[0],
                    'label': 'выплата',
                },
            ]
        },
        'options': {
            'plugins': {
                'legend': {
                    'display': 0,
                    'labels': {
                        'font': {
                            'size': 18
                        }
                    },
                },
                'tooltip': {
                    'titleFont': {
                        'size': 20
                    },
                    'titleAlign': 'center',
                    'boxPadding': 10
                },
                'title': {
                    'font': {
                        'size': 30
                    },
                    'display': 'true',
                    'text': f'Дивиденды, последние {limit} выплат'
                },
            }
        }
    })

@login_required()
def total_for_each_year(request):
    currency = request.GET.get('currency', 'USD')
    res = Dividend.objects \
        .filter(user=request.user, currency__name=currency) \
        .annotate(year=TruncYear('date_of_receipt')) \
        .values('year') \
        .annotate(total=Sum('payoff')) \
        .order_by('year')

    labels = [r['year'].year for r in res]
    data = [r['total'] for r in res]

    return JsonResponse({
        'type': 'bar',
        'data': {
            'labels': labels,
            'datasets': [
                {
                    'data': data,
                    'label': 'Дивиденды в ' + currency,
                    'backgroundColor': [
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(255, 159, 64, 0.2)',
                        'rgba(255, 205, 86, 0.2)',
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(54, 162, 235, 0.2)',
                        'rgba(153, 102, 255, 0.2)',
                        'rgba(201, 203, 207, 0.2)'
                    ],
                    'borderColor': [
                        'rgb(255, 99, 132)',
                        'rgb(255, 159, 64)',
                        'rgb(255, 205, 86)',
                        'rgb(75, 192, 192)',
                        'rgb(54, 162, 235)',
                        'rgb(153, 102, 255)',
                        'rgb(201, 203, 207)'
                    ],
                    'borderWidth': 1
                }
            ]
        },
        'options': {
            'plugins': {
                'legend': {
                    'display': 0,
                    'labels': {
                        'font': {
                            'size': 18
                        }
                    },
                },
                'tooltip': {
                    'titleFont': {
                        'size': 20
                    },
                    'titleAlign': 'center',
                    'boxPadding': 10
                },
                'title': {
                    'font': {
                        'size': 30
                    },
                    'display': 'true',
                    'text': f'Дивиденды в {currency}'
                },
            }
        }
    })
