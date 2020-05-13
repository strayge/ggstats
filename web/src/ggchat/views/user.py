from django.shortcuts import render_to_response
from django.views.decorators.cache import cache_page

from ggchat.models import *


@cache_page(10 * 60)
def user(request, user_id):
    user_obj = User.objects.filter(user_id=user_id).first()
    if not user_obj:
        return render_to_response('ggchat/user.html', {'title': 'Пользователь #{}'.format(user_id)})

    count_per_section = 10
    username = user_obj.username
    last_donations = Donation.objects.filter(user_id=user_id).order_by('-timestamp')[:count_per_section]
    channel = Channel.objects.filter(streamer_id=user_id).first()
    received_bans = Ban.objects.filter(user_id=user_id).order_by('-timestamp')[:count_per_section]

    content = {
        'name': username,
        'donations': last_donations,
        'user_id': user_id,
        'channel': channel,
        'received_bans': received_bans,
    }

    return render_to_response('ggchat/user.html', content)


@cache_page(10 * 60)
def user_by_name(request, username):
    user_obj = User.objects.filter(username=username).first()
    if not user_obj:
        return render_to_response('ggchat/user.html', {'title': 'Пользователь {}'.format(username)})
    user_id = user_obj.user_id
    return user(request, user_id)
