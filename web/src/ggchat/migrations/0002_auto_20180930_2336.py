# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-09-30 23:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ggchat', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='message_id',
            field=models.BigIntegerField(db_index=True),
        ),
    ]
