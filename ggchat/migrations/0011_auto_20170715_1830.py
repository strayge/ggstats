# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-15 18:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ggchat', '0010_auto_20170715_1744'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donation',
            name='text',
            field=models.CharField(max_length=1000),
        ),
    ]
