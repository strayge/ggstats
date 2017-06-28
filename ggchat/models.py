import datetime

from django.db import models
from django.utils import timezone


class CommonMessage(models.Model):
    type = models.CharField(max_length=100)
    data = models.CharField(max_length=2000)
    timestamp = models.DateTimeField(default=timezone.now)


class Channel(models.Model):
    channel_id = models.PositiveIntegerField(primary_key=True)
    streamer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)


class ChannelStatus(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(default=timezone.now)
    up = models.BooleanField(default=True)


class User(models.Model):
    user_id = models.PositiveIntegerField(primary_key=True)
    username = models.CharField(max_length=50)


class Message(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(default=timezone.now)
    text = models.CharField(max_length=2000)
    removed = models.BooleanField(default=False)
    removed_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)


class Donation(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL)
    amount = models.FloatField()
    text = models.CharField(max_length=500)
    timestamp = models.DateTimeField()


class PremiumActivation(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(default=timezone.now)


class PremiumStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL)
    started = models.DateField(default=datetime.date.today())
    ended = models.DateField(default=datetime.date.today())
    modified = models.DateTimeField(default=timezone.now)
    resubs = models.PositiveSmallIntegerField()


class Poll(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL)
    author = models.ForeignKey(User, on_delete=models.SET_NULL)
    text = models.CharField(max_length=200)
    answers = models.CharField(max_length=500)
    timestamp = models.DateTimeField(default=timezone.now)


class Warning(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL)
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL)
    reason = models.CharField(max_length=200)
    timestamp = models.DateTimeField(default=timezone.now)


class Ban(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(default=timezone.now)
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL)
    duration = models.PositiveIntegerField()
    reason = models.CharField(max_length=200)
    show = models.BooleanField(default=True)


class ChannelStats(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(default=timezone.now)
    clients = models.IntegerField()
    users = models.IntegerField()


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(default=timezone.now)
