# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-29 14:17
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ggchat', '0002_auto_20170629_1942'),
    ]

    operations = [
        migrations.AlterField(
            model_name='premiumstatus',
            name='ended',
            field=models.DateField(default=datetime.date.today, null=True),
        ),
    ]