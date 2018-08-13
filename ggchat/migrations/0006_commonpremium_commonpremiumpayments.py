# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-29 21:13
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ggchat', '0005_auto_20170629_2037'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommonPremium',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=datetime.date.today)),
                ('per_year', models.PositiveIntegerField()),
                ('per_180_days', models.PositiveIntegerField()),
                ('per_90_days', models.PositiveIntegerField()),
                ('per_30_days', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='CommonPremiumPayments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=datetime.date.today)),
                ('amount', models.FloatField()),
                ('channel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.Channel')),
            ],
        ),
    ]
