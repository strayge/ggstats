import datetime

from django.db import models
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

class CommonMessage(models.Model):
    type = models.CharField(max_length=100)
    data = models.CharField(max_length=2000)
    timestamp = models.DateTimeField(default=timezone.now)


class User(models.Model):
    user_id = models.PositiveIntegerField(primary_key=True)
    username = models.CharField(max_length=50)

    def __str__(self):
        return '{} (#{})'.format(self.username, self.user_id)


class Channel(models.Model):
    channel_id = models.CharField(max_length=50, primary_key=True)
    streamer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        try:
            return '{} (#{})'.format(self.streamer.username, self.channel_id)
        except ObjectDoesNotExist:
            return '#{}'.format(self.channel_id)


class ChannelStatus(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    up = models.BooleanField(default=True)


class Message(models.Model):
    message_id = models.IntegerField(primary_key=True)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    text = models.CharField(max_length=2000)
    removed = models.BooleanField(default=False)
    removed_by = models.ForeignKey(User, related_name='removed_by', on_delete=models.SET_NULL, null=True, default=None)

    def __str__(self):
        return '#{} {} @ {}: "{}"'.format(self.message_id, self.user, self.channel, self.text, )


class Donation(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    amount = models.FloatField()
    text = models.CharField(max_length=500)
    timestamp = models.DateTimeField()


class PremiumActivation(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now)


class PremiumStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    started = models.DateField(default=datetime.date.today)
    ended = models.DateField(default=datetime.date.today)
    modified = models.DateTimeField(default=timezone.now)
    resubs = models.PositiveSmallIntegerField()


class Poll(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.CharField(max_length=200)
    answers = models.CharField(max_length=500)
    timestamp = models.DateTimeField(default=timezone.now)


class Warning(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    moderator = models.ForeignKey(User, related_name='warning_by', on_delete=models.SET_NULL, null=True)
    reason = models.CharField(max_length=200)
    timestamp = models.DateTimeField(default=timezone.now)


class Ban(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    moderator = models.ForeignKey(User, related_name='ban_by', on_delete=models.SET_NULL, null=True)
    duration = models.PositiveIntegerField()
    reason = models.CharField(max_length=200)
    show = models.BooleanField(default=True)


class ChannelStats(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    clients = models.IntegerField()
    users = models.IntegerField()


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
