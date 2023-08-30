from collections import defaultdict
import time


DEFAULT_INTERVAL = 20 * 60


async def calc_total_stats(mongo, from_ts, to_ts):
    counters = await mongo.gg.counters.find(
        {'timestamp': {'$gte': from_ts, '$lte': to_ts}},
    ).sort('timestamp', 1).to_list(None)

    stats_per_channel: dict[int, dict[str, dict]] = defaultdict(dict)
    top_gg: dict[int, dict[str, int]] = defaultdict(dict)
    top_gg_hidden: dict[int, dict[str, int]] = defaultdict(dict)

    for row in counters:
        channel_id = row['channel_id']
        ts = row['timestamp'] // DEFAULT_INTERVAL * DEFAULT_INTERVAL
        hidden = bool(row.get('hidden'))
        clients = row.get('clients') or 0
        users = row.get('users') or 0
        viewers = row.get('viewers') or 0
        if channel_id in stats_per_channel[ts]:
            continue
        stats_per_channel[ts][channel_id] = {
            'clients': clients, 'users': users, 'viewers': viewers, 'hidden': hidden,
        }
        if hidden:
            top_gg_hidden[ts][channel_id] = viewers
        else:
            top_gg[ts][channel_id] = viewers

    limit = 3
    for ts, channels in top_gg.items():
        top_gg[ts] = dict(sorted(channels.items(), key=lambda x: x[1], reverse=True)[:limit])
    for ts, channels in top_gg_hidden.items():
        top_gg_hidden[ts] = dict(sorted(channels.items(), key=lambda x: x[1], reverse=True)[:limit])

    channel_ids = set()
    for channels in top_gg.values():
        channel_ids |= channels.keys()
    for channels in top_gg_hidden.values():
        channel_ids |= channels.keys()
    names_list = await mongo.gg.channels.find({'_id': {'$in': list(channel_ids)}}).to_list(None)
    names = {x['_id']: x['name'] for x in names_list}

    stats: dict[int, dict] = defaultdict(dict)
    for ts in stats_per_channel.keys():
        viewers = sum([x['viewers'] for x in stats_per_channel[ts].values() if not x['hidden']])
        viewers_hidden = sum([x['viewers'] for x in stats_per_channel[ts].values() if x['hidden']])
        clients = sum([x['clients'] for x in stats_per_channel[ts].values()])
        users = sum([x['users'] for x in stats_per_channel[ts].values()])
        stats[ts] = {
            'viewers': viewers,
            'viewers_hidden': viewers_hidden,
            'clients': clients,
            'users': users,
            'top': [(names.get(ch_id, f'#{ch_id}'), num) for ch_id, num in top_gg[ts].items()],
            'top_hidden': [(names.get(ch_id, f'#{ch_id}'), num) for ch_id, num in top_gg_hidden[ts].items()],
        }
    documents = [{'_id': ts, **stats[ts]} for ts in stats.keys()]
    if documents:
        await mongo.gg.stats.delete_many({'_id': {'$in': [x['_id'] for x in documents]}})
        await mongo.gg.stats.insert_many(documents)


def tooltip_from_dict(top_dict: dict):
    result = {}
    for ts, tops in top_dict.items():
        lines = []
        for name, value in tops:
            lines.append(f'<b>{name}</b>: {value}')
        result[ts] = '<br>'.join(lines)
    return result


async def viewers_common(mongo, from_date, range, interval_secs = DEFAULT_INTERVAL):
    last_row = await mongo.gg.stats.find_one(sort=[('timestamp', -1)])
    if last_row:
        latest_calced_timestamp = last_row['_id']
    else:
        latest_calced_timestamp = from_date

    # calc new part of data
    now = int(time.time())
    from_timestamp: int = max(from_date, latest_calced_timestamp)
    to_timestamp: int = min(now, from_timestamp + 12 * 60 * 60)
    while to_timestamp != now:
        await calc_total_stats(mongo, from_timestamp, to_timestamp)
        from_timestamp = to_timestamp
        to_timestamp = min(now, from_timestamp + 12 * 60 * 60)
    await calc_total_stats(mongo, from_date, now)

    each = round(interval_secs / DEFAULT_INTERVAL)
    stats = await mongo.gg.stats.find(
        {'_id': {'$gte': from_date, '$lte': now}},
    ).sort('_id', 1).to_list(None)
    stats = stats[::each]

    data_sum_users_list = []
    data_sum_clients_list = []
    data_sum_viewers_gg_list = []
    data_sum_viewers_gg_hidden_list = []

    data_viewers_gg_top = {}
    data_viewers_gg_hidden_top = {}

    for row in stats:
        timestamp_js = int(row['_id'] * 1000)
        data_sum_users_list.append({'timestamp': timestamp_js, 'value': row['users']})
        data_sum_clients_list.append({'timestamp': timestamp_js, 'value': row['clients']})
        data_sum_viewers_gg_list.append({'timestamp': timestamp_js, 'value': row['viewers']})
        data_sum_viewers_gg_hidden_list.append({'timestamp': timestamp_js, 'value': row['viewers_hidden']})
        data_viewers_gg_top[timestamp_js] = row['top']
        data_viewers_gg_hidden_top[timestamp_js] = row['top_hidden']

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
        # 'visible5': False,

        'zoom': True,
        'legend': True,
        # 'title': 'Зрители',
        'y_title': 'Количество',
    }
    return {'chart1': chart_users_total, 'title': 'Статистика по зрителям', 'range': range}
