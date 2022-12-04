from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import UpdateView, CreateView, TemplateView
from polygon import BadResponse

from mondiv.forms import SearchCompanyForm, ChangeUserInfoForm
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
                    company.get_remote_image()

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
