# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-03-19 12:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ggchat', '0015_donation_voice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='message_id',
            field=models.BigIntegerField(),
        ),
    ]
