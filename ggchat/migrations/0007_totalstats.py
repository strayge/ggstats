# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-08 00:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ggchat', '0006_commonpremium_commonpremiumpayments'),
    ]

    operations = [
        migrations.CreateModel(
            name='TotalStats',
            fields=[
                ('timestamp', models.DateTimeField(primary_key=True, serialize=False)),
                ('clients', models.IntegerField()),
                ('users', models.IntegerField()),
            ],
        ),
    ]
