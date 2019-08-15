from django.shortcuts import render_to_response
from django.utils import timezone
from django.views.decorators.cache import cache_page

from ggchat.models import *

DEFAULT_INTERVAL = 20 * 60


def calc_total_stats(from_ts, to_ts):
    full_data = ChannelStats.objects.filter(timestamp__gte=from_ts, timestamp__lte=to_ts).values(
        'channel_id', 'timestamp', 'users', 'clients').all()
    full_data_player = PlayerChannelStats.objects.filter(timestamp__gte=from_ts, timestamp__lte=to_ts).exclude(
        hidden=True).values('channel_id', 'timestamp', 'viewers', 'viewers_gg', 'status', 'status_gg').all()
    data = {}
    for d in full_data:
        channel_id = d['channel_id']
        if channel_id not in data:
            data[channel_id] = {}
        timestamp = int(d['timestamp'].timestamp() // DEFAULT_INTERVAL)
        if timestamp not in data[channel_id]:
            data[channel_id][timestamp] = (d['users'], d['clients'], 0, 0)
    for d in full_data_player:
        channel_id = d['channel_id']
        if channel_id not in data:
            data[channel_id] = {}
        timestamp = int(d['timestamp'].timestamp() // DEFAULT_INTERVAL)

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
        ts = timestamp * DEFAULT_INTERVAL
        restores_timestamp = timezone.make_aware(datetime.datetime.fromtimestamp(ts))
        total_stats = TotalStats(timestamp=restores_timestamp, clients=clients, users=users, viewers=viewers,
                                 viewers_gg=viewers_gg)
        total_stats.save()


@cache_page(30 * 60)
def viewers_week(request):
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
                         'visible': False,

                         'data2': data_sum_users_list,
                         'x_keyword2': 'timestamp',
                         'y_keyword2': 'value',
                         'type2': 'area',
                         'name2': 'Залогиненных в чате (все каналы)',

                         # 'data3': data_sum_viewers_list,
                         # 'x_keyword3': 'timestamp',
                         # 'y_keyword3': 'value',
                         # 'type3': 'line',
                         # 'name3': 'Всего зрителей',
                         # 'color3': '#cccccc',

                         'data4': data_sum_viewers_gg_list,
                         'x_keyword4': 'timestamp',
                         'y_keyword4': 'value',
                         'type4': 'line',
                         'name4': 'Зрителей (без каналов под галкой)',
                         'color4': '#ff0000',

                         'zoom': True,
                         'legend': True,
                         # 'title': 'Зрители',
                         'y_title': 'Количество',
                         }

    # month_table = [{'month': 'month1', 'viewers_average': 1, 'viewers_median': 2, 'chat_average': 3, 'chat_median': 4}]
    # month_start = now - datetime.timedelta(days=now.day-1, hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond+1)
    # half_year_ago = month_start - datetime.timedelta(days=6*30)
    # half_year_ago = half_year_ago - datetime.timedelta(days=half_year_ago.day-1, hours=half_year_ago.hour, minutes=half_year_ago.minute, seconds=half_year_ago.second, microseconds=half_year_ago.microsecond)
    # full_data = TotalStats.objects.filter(timestamp__gte=half_year_ago, timestamp__lte=month_start).order_by('timestamp').all()
    # current_viewers = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    # current_chat = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    # current_month = -1
    # month_table = []
    # month = current_month
    # for total_stats in full_data:
    #     month = total_stats.timestamp.month
    #     if month != current_month:
    #         if current_month != -1:
    #             viewers_average = [median(x) for x in current_viewers if len(x)]
    #             chat_average = [median(x) for x in current_chat if len(x)]
    #             month_table.append({'month': current_month, 'viewers_average': viewers_average, 'chat_average': chat_average})
    #         current_viewers = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    #         current_chat = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
    #         current_month = month
    #     hour = total_stats.timestamp.hour
    #     if total_stats.viewers_gg != 0:
    #         current_viewers[hour].append(total_stats.viewers_gg)
    #     if total_stats.users != 0:
    #         current_chat[hour].append(total_stats.users)
    # viewers_average = [mean(x) for x in current_viewers if len(x)]
    # chat_average = [mean(x) for x in current_chat if len(x)]
    # month_table.append({'month': month, 'viewers_average': viewers_average, 'chat_average': chat_average})

    return render_to_response('ggchat/viewers.html', {'title': 'Статистика по зрителям',
                                                      'range': 'week',
                                                      'chart1': chart_users_total,
                                                      # 'month_table': month_table,
                                                      })


@cache_page(2 * 60 * 60)
def viewers_month(request):
    week_ago = timezone.now() - datetime.timedelta(days=30)

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
                         'visible': False,

                         'data2': data_sum_users_list,
                         'x_keyword2': 'timestamp',
                         'y_keyword2': 'value',
                         'type2': 'area',
                         'name2': 'Залогиненных в чате (все каналы)',

                         # 'data3': data_sum_viewers_list,
                         # 'x_keyword3': 'timestamp',
                         # 'y_keyword3': 'value',
                         # 'type3': 'line',
                         # 'name3': 'Всего зрителей',
                         # 'color3': '#cccccc',

                         'data4': data_sum_viewers_gg_list,
                         'x_keyword4': 'timestamp',
                         'y_keyword4': 'value',
                         'type4': 'line',
                         'name4': 'Зрителей (без каналов под галкой)',
                         'color4': '#ff0000',

                         'zoom': True,
                         'legend': True,
                         # 'title': 'Зрители',
                         'y_title': 'Количество',
                         }
    return render_to_response('ggchat/viewers.html', {'chart1': chart_users_total,
                                                      'title': 'Статистика по зрителям',
                                                      'range': 'month'})


@cache_page(24 * 60 * 60)
def viewers_year(request):
    year_ago = timezone.now() - datetime.timedelta(days=365)

    last_total_stats = TotalStats.objects.order_by('-timestamp').first()
    if last_total_stats:
        # latest_calced_timestamp = last_total_stats.timestamp
        latest_calced_timestamp = last_total_stats.timestamp - datetime.timedelta(minutes=40)
    else:
        latest_calced_timestamp = year_ago

    # calc new part of data
    now = timezone.now()
    from_timestamp = max(year_ago, latest_calced_timestamp)
    to_timestamp = min(now, from_timestamp + datetime.timedelta(hours=12))
    while to_timestamp != now:
        calc_total_stats(from_timestamp, to_timestamp)
        from_timestamp = to_timestamp
        to_timestamp = min(now, from_timestamp + datetime.timedelta(hours=12))
    calc_total_stats(from_timestamp, to_timestamp)

    INTERVAL = 2 * 60 * 60
    each = round(INTERVAL / DEFAULT_INTERVAL)

    full_data = TotalStats.objects.filter(timestamp__gte=year_ago).all()[::each]
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
                         'visible': False,

                         'data2': data_sum_users_list,
                         'x_keyword2': 'timestamp',
                         'y_keyword2': 'value',
                         'type2': 'area',
                         'name2': 'Залогиненных в чате (все каналы)',

                         # 'data3': data_sum_viewers_list,
                         # 'x_keyword3': 'timestamp',
                         # 'y_keyword3': 'value',
                         # 'type3': 'line',
                         # 'name3': 'Всего зрителей',
                         # 'color3': '#cccccc',

                         'data4': data_sum_viewers_gg_list,
                         'x_keyword4': 'timestamp',
                         'y_keyword4': 'value',
                         'type4': 'line',
                         'name4': 'Зрителей (без каналов под галкой)',
                         'color4': '#ff0000',

                         'zoom': True,
                         'legend': True,
                         # 'title': 'Зрители',
                         'y_title': 'Количество',
                         }
    return render_to_response(
        'ggchat/viewers.html',
        {'chart1': chart_users_total, 'title': 'Статистика по зрителям', 'range': 'year'}
    )
