from django.db.models import Count
from django.shortcuts import render_to_response
from django.utils import timezone
from django.views.decorators.cache import cache_page

from ggchat.models import *


@cache_page(1 * 60 * 60)
def moderators(request):
    week_ago = timezone.now() - datetime.timedelta(days=7)
    warns = Warning.objects.filter(timestamp__gte=week_ago).values('moderator_id', 'moderator__username').annotate(count=Count('timestamp')).order_by('-count')
    bans = Ban.objects.filter(timestamp__gte=week_ago).values('moderator_id', 'moderator__username').annotate(count=Count('timestamp')).order_by('-count')
    removed_msgs = Message.objects.filter(timestamp__gte=week_ago, removed=True).values('removed_by_id', 'removed_by__username').annotate(count=Count('message_id')).order_by('-count')[:20]

    loyal_moders = []
    warns_dict = {}
    for w in warns:
        moderator_id = w['moderator_id']
        warns_dict[moderator_id] = {'moderator_id': moderator_id,
                                    'moderator__username': w['moderator__username'],
                                    'score': w['count']}
    for b in bans:
        moderator_id = b['moderator_id']
        count = b['count']
        if moderator_id in warns_dict:
            if count != 0:
                warns_dict[moderator_id]['score'] /= count
            else:
                warns_dict[moderator_id]['score'] += 100000
            loyal_moders.append(warns_dict[moderator_id])

    loyal_moders.sort(key=lambda x: x['score'], reverse=True)

    stupid_moders = Ban.objects.filter(timestamp__gte=week_ago, permanent=True).values('moderator_id', 'moderator__username').annotate(count=Count('timestamp')).order_by('-count')[:20]

    content = {'warns': warns[:20],
               'bans': bans[:20],
               'removed_msgs': removed_msgs,
               'loyal_moders': loyal_moders[:20],
               'stupid_moders': stupid_moders,
               }

    return render_to_response('ggchat/moderators.html', content)
