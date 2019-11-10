# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-11-06 23:02
from __future__ import unicode_literals

from django.db import migrations, models


def fill_ban_type(apps, schema_editor):
    Ban = apps.get_model('ggchat', 'Ban')
    Ban.objects.filter(permanent=True).update(ban_type=2)
    Ban.objects.filter(
        permanent=False,
        reason='До конца стрима',
        duration=5184000,
    ).update(ban_type=1)
    Ban.objects.filter(
        permanent=False,
        reason='До конца стрима',
        duration=2592000,
    ).update(ban_type=1)


class Migration(migrations.Migration):

    dependencies = [
        ('ggchat', '0005_auto_20190818_2329'),
    ]

    operations = [
        migrations.AddField(
            model_name='ban',
            name='ban_type',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.RunPython(fill_ban_type),
    ]