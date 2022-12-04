from django.db import models
from django.core.files import File
from urllib import request
import os

from mondiv.utils import get_upl_and_apiKey


class Company(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    ticker = models.CharField(unique=True, max_length=8, verbose_name='Тикер')
    description = models.CharField(max_length=3000, verbose_name='О компании')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    icon_image = models.ImageField(upload_to='images/icon', verbose_name='Иконка', null=True)
    logo_image = models.ImageField(upload_to='images/logo', verbose_name='Логотип', null=True)
    icon_url = models.URLField(null=True)
    logo_url = models.URLField(null=True)

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
        if self.logo_url and not self.logo_image:
            url = get_upl_and_apiKey(self.logo_url)
            result = request.urlretrieve(url)
            u = os.path.basename(url)
            self.logo_image.save(
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

# class Item(models.Model):
#     image_file = models.ImageField(upload_to='images')
#     image_url = models.URLField()
#
#     def get_remote_image(self):
#         if self.image_url and not self.image_file:
#             result = request.urlretrieve(self.image_url)
#             print('OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO')
#             print(result[0])
#             u = os.path.basename(self.image_url)
#             print(u[u.rindex(".") + 1:u.rindex("?")]
#                   )
#             print('OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO')
#             self.image_file.save(
#                 'first.jpg',
#                 File(open(result[0], 'rb'))
#             )
#             self.save()
