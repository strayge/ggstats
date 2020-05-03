from django.db.models import Q, Sum
from django.shortcuts import render_to_response
from django.views.decorators.cache import cache_page

from ggchat.helpers import is_admin
from ggchat.models import *


@cache_page(10 * 60)
def user(request, user_id):
    user_obj = User.objects.filter(user_id=user_id).first()
    if not user_obj:
        return render_to_response('ggchat/user.html', {'title': 'Пользователь #{}'.format(user_id)})

    count_per_section = 10
    if "more" in request.GET:
        count_per_section = 50
    if 'muchmore' in request.GET:
        count_per_section = 500
    if 'muchmuchmore' in request.GET:
        count_per_section = 10000

    username = user_obj.username
    last_messages = Message.objects.filter(user_id=user_id).order_by('-timestamp')[:count_per_section]
    last_donations = Donation.objects.filter(user_id=user_id).order_by('-timestamp')[:count_per_section]
    last_premiums = PremiumActivation.objects.filter(user_id=user_id).order_by('-timestamp')[:count_per_section]
    last_follows = Follow.objects.filter(user_id=user_id).order_by('-timestamp')[:10]
    channel = Channel.objects.filter(streamer_id=user_id).first()
    if channel:
        active_premiums = PremiumStatus.objects.filter(user_id=user_id, ended=None).exclude(channel=channel)
    else:
        active_premiums = PremiumStatus.objects.filter(user_id=user_id, ended=None)
    bans = Ban.objects.filter(moderator_id=user_id).order_by('-timestamp')[:count_per_section]
    received_bans = Ban.objects.filter(user_id=user_id).order_by('-timestamp')[:count_per_section]
    removed_messages = Message.objects.filter(user_id=user_id, removed=True).order_by('-timestamp')[:count_per_section]

    donations_by_channel = Donation.objects.filter(user_id=user_id).values('channel_id', 'channel__streamer__username').annotate(sum=Sum('amount')).filter(sum__gt=0).order_by('-sum')
    donations_total = sum(d['sum'] for d in donations_by_channel)

    timeinchat = UserInChat.objects.filter(user_id=user_id).order_by('-end')[:count_per_section]

    week_ago = timezone.now() - datetime.timedelta(days=7)

    timeinchat_weekly_raw = UserInChat.objects.filter(user_id=user_id).filter(Q(start__gte=week_ago) | Q(end__gte=week_ago)).all()
    chat_time_per_channel = {}
    chat_channels = {}
    for rec in timeinchat_weekly_raw:
        chat_channels[rec.channel_id] = rec.channel
        time = (rec.end - max(week_ago, rec.start)).total_seconds()
        chat_time_per_channel[rec.channel_id] = chat_time_per_channel.get(rec.channel_id, 0) + time
    chat_top_time = []
    for chat_channel_id in chat_time_per_channel:
        chat_top_time.append((chat_channels[chat_channel_id], chat_time_per_channel[chat_channel_id]))
    chat_top_time.sort(key=lambda x: x[1], reverse=True)
    chat_top_time = chat_top_time[:count_per_section]

    content = {
        'name': username,
        'messages': last_messages,
        'donations': last_donations,
        'premiums': last_premiums,
        'follows': last_follows,
        'active_premiums': active_premiums,
        'user_id': user_id,
        'channel': channel,
        'received_bans': received_bans,
        'bans': bans,
        'removed_messages': removed_messages,
        'show_chat_links': is_admin(request),
        'donations_by_channel': donations_by_channel,
        'donations_total': donations_total,
        'timeinchat': timeinchat,
        'timeinchat_weekly': chat_top_time,
    }

    return render_to_response('ggchat/user.html', content)


@cache_page(10 * 60)
def user_by_name(request, username):
    user_obj = User.objects.filter(username=username).first()
    if not user_obj:
        return render_to_response('ggchat/user.html', {'title': 'Пользователь {}'.format(username)})
    user_id = user_obj.user_id
    return user(request, user_id)
