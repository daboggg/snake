from django.contrib.auth.models import AbstractUser
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
    icon_url = models.URLField(null=True)

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

# class AppUser(AbstractUser):
#     is_activated = models.BooleanField(default=True, db_index=True, verbose_name='Прошел активацию?')
#     send_messages = models.BooleanField(default=True,verbose_name='Слать оповещения о новых комментариях?')
#
#     class Meta(AbstractUser.Meta):
#         pass

