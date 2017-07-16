import datetime

import itertools

from django.db.models import Count, Min, Sum, Avg
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils import timezone
from django.views.decorators.cache import cache_page

from ggchat.models import Donation, ChannelStats, User, Message, PremiumActivation, Follow, PremiumStatus, \
    Channel, Ban, Warning, TotalStats, CommonPremiumPayments, PlayerChannelStats


@cache_page(60 * 10)
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


@cache_page(60 * 10)
def viewers(request):

    def calc_total_stats(from_ts, to_ts):
        full_data = ChannelStats.objects.filter(timestamp__gte=from_ts, timestamp__lte=to_ts).values('channel_id', 'timestamp', 'users', 'clients').all()
        full_data_player = PlayerChannelStats.objects.filter(timestamp__gte=from_ts, timestamp__lte=to_ts).values('channel_id', 'timestamp', 'viewers', 'viewers_gg', 'status', 'status_gg').all()
        INTERVAL = 20*60
        data = {}
        for d in full_data:
            channel_id = d['channel_id']
            if channel_id not in data:
                data[channel_id] = {}
            timestamp = int(d['timestamp'].timestamp() // INTERVAL)
            if timestamp not in data[channel_id]:
                data[channel_id][timestamp] = (d['users'], d['clients'], 0, 0)
        for d in full_data_player:
            channel_id = d['channel_id']
            if channel_id not in data:
                data[channel_id] = {}
            timestamp = int(d['timestamp'].timestamp() // INTERVAL)

            new_item = ()
            viewers = d['viewers'] if d['status'] else 0
            viewers_gg = d['viewers_gg'] if d['status_gg'] else 0
            if timestamp not in data[channel_id]:
                data[channel_id][timestamp] = (0, 0, viewers, viewers_gg)
            else:
                users, clients, v, vgg = data[channel_id][timestamp]
                if v == 0 or vgg == 0:
                    data[channel_id][timestamp] = (users, clients, viewers, viewers_gg)

        data_sum_users = {}
        data_sum_clients = {}
        data_sum_viewers = {}
        data_sum_viewers_gg = {}
        for channel_id in data:
            for timestamp in data[channel_id]:
                users, clients, viewers, viewers_gg = data[channel_id][timestamp]
                data_sum_users[timestamp] = data_sum_users.get(timestamp, 0) + users
                data_sum_clients[timestamp] = data_sum_clients.get(timestamp, 0) + clients
                data_sum_viewers[timestamp] = data_sum_viewers.get(timestamp, 0) + viewers
                data_sum_viewers_gg[timestamp] = data_sum_viewers_gg.get(timestamp, 0) + viewers_gg

        for timestamp, users in data_sum_users.items():
            if timestamp in data_sum_clients and timestamp in data_sum_viewers and timestamp in data_sum_viewers_gg:
                clients = data_sum_clients[timestamp]
                viewers = data_sum_viewers[timestamp]
                viewers_gg = data_sum_viewers_gg[timestamp]
            else:
                continue
            ts = timestamp * INTERVAL
            restores_timestamp = timezone.make_aware(datetime.datetime.fromtimestamp(ts))
            total_stats = TotalStats(timestamp=restores_timestamp, clients=clients,
                                     users=users, viewers=viewers, viewers_gg=viewers_gg)
            total_stats.save()

    week_ago = timezone.now() - datetime.timedelta(days=7)

    last_total_stats = TotalStats.objects.order_by('-timestamp').first()
    if last_total_stats:
        # latest_calced_timestamp = last_total_stats.timestamp
        latest_calced_timestamp = last_total_stats.timestamp - datetime.timedelta(minutes=40)
    else:
        latest_calced_timestamp = week_ago

    # calc new part of data
    now = timezone.now()
    from_timestamp = max(week_ago, latest_calced_timestamp)
    to_timestamp = min(now, from_timestamp + datetime.timedelta(hours=12))
    while to_timestamp != now:
        calc_total_stats(from_timestamp, to_timestamp)
        from_timestamp = to_timestamp
        to_timestamp = min(now, from_timestamp + datetime.timedelta(hours=12))
    calc_total_stats(from_timestamp, to_timestamp)

    full_data = TotalStats.objects.filter(timestamp__gte=week_ago).all()
    data_sum_users_list = []
    data_sum_clients_list = []
    data_sum_viewers_list = []
    data_sum_viewers_gg_list = []
    for total_stats in full_data:
        timestamp_js = total_stats.timestamp.timestamp() * 1000
        data_sum_users_list.append({'timestamp': timestamp_js, 'value': total_stats.users})
        data_sum_clients_list.append({'timestamp': timestamp_js, 'value': total_stats.clients})
        data_sum_viewers_list.append({'timestamp': timestamp_js, 'value': total_stats.viewers})
        data_sum_viewers_gg_list.append({'timestamp': timestamp_js, 'value': total_stats.viewers_gg})

    data_sum_users_list.sort(key=lambda x: x['timestamp'])
    data_sum_clients_list.sort(key=lambda x: x['timestamp'])
    data_sum_viewers_list.sort(key=lambda x: x['timestamp'])
    data_sum_viewers_gg_list.sort(key=lambda x: x['timestamp'])

    chart_users_total = {'data': data_sum_clients_list,
                         'x_keyword': 'timestamp',
                         'y_keyword': 'value',
                         'type': 'area',
                         'name': 'Всего в чате',

                         'data2': data_sum_users_list,
                         'x_keyword2': 'timestamp',
                         'y_keyword2': 'value',
                         'type2': 'area',
                         'name2': 'Залогиненных в чате',

                         'data3': data_sum_viewers_list,
                         'x_keyword3': 'timestamp',
                         'y_keyword3': 'value',
                         'type3': 'line',
                         'name3': 'Всего зрителей',
                         'color3': '#cccccc',

                         'data4': data_sum_viewers_gg_list,
                         'x_keyword4': 'timestamp',
                         'y_keyword4': 'value',
                         'type4': 'line',
                         'name4': 'Зрителей на GG плеере',
                         'color4': '#ff0000',

                         'zoom': True,
                         'legend': True,
                         # 'title': 'Зрители',
                         'y_title': 'Количество',
                         }
    return render_to_response('ggchat/chart.html', {'chart1': chart_users_total,
                                                    'title': 'Общее число зрителей'})


@cache_page(60 * 10)
def money(request):
    week_ago = timezone.now() - datetime.timedelta(days=7)
    donates_data = Donation.objects.filter(timestamp__gte=week_ago).order_by('-timestamp').values('user_id', 'channel_id', 'amount', 'timestamp')

    grouped_by_date = {}
    for donate in donates_data:
        date = donate['timestamp'].date()
        grouped_by_date[date] = grouped_by_date.get(date, 0) + donate['amount']
    grouped_by_date_list = []
    for date, amount in grouped_by_date.items():
        grouped_by_date_list.append({'date': date, 'amount': int(amount)})

    chart_donate_total = {'data': grouped_by_date_list,
                          'x_keyword': 'date',
                          'y_keyword': 'amount',
                          'type': 'column',
                          'name': 'Донат',
                          'title': '',
                          'y_title': 'Рублей',
                          }

    grouped_by_channel = {}
    for donate in donates_data:
        channel_id = donate['channel_id']
        # skip donates to cups
        if channel_id is None:
            continue
        grouped_by_channel[channel_id] = grouped_by_channel.get(channel_id, 0) + donate['amount']
    grouped_by_channel_list = []
    for channel_id, amount in grouped_by_channel.items():
        channel = Channel.objects.filter(channel_id=channel_id).first()
        if channel and channel.streamer:
            streamer_name = channel.streamer.username
        else:
            streamer_name = ''
        grouped_by_channel_list.append({'channel_id': channel_id, 'amount': int(amount), 'username': streamer_name})
    grouped_by_channel_list.sort(key=lambda x: x['amount'], reverse=True)

    # common prems stats
    latest_date = CommonPremiumPayments.objects.order_by('-date').first().date
    current_month_prems = CommonPremiumPayments.objects.filter(date=latest_date).values('channel_id', 'channel__streamer__username', 'amount').order_by('-amount').all()
    current_month_days = min(latest_date.day, 7)

    prev_month_days = 7 - current_month_days
    prev_month_last_day = latest_date - datetime.timedelta(days=latest_date.day)
    prev_month_day = CommonPremiumPayments.objects.filter(date__year=prev_month_last_day.year, date__month=prev_month_last_day.month).order_by('-date').first().date
    prev_month_prems = CommonPremiumPayments.objects.filter(date=prev_month_day).values('channel_id', 'channel__streamer__username', 'amount').order_by('-amount').all()

    # union dicts
    common_prems_dict = {}
    for prem in current_month_prems:
        channel_id = prem['channel_id']
        # if channel_id == '5':
        #     print('cur', prem['amount'], latest_date.day, current_month_days, prem['amount'] / latest_date.day * current_month_days)
        prem['amount'] = prem['amount'] / latest_date.day * current_month_days
        common_prems_dict[channel_id] = prem

    if prev_month_days:
        for prem in prev_month_prems:
            channel_id = prem['channel_id']
            # if channel_id == '5':
            #     print('prev', prem['amount'], prev_month_day.day, prev_month_days, prem['amount'] / prev_month_day.day * prev_month_days)
            prem['amount'] = prem['amount'] / prev_month_day.day * prev_month_days
            if channel_id in common_prems_dict:
                # if channel_id == '5':
                #     print('exists', common_prems_dict[channel_id]['amount'], prem['amount'])
                common_prems_dict[channel_id]['amount'] += prem['amount']
            else:
                # if channel_id == '5':
                #     print('not exists', prem['amount'])
                common_prems_dict[channel_id] = prem

    # convert resulted dict to list
    common_prems = list(common_prems_dict.values())
    common_prems.sort(key=lambda x: x['amount'], reverse=True)

    # common_prems = CommonPremiumPayments.objects.filter(date__gte=week_ago).values('channel_id', 'channel__streamer__username').annotate(sum=Sum('amount')).order_by('-sum')[:20]
    # for i in range(len(common_prems)):
    #     common_prems[i]['sum'] /= 7

    content = {'chart_donate_total': chart_donate_total,
               'donate_top_per_channel': grouped_by_channel_list[:15],
               'common_prems': common_prems[:20],
               }

    return render_to_response('ggchat/money.html', content)


@cache_page(60 * 1)
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


@cache_page(60 * 10)
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
    }

    return render_to_response('ggchat/channel.html', content)


@cache_page(60 * 10)
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


@cache_page(60 * 10)
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

@cache_page(60 * 10)
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
