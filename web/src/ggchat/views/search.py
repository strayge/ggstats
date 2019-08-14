from django.http import HttpResponseForbidden
from django.shortcuts import render_to_response
from django.utils import timezone
from django.views.decorators.cache import cache_page

from ggchat.helpers import calculate_hash, is_admin
from ggchat.models import *


@cache_page(5 * 60)
def search(request, channel_id, text):

    key = request.GET.get("key", "")
    valid_key = calculate_hash('search' + '|' + channel_id + '|' + text)[:16]

    if not is_admin(request) and (key != valid_key):
        return HttpResponseForbidden()

    time_limit = timezone.now() - datetime.timedelta(days=7)
    messages_limit = 10000

    if request.GET.get("more", ""):
        time_limit = timezone.now() - datetime.timedelta(days=14)
        messages_limit = messages_limit * 10

    if channel_id == '0':
        messages_limit = messages_limit * 10
        messages_in_range = Message.objects.filter(timestamp__gte=time_limit).order_by('-timestamp').values('message_id')[:messages_limit]
        first_message = messages_in_range[len(messages_in_range)-1]['message_id']
        messages = Message.objects.filter(message_id__gte=first_message, text__contains=text).order_by('-timestamp')
    else:
        channel_obj = Channel.objects.filter(channel_id=channel_id).first()
        messages = []
        if channel_obj:
            messages_in_range = Message.objects.filter(channel_id=channel_id, timestamp__gte=time_limit).order_by('-timestamp').values('message_id')[:messages_limit]
            first_message = messages_in_range[len(messages_in_range)-1]['message_id']
            messages = Message.objects.filter(channel_id=channel_id, message_id__gte=first_message, text__contains=text).order_by('-timestamp')

    content = {'messages': messages,
               'show_chat_links': is_admin(request),
               'key': valid_key,
               'channel_id': channel_id,
               'text': text,
               }
    return render_to_response('ggchat/search.html', content)
