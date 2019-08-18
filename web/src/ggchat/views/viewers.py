import json

from django.shortcuts import render_to_response
from django.utils import timezone
from django.views.decorators.cache import cache_page

from ggchat.models import *

DEFAULT_INTERVAL = 20 * 60


def calc_total_stats(from_ts, to_ts):
    full_data_chat = ChannelStats.objects.filter(timestamp__gte=from_ts, timestamp__lte=to_ts).values(
        'channel_id', 'timestamp', 'users', 'clients').all()
    full_data_player = PlayerChannelStats.objects.filter(timestamp__gte=from_ts, timestamp__lte=to_ts,).values(
        'channel_id', 'timestamp', 'viewers', 'viewers_gg', 'status', 'status_gg', 'hidden', 'channel__streamer__username').all()

    data_per_channel = {}
    top_gg = {}
    top_gg_hidden = {}

    for row in full_data_chat:
        channel_id = row['channel_id']
        if channel_id not in data_per_channel:
            data_per_channel[channel_id] = {}
        timestamp = int(row['timestamp'].timestamp() // DEFAULT_INTERVAL)
        if timestamp not in data_per_channel[channel_id]:
            data_per_channel[channel_id][timestamp] = {'chat_users': row['users'], 'chat_clients': row['clients']}

    for row in full_data_player:
        channel_id = row['channel_id']
        streamer = row['channel__streamer__username']
        if not streamer:
            streamer = f'#{channel_id}'
        is_hidden = bool(row['hidden'])
        if channel_id not in data_per_channel:
            data_per_channel[channel_id] = {}
        timestamp = int(row['timestamp'].timestamp() // DEFAULT_INTERVAL)
        if timestamp not in top_gg:
            top_gg[timestamp] = []
            top_gg_hidden[timestamp] = []

        viewers_gg = row['viewers_gg'] if row['status_gg'] else 0
        if timestamp not in data_per_channel[channel_id]:
            data_per_channel[channel_id][timestamp] = {}
        if not data_per_channel[channel_id][timestamp].get('viewers_gg') and not data_per_channel[channel_id][timestamp].get('viewers_gg_hidden'):
            if is_hidden:
                data_per_channel[channel_id][timestamp]['viewers_gg_hidden'] = viewers_gg
                top_gg_hidden[timestamp].append((streamer, viewers_gg))
            else:
                data_per_channel[channel_id][timestamp]['viewers_gg'] = viewers_gg
                top_gg[timestamp].append((streamer, viewers_gg))

    data_sum_users = {}
    data_sum_clients = {}
    data_sum_viewers_gg = {}
    data_sum_viewers_gg_hidden = {}
    for channel_id in data_per_channel:
        for timestamp in data_per_channel[channel_id]:
            data = data_per_channel[channel_id][timestamp]
            data_sum_users[timestamp] = data_sum_users.get(timestamp, 0) + data.get('chat_users', 0)
            data_sum_clients[timestamp] = data_sum_clients.get(timestamp, 0) + data.get('chat_clients', 0)
            data_sum_viewers_gg[timestamp] = data_sum_viewers_gg.get(timestamp, 0) + data.get('viewers_gg', 0)
            data_sum_viewers_gg_hidden[timestamp] = data_sum_viewers_gg_hidden.get(timestamp, 0) + data.get('viewers_gg_hidden', 0)

    for timestamp, users in data_sum_users.items():
        clients = data_sum_clients.get(timestamp, 0)
        viewers_gg = data_sum_viewers_gg.get(timestamp, 0)
        viewers_gg_hidden = data_sum_viewers_gg_hidden.get(timestamp, 0)

        top_gg_final = sorted(top_gg.get(timestamp, []), key=lambda x: x[1], reverse=True)[:3]
        top_gg_hidden_final = sorted(top_gg_hidden.get(timestamp, []), key=lambda x: x[1], reverse=True)[:3]

        ts = timestamp * DEFAULT_INTERVAL
        restores_timestamp = timezone.make_aware(datetime.datetime.fromtimestamp(ts))
        total_stats = TotalStats(
            timestamp=restores_timestamp,
            clients=clients, users=users, viewers_gg=viewers_gg, viewers_gg_hidden=viewers_gg_hidden,
            viewers_gg_top=json.dumps(top_gg_final),
            viewers_gg_hidden_top=json.dumps(top_gg_hidden_final),
        )
        total_stats.save()


def tooltip_from_dict(top_dict: dict):
    result = {}
    for ts, tops in top_dict.items():
        lines = []
        for name, value in tops:
            lines.append(f'<b>{name}</b>: {value}')
        result[ts] = '<br>'.join(lines)
    return result


def viewers_common(from_date, interval_secs, range):
    last_total_stats = TotalStats.objects.order_by('-timestamp').first()
    if last_total_stats:
        latest_calced_timestamp = last_total_stats.timestamp - datetime.timedelta(minutes=40)
    else:
        latest_calced_timestamp = from_date

    # calc new part of data
    now = timezone.now()
    from_timestamp = max(from_date, latest_calced_timestamp)
    to_timestamp = min(now, from_timestamp + datetime.timedelta(hours=12))
    while to_timestamp != now:
        calc_total_stats(from_timestamp, to_timestamp)
        from_timestamp = to_timestamp
        to_timestamp = min(now, from_timestamp + datetime.timedelta(hours=12))
    calc_total_stats(from_timestamp, to_timestamp)

    each = round(interval_secs / DEFAULT_INTERVAL)

    full_data = TotalStats.objects.filter(timestamp__gte=from_date).all()[::each]
    data_sum_users_list = []
    data_sum_clients_list = []
    data_sum_viewers_gg_list = []
    data_sum_viewers_gg_hidden_list = []

    data_viewers_gg_top = {}
    data_viewers_gg_hidden_top = {}

    for total_stats in full_data:
        timestamp_js = int(total_stats.timestamp.timestamp() * 1000)
        data_sum_users_list.append({'timestamp': timestamp_js, 'value': total_stats.users or 0})
        data_sum_clients_list.append({'timestamp': timestamp_js, 'value': total_stats.clients or 0})
        data_sum_viewers_gg_list.append({'timestamp': timestamp_js, 'value': total_stats.viewers_gg or 0})
        data_sum_viewers_gg_hidden_list.append({'timestamp': timestamp_js, 'value': total_stats.viewers_gg_hidden or 0})

        if total_stats.viewers_gg_top and total_stats.viewers_gg_hidden_top:
            data_viewers_gg_top[timestamp_js] = json.loads(total_stats.viewers_gg_top)
            data_viewers_gg_hidden_top[timestamp_js] = json.loads(total_stats.viewers_gg_hidden_top)

    data_sum_users_list.sort(key=lambda x: x['timestamp'])
    data_sum_clients_list.sort(key=lambda x: x['timestamp'])
    data_sum_viewers_gg_list.sort(key=lambda x: x['timestamp'])
    data_sum_viewers_gg_hidden_list.sort(key=lambda x: x['timestamp'])

    chart_users_total = {
        'data': data_sum_clients_list,
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

        'data4': data_sum_viewers_gg_list,
        'x_keyword4': 'timestamp',
        'y_keyword4': 'value',
        'type4': 'line',
        'name4': 'Зрителей (без каналов под галкой)',
        'color4': '#ff0000',
        'tooltips4': tooltip_from_dict(data_viewers_gg_top),

        'data5': data_sum_viewers_gg_hidden_list,
        'x_keyword5': 'timestamp',
        'y_keyword5': 'value',
        'type5': 'line',
        'name5': 'Зрителей (каналы под галкой)',
        'color5': '#cccccc',
        'tooltips5': tooltip_from_dict(data_viewers_gg_hidden_top),
        'visible5': False,

        'zoom': True,
        'legend': True,
        # 'title': 'Зрители',
        'y_title': 'Количество',
    }
    return render_to_response(
        'ggchat/viewers.html',
        {'chart1': chart_users_total, 'title': 'Статистика по зрителям', 'range': range}
    )


@cache_page(30 * 60)
def viewers_week(request):
    week_ago = timezone.now() - datetime.timedelta(days=7)
    return viewers_common(week_ago, DEFAULT_INTERVAL, 'week')


@cache_page(2 * 60 * 60)
def viewers_month(request):
    month_ago = timezone.now() - datetime.timedelta(days=30)
    return viewers_common(month_ago, DEFAULT_INTERVAL, 'month')


@cache_page(24 * 60 * 60)
def viewers_year(request):
    year_ago = timezone.now() - datetime.timedelta(days=365)
    return viewers_common(year_ago, 1 * 60 * 60, 'year')
