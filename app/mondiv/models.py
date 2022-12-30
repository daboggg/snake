from django.contrib.auth.models import User
from django.db import models
from django.core.files import File
from urllib import request
import os

from mondiv.utils import get_upl_and_apiKey

class Currency(models.Model):
    name = models.CharField(max_length=5, verbose_name='Валюта')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Валюта'
        verbose_name_plural = 'Вылюты'

class Account(models.Model):
    name = models.CharField(max_length=100, verbose_name='Брокерский счет')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Владелец счета')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Счет'
        verbose_name_plural = 'Счета'



class Company(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    ticker = models.CharField(unique=True, max_length=8, verbose_name='Тикер')
    description = models.CharField(max_length=3000, verbose_name='О компании')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    icon_image = models.ImageField(upload_to='images/icon', verbose_name='Иконка', null=True)
    icon_url = models.URLField(null=True, blank=True)

    # def delete(self, *args, **kwargs):
    #     # До удаления записи получаем необходимую информацию
    #     storage, path = self.icon_image.storage, self.icon_image.path
    #     # Удаляем сначала модель ( объект )
    #     super().delete(*args, **kwargs)
    #     # Потом удаляем сам файл
    #     storage.delete(path)

    def get_remote_image(self):
        if self.icon_url and not self.icon_image:
            url = get_upl_and_apiKey(self.icon_url)
            result = request.urlretrieve(url)
            u = os.path.basename(url)
            self.icon_image.save(
                # выделяем из url имя сохраняемого файла
                self.ticker + '.' + u[u.rindex(".") + 1:u.rindex("?")],
                File(open(result[0], 'rb'))
            )
        self.save()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Компания'
        verbose_name_plural = 'Компании'
        ordering = ['name']


class Dividend(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='Пользователь')
    company = models.ForeignKey(Company, on_delete=models.PROTECT, verbose_name='Компания')
    date_of_receipt = models.DateField(verbose_name='Дата получения выплаты')
    amount_of_shares = models.SmallIntegerField(verbose_name='Количество акций')
    quantity_per_share = models.FloatField(verbose_name='Выплата на акцию')
    payment = models.FloatField(null=True, blank=True, verbose_name='Выплата')
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name='Валюта')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, verbose_name='Счет')

    class Meta:
        verbose_name = 'Дивиденд'
        verbose_name_plural = 'Дивиденды'
