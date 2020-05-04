import locale
import queue
import time

import requests

from ggchat.management.commands._common import setup_logger
from ggchat.models import *

SAVE_STATS_PERIOD = 10 * 60
NON_LOGGING_MESSAGES = [
    'channel_counters',
    'channel_history',
    'channels_list',
    'error',
    'message',
    'success_join',
    'update_channel_info',
    'users_list',
    'welcome',
]
KNOWN_MESSAGES = [
    'channel_counters',
    'channel_history',
    'channels_list',
    'error',
    'follower',
    'job_prize_increased',
    'message',
    'new_job',
    'new_poll',
    'payment',
    'premium',
    'random_result',
    'remove_message',
    'setting',
    'success_join',
    'update_channel_info',
    'update_job',
    'user_ban',
    'user_warn',
    'users_list',
    'welcome',
]


class ChatMsgParser:
    def __init__(self, log_level, queue_msg_parse):
        self.queue = queue_msg_parse
        self.log = setup_logger(log_level)

        self.log.debug('parser init')

        self.last_player_counters = 0
        self.PLAYER_COUNTERS_PERIOD = 5 * 60

        self.joined_channels_last_period = set()

        self.run()

    def run(self):
        self.log.info('parser run')
        while True:
            try:
                self.periodic_processing()
                # prevent infinite wait for process KeyboardInterrupt
                msg = self.queue.get(block=True, timeout=1)
                self.parse(msg)
            except queue.Empty:
                self.log.debug('queue empty')
                pass
            except (KeyboardInterrupt, SystemExit):
                self.log.info('parser interrupted')
                break
            except:
                self.log.exception('parser exception')
                time.sleep(10)

    def periodic_processing(self):
        now = time.time()
        if now > self.last_player_counters + self.PLAYER_COUNTERS_PERIOD:
            self.last_player_counters = now
            self.get_player_counters()

    def log_msg(self, msg_type, msg):
        if msg_type not in NON_LOGGING_MESSAGES:
            try:
                encoding = locale.getpreferredencoding()
                s = msg.__repr__().encode(encoding, 'ignore').decode(encoding)
                self.log.info('{}'.format(s))
            except:
                self.log.warning('error during printing "{}" msg'.format(msg_type))
        elif msg_type == 'error' and 'You are already connected to the channel' not in str(msg):
            self.log.warning('{}'.format(msg))

    def parse(self, msg):
        msg_type = msg['type'] if 'type' in msg else ''
        self.log_msg(msg_type, msg)

        if msg_type not in KNOWN_MESSAGES:
            # for changes debug
            self.log.warning('Unknown type: {}'.format(msg))
            return

        if msg_type == 'channel_counters':
            self.parse_counters(msg)

    def parse_counters(self, msg):
        channel_id = msg['data']['channel_id']
        users = int(msg['data']['users_in_channel'])
        clients = int(msg['data']['clients_in_channel'])

        if channel_id not in self.joined_channels_last_period:
            self.joined_channels_last_period.add(str(channel_id))

        try:
            last_status = ChannelStats.objects.filter(channel_id=channel_id).latest('timestamp')
            last_timestamp = last_status.timestamp
        except ChannelStats.DoesNotExist:
            last_timestamp = None

        # one time per SAVE_STATS_PERIOD//60 minutes save counter for each channel
        if not last_timestamp or timezone.now() > last_timestamp + timezone.timedelta(minutes=SAVE_STATS_PERIOD // 60):
            current_status = ChannelStats(channel_id=channel_id, users=users, clients=clients)
            current_status.save()

    def get_player_counters(self):
        # get stats from player for all joined channels
        if not self.joined_channels_last_period:
            return

        try:
            last_player_stats = PlayerChannelStats.objects.latest('timestamp')
            last_time_save_player_stats = last_player_stats.timestamp
        except PlayerChannelStats.DoesNotExist:
            last_time_save_player_stats = None

        # one time per SAVE_STATS_PERIOD//60 minutes save player's stats for all joined channels
        if not last_time_save_player_stats or timezone.now() > last_time_save_player_stats + timezone.timedelta(minutes=SAVE_STATS_PERIOD // 60):
            channels_ids_str = ','.join(self.joined_channels_last_period)
            self.joined_channels_last_period = set()
            url_gg = 'https://goodgame.ru/api/getggchannelstatus?id={}&fmt=json'.format(channels_ids_str)
            url_all = 'https://goodgame.ru/api/getchannelstatus?id={}&fmt=json'.format(channels_ids_str)
            answer_gg = {}
            answer_all = {}
            streams = {}
            with requests.Session() as session:
                try:
                    with session.get(url_gg, timeout=10) as resp:
                        if resp.status_code == 200:
                            answer_gg = resp.json()
                    with session.get(url_all, timeout=10) as resp:
                        if resp.status_code == 200:
                            answer_all = resp.json()

                    stream_url = 'https://goodgame.ru/api/4/stream?page={}'
                    # 1st page
                    with session.get(stream_url.format(1), timeout=10) as resp:
                        page = resp.json()
                        total_pages = page['queryInfo']['qty'] // page['queryInfo']['onPage'] + 1
                        # adding 1 page
                        for s in page['streams']:
                            streams[str(s['id'])] = s
                    # other pages
                    for pagenum in range(2, total_pages + 1):
                        with session.get(stream_url.format(pagenum), timeout=10) as resp:
                            page = resp.json()
                            for s in page['streams']:
                                streams[str(s['id'])] = s

                except requests.exceptions.SSLError:
                    self.log.error('SSLError during fetch player counters')

            if answer_gg and answer_all:
                for channel_id in answer_gg.keys():
                    player_in_chat = int(answer_gg[channel_id].get('usersinchat', 0))
                    player_viewers_gg = int(answer_gg[channel_id].get('viewers', 0))
                    player_viewers = 0
                    if channel_id in answer_all:
                        player_viewers = int(answer_all[channel_id].get('viewers', 0))
                    if answer_gg[channel_id].get('status', 'Dead').lower() == 'live':
                        player_status_gg = True
                    else:
                        player_status_gg = False
                    player_status = False
                    if channel_id in answer_all and answer_all[channel_id].get('status', 'Dead').lower() == 'live':
                        player_status = True

                    if player_status_gg and streams:
                        if channel_id in streams and streams[channel_id]['hidden'] not in ['1', 1]:
                            hidden = False
                        else:
                            hidden = True
                    else:
                        hidden = None

                    player_stats = PlayerChannelStats(
                        channel_id=channel_id,
                        chat=player_in_chat,
                        viewers=player_viewers,
                        viewers_gg=player_viewers_gg,
                        status=player_status,
                        status_gg=player_status_gg,
                        hidden=hidden,
                    )
                    player_stats.save()
        self.log.info('periodic_processing end')
