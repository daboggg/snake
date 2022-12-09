from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import F, Count, Sum, DateField
from django.db.models.functions import TruncMonth, TruncYear
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView, CreateView, TemplateView, ListView

from mondiv.forms import SearchCompanyForm, ChangeUserInfoForm, AddDividendForm
from mondiv.models import Company, Dividend
from mondiv.utils import client, get_month_list

from datetime import datetime, timedelta


class AddDividendView(LoginRequiredMixin, CreateView):
    form_class = AddDividendForm
    template_name = 'mondiv/main/add_dividend.html'
    success_url = reverse_lazy('mondiv:dividends_received')

    def form_valid(self, form):
        fields = form.save(commit=False)
        fields.user = self.request.user
        fields.save()
        return super().form_valid(form)


class DividendsReceivedView(LoginRequiredMixin, ListView):
    model = Dividend
    context_object_name = 'dividends'
    template_name = 'mondiv/main/dividends_received.html'

    def get_queryset(self):
        return Dividend.objects.filter(user=self.request.user) \
            .annotate(total=F('amount_of_shares') * F('quantity_per_share'))


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

                    messages.add_message(request, messages.INFO,
                                         f"Компания: {res.name}, с тикером: {ticker} успешно добавлена")
                    return redirect('mondiv:add_dividend')
                except Exception as e:
                    messages.add_message(request, messages.ERROR, e)
                    return render(request, 'mondiv/main/add_company.html', {'form': SearchCompanyForm()})
        else:
            return render(request, 'mondiv/main/add_company.html', {'form': form})
    else:
        return render(request, 'mondiv/main/add_company.html', {'form': SearchCompanyForm()})


def index(request):
    return render(request, 'mondiv/main/index.html')


##########  AUTH  #############################################################
class MDLoginView(LoginView):
    template_name = 'mondiv/auth/login.html'


@login_required
def profile(request):
    return render(request, 'mondiv/auth/profile.html')


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


###########  Charts ######################################

def proba(request):
    res = Dividend.objects \
        .filter(user=request.user, currency__name='RUB', date_of_receipt__gt=f'{datetime.now().year - 2}-01-01') \
        .annotate(month=TruncMonth('date_of_receipt')) \
        .annotate(year=TruncYear('date_of_receipt')) \
        .annotate(payment=F('amount_of_shares') * F('quantity_per_share')) \
        .values('month', 'year') \
        .annotate(total=Sum('payment')) \
        .order_by('month')

    res = [{'month': r['month'].strftime("%B"), 'year': r['year'].year, 'total': r['total']} for r in res]

    # формирует список по годам
    list_by_year = []
    year = datetime.now().year
    count = 0
    for y in range(year - 2, year + 1):
        list_by_year.append([])
        for r in res:
            if str(y) == str(r['year']):
                list_by_year[count].append(r)
        count = count + 1

    # готовый список
    ready_list = []
    cnt = 0
    for y in list_by_year:
        # if len(y) == 0:
        #     print('OOOOOOOOOOOOOOOO')
        ready_list.append([])
        for month in get_month_list():
            flg =True
            for m in y:
                if month == m['month']:
                    ready_list[cnt].append(m['total'])
                    flg = False
            if flg:
                ready_list[cnt].append(0)
        cnt = cnt + 1
    print(ready_list)
    return render(request, 'mondiv/main/proba.html', {'res': ready_list})


def last_year(request):
    currency = request.GET.get('currency', 'USD')
    res = Dividend.objects \
        .filter(user=request.user, currency__name=currency, date_of_receipt__gt=datetime.now() - relativedelta(years=1)) \
        .annotate(month=TruncMonth('date_of_receipt')) \
        .annotate(payment=F('amount_of_shares') * F('quantity_per_share')) \
        .values('month') \
        .annotate(total=Sum('payment')) \
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
                }
            }
        }
    })

def last_three_years(request):
    currency = request.GET.get('currency', 'USD')
    res = Dividend.objects \
        .filter(user=request.user, currency__name=currency, date_of_receipt__gt=f'{datetime.now().year - 2}-01-01') \
        .annotate(month=TruncMonth('date_of_receipt')) \
        .annotate(year=TruncYear('date_of_receipt')) \
        .annotate(payment=F('amount_of_shares') * F('quantity_per_share')) \
        .values('month', 'year') \
        .annotate(total=Sum('payment')) \
        .order_by('month')

    res = [{'month': r['month'].strftime("%B"), 'year': r['year'].year, 'total': r['total']} for r in res]

    # формирует список по годам
    list_by_year = []
    year = datetime.now().year
    count = 0
    for y in range(year - 2, year + 1):
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
                    'data': ready_list[0],
                    'label': 'Нет дивидендов' if len(list_by_year[0])==0 else 'Дивиденды за ' + str(list_by_year[0][0]["year"]) + ' год в '+str(currency) ,
                },
                {
                    'data': ready_list[1],
                    'label': 'Нет дивидендов' if len(list_by_year[1])==0 else 'Дивиденды за ' + str(list_by_year[1][0]["year"]) + ' год в '+str(currency) ,
                },
                {
                    'data': ready_list[2],
                    'label': 'Нет дивидендов' if len(list_by_year[2])==0 else 'Дивиденды за ' + str(list_by_year[2][0]["year"]) + ' год в '+str(currency) ,
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
                }
            }
        }
    })