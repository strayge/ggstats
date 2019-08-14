from django.db.models import Count, Sum
from django.shortcuts import render_to_response
from django.utils import timezone
from django.views.decorators.cache import cache_page

from ggchat.models import *


@cache_page(1 * 60 * 60)
def chats(request):
    week_ago = timezone.now() - datetime.timedelta(days=7)
    deleted_messages = Message.objects.filter(removed=True).order_by('-timestamp')[:20]
    popular_chats = Message.objects.filter(timestamp__gte=week_ago).values('channel_id', 'channel__streamer__username').annotate(count=Count('message_id')).order_by('-count')[:20]

    warns = Warning.objects.filter(timestamp__gte=week_ago).values('user_id', 'user__username').annotate(count=Count('timestamp')).order_by('-count')
    bans = Ban.objects.filter(timestamp__gte=week_ago).values('user_id', 'user__username').annotate(count=Count('timestamp')).order_by('-count')

    top_trols = []
    for warn in warns:
        for ban in bans:
            if ban['user_id'] == warn['user_id']:
                break
        else:
            top_trols.append(warn)
            if len(top_trols) > 20:
                break

    # todo: наиболее популярные смайлы

    content = {'deleted_messages': deleted_messages,
               'popular_chats': popular_chats,
               'top_trols': top_trols,
               }
    return render_to_response('ggchat/chats.html', content)
