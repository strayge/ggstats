import itertools

from django.shortcuts import render_to_response
from django.utils import timezone
from django.views.decorators.cache import cache_page

from ggchat.helpers import is_admin
from ggchat.models import *


@cache_page(15 * 60)
def channel(request, channel_id):
    channel_obj = Channel.objects.filter(channel_id=channel_id).first()
    if not channel_obj:
        return render_to_response('ggchat/channel.html', {'title': 'Канал #{}'.format(channel_id)})

    count_per_section = 10
    chart_days = 7
    if "more" in request.GET:
        count_per_section = 50
        chart_days = 30
    if 'muchmore' in request.GET:
        count_per_section = 500
        chart_days = 365
    if 'muchmuchmore' in request.GET:
        count_per_section = 10000
        chart_days = 365

    last_messages = Message.objects.filter(channel_id=channel_id).order_by('-timestamp')[:count_per_section]
    last_donations = Donation.objects.filter(channel_id=channel_id).order_by('-timestamp')[:count_per_section]
    last_premiums = PremiumActivation.objects.filter(channel_id=channel_id).order_by('-timestamp')[:count_per_section]
    last_follows = Follow.objects.filter(channel_id=channel_id).order_by('-timestamp')[:count_per_section]
    active_premiums = PremiumStatus.objects.filter(channel_id=channel_id, ended=None)

    week_ago = timezone.now() - datetime.timedelta(days=chart_days)
    chart_clients_data = ChannelStats.objects.filter(channel_id=channel_id, timestamp__gte=week_ago).order_by('timestamp').values('timestamp', 'clients').all()
    chart_users_data = ChannelStats.objects.filter(channel_id=channel_id, timestamp__gte=week_ago).order_by('timestamp').values('timestamp', 'users').all()
    viewers_data_pre = PlayerChannelStats.objects.filter(channel_id=channel_id, timestamp__gte=week_ago).order_by('timestamp').values('timestamp', 'viewers', 'status').all()
    viewers_gg_data_pre = PlayerChannelStats.objects.filter(channel_id=channel_id, timestamp__gte=week_ago).order_by('timestamp').values('timestamp', 'viewers_gg', 'status_gg').all()
    viewers_data = []
    for x in viewers_data_pre:
        if not x['status']:
            x['viewers'] = 0
        del(x['status'])
        viewers_data.append(x)
    viewers_gg_data = []
    for x in viewers_gg_data_pre:
        if not x['status_gg']:
            x['viewers_gg'] = 0
        del(x['status_gg'])
        viewers_gg_data.append(x)

    chart_people = {'data': chart_clients_data,
                    'x_keyword': 'timestamp',
                    'y_keyword': 'clients',
                    'type': 'area',
                    'name': 'Всего в чате',
                    'visible': False,

                    'data2': chart_users_data,
                    'x_keyword2': 'timestamp',
                    'y_keyword2': 'users',
                    'type2': 'area',
                    'name2': 'Залогиненных в чате',

                    'data3': viewers_data,
                    'x_keyword3': 'timestamp',
                    'y_keyword3': 'viewers',
                    'type3': 'line',
                    'name3': 'Всего зрителей',
                    'color3': '#cccccc',

                    'data4': viewers_gg_data,
                    'x_keyword4': 'timestamp',
                    'y_keyword4': 'viewers_gg',
                    'type4': 'line',
                    'name4': 'Зрителей на GG плеере',
                    'color4': '#ff0000',

                    'zoom': True,
                    'legend': True,
                    'title': '',
                    'y_title': 'Количество',
                    }

    donates_data = Donation.objects.filter(channel_id=channel_id, timestamp__gte=week_ago).order_by('-timestamp').values('timestamp', 'amount')
    donates_grouped = [list(g) for t, g in itertools.groupby(donates_data, key=lambda donate: donate['timestamp'].date())]
    donates_grouped_and_summed = []
    for group in donates_grouped:
        date = group[0]['timestamp'].date()
        amount = 0
        for donate in group:
            amount += donate['amount']
        donates_grouped_and_summed.append({'date': date, 'amount': amount})

    chart_income = {'data': donates_grouped_and_summed,
                    'x_keyword': 'date',
                    'y_keyword': 'amount',
                    'type': 'column',
                    'name': 'Донат',

                    # 'zoom': True,
                    'legend': True,
                    'title': '',
                    'y_title': 'Рублей',
                    }

    content = {'channel': channel_obj,
               'messages': last_messages,
               'donations': last_donations,
               'premiums': last_premiums,
               'follows': last_follows,
               'active_premiums': active_premiums,
               'chart_people': chart_people,
               'chart_income': chart_income,
               'show_chat_links': is_admin(request),
    }

    return render_to_response('ggchat/channel.html', content)
