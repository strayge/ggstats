# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-16 15:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ggchat', '0013_auto_20170716_1449'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='message',
            name='message_id',
            field=models.IntegerField(),
        ),
    ]