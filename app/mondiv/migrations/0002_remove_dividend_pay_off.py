# Generated by Django 3.2.6 on 2022-12-30 21:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mondiv', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dividend',
            name='pay_off',
        ),
    ]
