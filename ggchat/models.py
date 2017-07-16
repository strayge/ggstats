import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone


class CommonMessage(models.Model):
    type = models.CharField(max_length=400)
    data = models.CharField(max_length=8000)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)


class User(models.Model):
    user_id = models.PositiveIntegerField(primary_key=True)
    username = models.CharField(max_length=200, db_index=True)

    def __str__(self):
        return '{}#{}'.format(self.username, self.user_id)


class Channel(models.Model):
    channel_id = models.CharField(max_length=200, primary_key=True)
    streamer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        try:
            return '{}#{}'.format(self.streamer.username, self.channel_id)
        except ObjectDoesNotExist:
            return '#{}'.format(self.channel_id)


class ChannelStatus(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    up = models.BooleanField(default=True)


class Message(models.Model):
    message_id = models.IntegerField()
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    text = models.CharField(max_length=10000)
    removed = models.BooleanField(default=False, db_index=True)
    removed_by = models.ForeignKey(User, related_name='removed_by', on_delete=models.SET_NULL, null=True, default=None)

    def __str__(self):
        return '#{} {} @ {}: "{}"'.format(self.message_id, self.user, self.channel, self.text, )


class Donation(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    amount = models.FloatField()
    text = models.CharField(max_length=4000)
    link = models.CharField(max_length=1000)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    def __str__(self):
        return '{} donated to {} {} rub. with text "{}"'.format(self.user, self.channel, self.amount, self.text)


class PremiumActivation(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    resubs = models.PositiveSmallIntegerField()
    payment = models.PositiveSmallIntegerField()


class PremiumStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    started = models.DateField(default=datetime.date.today)
    ended = models.DateField(default=datetime.date.today, null=True)
    modified = models.DateTimeField(default=timezone.now)
    resubs = models.PositiveSmallIntegerField()

    def __str__(self):
        if self.ended is None:
            return '{} has premium to {}'.format(self.user, self.channel)
        else:
            return '{} had premium to {} (ended)'.format(self.user, self.channel)


class Poll(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.CharField(max_length=800)
    answers = models.CharField(max_length=2000)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)


class Warning(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    moderator = models.ForeignKey(User, related_name='warning_by', on_delete=models.SET_NULL, null=True)
    reason = models.CharField(max_length=800)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)


class Ban(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    moderator = models.ForeignKey(User, related_name='ban_by', on_delete=models.SET_NULL, null=True)
    duration = models.PositiveIntegerField()
    reason = models.CharField(max_length=800)
    show = models.BooleanField(default=True)
    permanent = models.BooleanField(default=False)


class ChannelStats(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    clients = models.IntegerField()
    users = models.IntegerField()


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)


class CommonPremium(models.Model):
    date = models.DateField(default=datetime.date.today, db_index=True)
    per_year = models.PositiveIntegerField()
    per_180_days = models.PositiveIntegerField()
    per_90_days = models.PositiveIntegerField()
    per_30_days = models.PositiveIntegerField()


class CommonPremiumPayments(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    date = models.DateField(default=datetime.date.today, db_index=True)
    amount = models.FloatField()

    def __str__(self):
        return '{} {} {} rub.'.format(self.date, self.channel, self.amount)


class TotalStats(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    clients = models.IntegerField()
    users = models.IntegerField()
    viewers = models.IntegerField()
    viewers_gg = models.IntegerField()


class PlayerChannelStats(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    chat = models.IntegerField()
    viewers = models.IntegerField()
    viewers_gg = models.IntegerField()
    status = models.BooleanField()
    status_gg = models.BooleanField()
