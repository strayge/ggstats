# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-08-18 22:43
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ban',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('duration', models.PositiveIntegerField()),
                ('reason', models.CharField(max_length=800)),
                ('show', models.BooleanField(default=True)),
                ('permanent', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('channel_id', models.CharField(max_length=200, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='ChannelStats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('clients', models.IntegerField()),
                ('users', models.IntegerField()),
                ('channel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.Channel')),
            ],
        ),
        migrations.CreateModel(
            name='ChannelStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('up', models.BooleanField(default=True)),
                ('channel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.Channel')),
            ],
        ),
        migrations.CreateModel(
            name='CommonMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=400)),
                ('data', models.CharField(max_length=8000)),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='CommonPremium',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True, default=datetime.date.today)),
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
                ('date', models.DateField(db_index=True, default=datetime.date.today)),
                ('amount', models.FloatField()),
                ('channel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.Channel')),
            ],
        ),
        migrations.CreateModel(
            name='Donation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.FloatField()),
                ('text', models.CharField(max_length=4000)),
                ('link', models.CharField(max_length=1000)),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('voice', models.CharField(max_length=200, null=True)),
                ('channel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.Channel')),
            ],
        ),
        migrations.CreateModel(
            name='Follow',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('channel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.Channel')),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_id', models.BigIntegerField(db_index=True)),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('text', models.CharField(max_length=10000)),
                ('removed', models.BooleanField(db_index=True, default=False)),
                ('channel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.Channel')),
            ],
        ),
        migrations.CreateModel(
            name='PlayerChannelStats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('chat', models.IntegerField()),
                ('viewers', models.IntegerField()),
                ('viewers_gg', models.IntegerField()),
                ('status', models.BooleanField()),
                ('status_gg', models.BooleanField()),
                ('hidden', models.NullBooleanField()),
                ('channel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.Channel')),
            ],
        ),
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=800)),
                ('answers', models.CharField(max_length=2000)),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='PremiumActivation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('resubs', models.PositiveSmallIntegerField()),
                ('payment', models.PositiveSmallIntegerField()),
                ('channel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.Channel')),
            ],
        ),
        migrations.CreateModel(
            name='PremiumStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started', models.DateField(default=datetime.date.today)),
                ('ended', models.DateField(default=datetime.date.today, null=True)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now)),
                ('resubs', models.PositiveSmallIntegerField()),
                ('channel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.Channel')),
            ],
        ),
        migrations.CreateModel(
            name='TotalStats',
            fields=[
                ('timestamp', models.DateTimeField(primary_key=True, serialize=False)),
                ('clients', models.IntegerField()),
                ('users', models.IntegerField()),
                ('viewers', models.IntegerField()),
                ('viewers_gg', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('user_id', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('username', models.CharField(db_index=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='UserInChat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('end', models.DateTimeField(default=django.utils.timezone.now)),
                ('channel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.Channel')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.User')),
            ],
        ),
        migrations.CreateModel(
            name='Warning',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(max_length=800)),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('channel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.Channel')),
                ('moderator', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='warning_by', to='ggchat.User')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.User')),
            ],
        ),
        migrations.AddField(
            model_name='premiumstatus',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.User'),
        ),
        migrations.AddField(
            model_name='premiumactivation',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.User'),
        ),
        migrations.AddField(
            model_name='poll',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.User'),
        ),
        migrations.AddField(
            model_name='poll',
            name='channel',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.Channel'),
        ),
        migrations.AddField(
            model_name='message',
            name='removed_by',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='removed_by', to='ggchat.User'),
        ),
        migrations.AddField(
            model_name='message',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.User'),
        ),
        migrations.AddField(
            model_name='follow',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.User'),
        ),
        migrations.AddField(
            model_name='donation',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.User'),
        ),
        migrations.AddField(
            model_name='channel',
            name='streamer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.User'),
        ),
        migrations.AddField(
            model_name='ban',
            name='channel',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.Channel'),
        ),
        migrations.AddField(
            model_name='ban',
            name='moderator',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ban_by', to='ggchat.User'),
        ),
        migrations.AddField(
            model_name='ban',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ggchat.User'),
        ),
        migrations.AlterIndexTogether(
            name='userinchat',
            index_together=set([('channel', 'user')]),
        ),
    ]
