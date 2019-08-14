from django.shortcuts import render_to_response
from django.views.decorators.cache import cache_page

from ggchat.helpers import is_admin
from ggchat.models import *


@cache_page(10 * 60)
def chathistory(request, message_id, hash):
    from ggchat.templatetags.simplefilters import chat_hash
    message_id = int(message_id)

    time_range_in_minutes = 5
    if request.GET.get("long", ""):
        time_range_in_minutes = 60
    elif request.GET.get("verylong", ""):
        time_range_in_minutes = 7*24*60

    correct_hash = chat_hash(message_id)
    if correct_hash != hash:
        return render_to_response('ggchat/chathistory.html', {})

    message = Message.objects.filter(id=message_id).first()
    if not message:
        return render_to_response('ggchat/chathistory.html', {})

    channel_id = message.channel.channel_id
    timestamp = message.timestamp
    # timestamp = datetime.datetime.utcfromtimestamp(timestamp)
    timestamp_from = timestamp - datetime.timedelta(minutes=time_range_in_minutes)
    timestamp_to = timestamp + datetime.timedelta(minutes=time_range_in_minutes)
    messages = Message.objects.filter(channel_id=channel_id, timestamp__gte=timestamp_from, timestamp__lte=timestamp_to).order_by('-timestamp')[:1000]

    content = {'channel': message.channel,
               'messages': messages,
               'selected_message_id': message.id,
               'show_chat_links': is_admin(request),
               }
    return render_to_response('ggchat/chathistory.html', content)
