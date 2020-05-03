from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.views.decorators.cache import cache_page

from ggchat.helpers import is_admin
from ggchat.models import *


@cache_page(30 * 60)
def index(request):
    # todo: краткое описание
    latest_payments = Donation.objects.order_by('-timestamp')[:10]
    return render_to_response('ggchat/index.html', {'latest_payments': latest_payments})


def stats(request):
    output = 'stats: <br /> latest donation: <br />'
    latest_donation = Donation.objects.order_by('-timestamp').first()
    if latest_donation:
        output += str(latest_donation)
    return HttpResponse(output)


@cache_page(1 * 60 * 60)
def voice_player(request, url):
    return render_to_response('ggchat/voice_player.html', {'url': url})


@cache_page(24 * 60 * 60)
def removed(request):
    # count_per_section = 10
    # if "more" in request.GET:
    #     count_per_section = 50

    removed_messages = Message.objects.filter(removed=True).order_by('-timestamp')[:1000]

    content = {
        'removed_messages': removed_messages,
        'show_chat_links': is_admin(request),
    }

    return render_to_response('ggchat/removed.html', content)
