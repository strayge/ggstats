import datetime

import itertools
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils import timezone

from ggchat.models import Donation, ChannelStats, User, Message, PremiumActivation, Follow, PremiumStatus, Channel


def index(request):
    latest_payments = Donation.objects.order_by('-timestamp')[:10]
    return render_to_response('ggchat/index.html', {'latest_payments': latest_payments,
                                                    'title': 'Последние донаты'})


def stats(request):
    output = 'stats: <br /> latest donation: <br />'
    latest_donation = Donation.objects.order_by('-timestamp').first()
    if latest_donation:
        output += str(latest_donation)
    return HttpResponse(output)


def chart(request):
    all_needed_data = ChannelStats.objects.filter(channel_id='5').values('timestamp', 'users').all()
    all_needed_data2 = ChannelStats.objects.filter(channel_id='5').values('timestamp', 'clients').all()
    chart1 = {'data3': all_needed_data,
              'x_keyword3': 'timestamp',
              'y_keyword3': 'users',
              'type3': 'area',
              'name3': 'Зрителей',

              'data2': all_needed_data2,
              'x_keyword2': 'timestamp',
              'y_keyword2': 'clients',
              'type2': 'area',
              'name2': 'Клиентов',

              'zoom': True,
              'legend': True,
              'title': 'Зрители',
              'y_title': 'Количество',
              }
    return render_to_response('ggchat/chart.html', {'chart1': chart1})


def money(request):
    headers = ['Pag1', 'Page2', 'Pag3e', 'Page4']
    data = [['/index.html', '1265', '32.3%', '$321.33', ],
            ['/about.html', '261', '33.3%', '$234.12', ],
            ['/sales.html', '665', '21.3%', '$16.34', ], ]

    return render_to_response('ggchat/table.html', {'headers': headers,
                                                    'data': data,
                                                    'title': 'Деньги',
                                                    'text_pre': 'pre',
                                                    'text_after': 'after'})


def user(request, user_id):
    user_obj = User.objects.filter(user_id=user_id).first()
    if not user_obj:
        return render_to_response('ggchat/user.html', {'title': 'Пользователь #{}'.format(user_id)})

    username = user_obj.username
    last_messages = Message.objects.filter(user_id=user_id).order_by('-timestamp')[:10]
    last_donations = Donation.objects.filter(user_id=user_id).order_by('-timestamp')[:10]
    last_premiums = PremiumActivation.objects.filter(user_id=user_id).order_by('-timestamp')[:10]
    last_follows = Follow.objects.filter(user_id=user_id).order_by('-timestamp')[:10]
    active_premiums = PremiumStatus.objects.filter(user_id=user_id, ended=None)
    channel = Channel.objects.filter(streamer_id=user_id).first()

    content = {'name': username,
               'messages': last_messages,
               'donations': last_donations,
               'premiums': last_premiums,
               'follows': last_follows,
               'active_premiums': active_premiums,
               'user_id': user_id,
               'channel': channel
               }

    return render_to_response('ggchat/user.html', content)


def channel(request, channel_id):
    channel_obj = Channel.objects.filter(channel_id=channel_id).first()
    if not channel_obj:
        return render_to_response('ggchat/channel.html', {'title': 'Канал #{}'.format(channel_id)})

    last_messages = Message.objects.filter(channel_id=channel_id).order_by('-timestamp')[:10]
    last_donations = Donation.objects.filter(channel_id=channel_id).order_by('-timestamp')[:10]
    last_premiums = PremiumActivation.objects.filter(channel_id=channel_id).order_by('-timestamp')[:10]
    last_follows = Follow.objects.filter(channel_id=channel_id).order_by('-timestamp')[:10]
    active_premiums = PremiumStatus.objects.filter(channel_id=channel_id, ended=None)

    week_ago = timezone.now() - datetime.timedelta(days=7)
    chart_clients_data = ChannelStats.objects.filter(channel_id=channel_id, timestamp__gte=week_ago).values('timestamp', 'clients').all()
    chart_users_data = ChannelStats.objects.filter(channel_id=channel_id, timestamp__gte=week_ago).values('timestamp', 'users').all()
    chart_people = {'data': chart_clients_data,
                    'x_keyword': 'timestamp',
                    'y_keyword': 'clients',
                    'type': 'area',
                    'name': 'Всего',

                    'data2': chart_users_data,
                    'x_keyword2': 'timestamp',
                    'y_keyword2': 'users',
                    'type2': 'area',
                    'name2': 'Залогиненных',

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

                    'zoom': True,
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
    }

    return render_to_response('ggchat/channel.html', content)
