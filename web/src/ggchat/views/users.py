from django.db.models import Count, Sum
from django.shortcuts import render_to_response
from django.utils import timezone
from django.views.decorators.cache import cache_page

from ggchat.models import *


@cache_page(1 * 60 * 60)
def users(request):
    week_ago = timezone.now() - datetime.timedelta(days=7)
    max_premiums = PremiumStatus.objects.filter(ended=None).values('user_id', 'user__username').annotate(count=Count('channel')).order_by('-count')[:20]
    max_sum_donations = Donation.objects.filter(timestamp__gte=week_ago).values('user_id', 'user__username').annotate(sum=Sum('amount')).order_by('-sum')[:20]
    max_count_donations = Donation.objects.filter(timestamp__gte=week_ago).values('user_id', 'user__username').annotate(count=Count('user')).order_by('-count')[:20]

    max_messages = Message.objects.filter(timestamp__gte=week_ago).values('user_id', 'user__username').annotate(count=Count('user')).order_by('-count')[:20]

    # peka_smiles = (':pekaclap:', ':insanepeka:', ':peka:', ':scarypeka:', ':ohmypeka:', ':pled:')
    # pekas = []
    #
    # for user_and_count in max_messages:
    #     user = user_and_count['user_id']
    #     messages = Message.objects.filter(timestamp__gte=week_ago, user=user).values('timestamp', 'text', 'user_id', 'user__username').all()
    #     if len(messages) < 10:
    #         continue
    #     peka_counter = 0
    #     for msg in messages:
    #         for smile in peka_smiles:
    #             peka_counter += msg['text'].count(smile)
    #     pekas_per_msg = '{:.2f}'.format(peka_counter / len(messages))
    #     pekas.append({'user_id': user, 'user__username': user_and_count['user__username'], 'count': pekas_per_msg})
    # pekas.sort(key=lambda x: x['count'], reverse=True)

    # todo: активный большую часть времени ???

    content = {'max_premiums': max_premiums,
               'max_sum_donations': max_sum_donations,
               'max_count_donations': max_count_donations,
               'max_messages': max_messages[:20],
               # 'pekas': pekas[:20],
               }
    return render_to_response('ggchat/users.html', content)
