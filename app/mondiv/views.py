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
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView, CreateView, TemplateView, ListView, DeleteView

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
            messages.add_message(request,messages.ERROR, 'Удаление невозможно, это не ваша запись')
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
        return Dividend.objects.filter(user=self.request.user) \
            .annotate(total=F('amount_of_shares') * F('quantity_per_share'))\
            .order_by('-id')[:50:-1]


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


###########  Charts json ######################################
def proba(request):
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

    return render(request, 'mondiv/main/proba.html', {'t': labels, 'd': data})


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

def last_n_years(request):
    year_now = datetime.now().year
    for_n_years = request.GET.get('for_n_years', 3)
    currency = request.GET.get('currency', 'USD')
    res = Dividend.objects \
        .filter(user=request.user, date_of_receipt__gt=f'{year_now - (for_n_years - 1)}-01-01', currency__name=currency) \
        .annotate(month=TruncMonth('date_of_receipt')) \
        .annotate(year=TruncYear('date_of_receipt')) \
        .annotate(payment=F('amount_of_shares') * F('quantity_per_share')) \
        .values('month', 'year') \
        .annotate(total=Sum('payment')) \
        .order_by('month')

    res = [{'month': r['month'].strftime("%B"), 'year': r['year'].year, 'total': r['total']} for r in res]

    # формирует список по годам
    list_by_year = []
    count = 0
    for y in range(year_now - (for_n_years-1), year_now + 1):
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
                    'label': 'Нет дивидендов' if len(list_by_year[n])==0 else 'Дивиденды за ' + str(list_by_year[n][0]["year"]) + ' год в '+str(currency) ,
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

def total_for_each_ticker(request):
    currency = request.GET.get('currency', 'USD')
    res = Dividend.objects \
        .filter(user=request.user, currency__name=currency) \
        .annotate(payment=F('amount_of_shares') * F('quantity_per_share')) \
        .values('company__name') \
        .annotate(total=Sum('payment'))

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
                    'labels': {
                        'font': {
                            'size': 18
                        }
                    },
                },
                'title': {
                    'font':{
                        'size': 30
                    },
                    'display': 'true',
                    'text': f'Дивиденды в {currency}'
                },
                'tooltip': {
                    'titleFont':{
                        'size': 20
                    },
                    'titleAlign': 'center',
                    'boxPadding': 10
                }
            }
        }
    })
