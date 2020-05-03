import locale
import queue
import time

import requests

from ggchat.management.commands._common import setup_logger
from ggchat.models import *

SAVE_STATS_PERIOD = 10 * 60
NON_LOGGING_MESSAGES = [
    'welcome',
    'success_join',
    'channel_counters',
    'channels_list',
    'error',
    'message',
    'channel_history',
    'users_list',
    'update_channel_info',
]
KNOWN_MESSAGES = [
    # skipped
    'welcome',
    'channels_list',
    'random_result',
    'new_poll',
    'error',
    'setting',
    'update_channel_info',
    'new_job',
    'job_prize_increased',
    'update_job',
    # processed
    'success_join',
    'channel_counters',
    'premium',
    'payment',
    'user_ban',
    'user_warn',
    'remove_message',
    'follower',
    'channel_history',
    'message',
    'users_list',
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
            self.log.warning('Unknown type: {}'.format(msg))
            return

        if msg_type == 'success_join':
            self.parse_channel_join(msg)

        elif msg_type == 'channel_counters':
            self.parse_counters(msg)

        elif msg_type == 'premium':
            self.parse_premium(msg)

        elif msg_type == 'payment':
            self.parse_payment(msg)

        elif msg_type == 'user_ban':
            self.parse_ban(msg)

        elif msg_type == 'user_warn':
            self.parse_warning(msg)

        elif msg_type == 'remove_message':
            self.parse_remove_message(msg)

        elif msg_type == 'follower':
            self.parse_follower(msg)

        elif msg_type == 'channel_history':
            messages = msg['data']['messages']
            for msg in messages:
                self.parse_message({'data': msg}, is_history=True)

        elif msg_type == 'message':
            self.parse_message(msg, is_history=False)

        elif msg_type == 'users_list':
            self.parse_users_list(msg)

    def parse_ban(self, msg):
        channel_id = msg['data']['channel_id']
        user_id = msg['data']['user_id']
        username = msg['data']['user_name']
        moderator_id = msg['data']['moder_id']
        moderator_username = msg['data']['moder_name']
        reason = msg['data']['reason']
        duration = int(msg['data'].get('duration', 0))
        ban_type = int(msg['data'].get('type', 0))
        show = bool(msg['data']['show'])

        permanent = ban_type == 2

        channel = Channel.objects.filter(channel_id=channel_id).first()
        user = User(user_id=user_id, username=username)
        user.save()
        moderator = User(user_id=moderator_id, username=moderator_username)
        moderator.save()

        if not channel:
            channel = Channel(channel_id=channel_id, streamer=None)
            channel.save()

        ban = Ban(
            user=user,
            channel=channel,
            moderator=moderator,
            duration=duration,
            reason=reason,
            show=show,
            permanent=permanent,
            ban_type=ban_type,
        )
        ban.save()

        self.mark_user_online(channel_id, moderator_id, moderator_username)

    def parse_warning(self, msg):
        channel_id = msg['data']['channel_id']
        user_id = msg['data']['user_id']
        username = msg['data']['user_name']
        moderator_id = msg['data']['moder_id']
        moderator_username = msg['data']['moder_name']
        reason = msg['data']['reason']

        channel = Channel.objects.filter(channel_id=channel_id).first()
        user = User(user_id=user_id, username=username)
        user.save()
        moderator = User(user_id=moderator_id, username=moderator_username)
        moderator.save()

        if not channel:
            channel = Channel(channel_id=channel_id, streamer=None)
            channel.save()

        warning = Warning(user=user, channel=channel, moderator=moderator, reason=reason)
        warning.save()

        self.mark_user_online(channel_id, moderator_id, moderator_username)

    def parse_users_list(self, msg):
        channel_id = msg['data']['channel_id']
        users = msg['data']['users']
        for user_data in users:
            user_id = user_data['id']
            username = user_data['name']
            self.mark_user_online(channel_id, user_id, username)

    def parse_message(self, msg, is_history=False):
        channel_id = msg['data']['channel_id']
        user_id = msg['data']['user_id']
        message_id = msg['data']['message_id']
        username = msg['data']['user_name']

        if is_history:
            old_message = Message.objects.filter(channel_id=channel_id, message_id=message_id).first()
            if old_message:
                return

        message_text = msg['data']['text']
        if len(message_text) > 10000:
            self.log.info('{}'.format(msg))
            self.log.warning('message too long ({})'.format(len(message_text)))
            message_text = message_text[:10000]

        user_premiums = msg['data']['premiums']
        user_resubs = msg['data']['resubs']

        user = User(user_id=user_id, username=username)
        user.save()

        channel = Channel.objects.filter(channel_id=channel_id).first()
        if not channel:
            channel = Channel(channel_id=channel_id, streamer=None)
            channel.save()

        message = Message(message_id=message_id, channel=channel, user=user, text=message_text)
        message.save()

        if not is_history:
            self.process_active_premiums(user_id, user_premiums, user_resubs)
            self.mark_user_online(channel_id, user_id, username)

    # current_prems: list of channel_id
    # resubs: dict: channel_id -> resub level
    def process_active_premiums(self, user_id, current_prems, current_resubs, only_new=False):
        prev_active_prems = PremiumStatus.objects.filter(user_id=user_id, ended=None)
        # end old prems
        if not only_new:
            for prem in prev_active_prems:
                # channel_id saved as str, so needed convert types in current_prems
                if prem.channel_id not in map(str, current_prems):
                    prem.ended = timezone.now()
                    prem.save()

        # add new prems
        for channel_id in current_prems:
            channel_id = str(channel_id)
            if channel_id in current_resubs:
                resubs = current_resubs[channel_id]
            else:
                resubs = 0

            channel = Channel.objects.filter(channel_id=channel_id).first()
            if not channel:
                continue

            # find active prev prem
            founded_prem = None
            for prem in prev_active_prems:
                if channel_id == prem.channel_id:
                    founded_prem = prem
                    break
            if founded_prem:
                founded_prem.modified = timezone.now()
                founded_prem.resubs = resubs
                founded_prem.save()
            else:
                new_prem = PremiumStatus(user_id=user_id, channel=channel, ended=None, resubs=resubs)
                new_prem.save()

    def parse_payment(self, msg):
        channel_id = msg['data']['channel_id']
        username = msg['data']['userName']
        amount = msg['data']['amount']
        text = msg['data']['message']
        link = msg['data']['link']
        user_id = msg['data']['userId']

        if 'voice' in msg['data']:
            voice = msg['data']['voice']
        else:
            voice = None

        user = User(user_id=user_id, username=username)
        if user_id == 0:
            user = User(user_id=0, username='Неизвестный')
        user.save()

        # donations to cups, showed on all subscribed channels
        if link:
            latest_donation_with_this_url = Donation.objects.filter(
                link=link, user=user,
                amount=amount,
                timestamp__gte=timezone.now() - timezone.timedelta(seconds=15),
            ).first()
            if not latest_donation_with_this_url:
                donation = Donation(user=user, channel=None, amount=amount, text=text, link=link, voice=voice)
                donation.save()
        else:
            channel = Channel.objects.filter(channel_id=channel_id).first()
            if channel:
                donation = Donation(user=user, channel=channel, amount=amount, text=text, link=link, voice=voice)
                donation.save()

    def parse_premium(self, msg):
        channel_id = msg['data']['channel_id']
        username = msg['data']['userName']
        user_resubs = msg['data']['resub']
        payment = msg['data']['payment']
        user_id = msg['data']['userId']

        channel = Channel.objects.filter(channel_id=channel_id).first()
        if not channel:
            channel = Channel(channel_id=channel_id, streamer=None)
            channel.save()

        user = User(user_id=user_id, username=username)
        if user_id != 0:
            user.save()
            self.process_active_premiums(user.user_id, [channel_id], {channel_id: user_resubs}, only_new=True)
            activation = PremiumActivation(channel=channel, user=user, resubs=user_resubs, payment=payment)
            activation.save()
        else:
            self.log.warning('Premium activated by anonymous')

    def parse_follower(self, msg):
        if 'channel_id' in msg['data']:
            channel_id = msg['data']['channel_id']
        else:
            channel_id = msg['data']['channel']

        if 'userName' in msg['data']:
            username = msg['data']['userName']
        else:
            username = msg['data']['username']

        user = User.objects.filter(username=username).first()

        if user:
            follow = Follow(user=user, channel_id=channel_id)
            follow.save()

    def parse_remove_message(self, msg):
        channel_id = msg['data']['channel_id']

        if 'message_id' not in msg['data']:
            self.log.info('remove_message without message_id, skipping...')
            return

        message_id = msg['data']['message_id']
        moderator_username = msg['data']['adminName']

        removed_message = Message.objects.filter(message_id=message_id).order_by('-timestamp').first()

        # save only first remove
        if removed_message and not removed_message.removed:
            removed_message.removed = True
            moderator = User.objects.filter(username=moderator_username).first()
            if moderator:
                removed_message.removed_by = moderator
            removed_message.save()

    def parse_channel_join(self, msg):
        channel_id = str(msg['data']['channel_id'])
        # save all changes in streamer (as user)
        if 'id' in msg['data']['channel_streamer']:
            streamer_id = msg['data']['channel_streamer']['id']
            streamer_username = msg['data']['channel_streamer']['name']
            streamer = User(user_id=streamer_id, username=streamer_username)
            streamer.save()
        else:
            streamer = None

        # save channel
        channel = Channel(channel_id=channel_id, streamer=streamer)
        channel.save()

        # streamer premiums and resubs save
        if streamer:
            streamer_premiums = msg['data']['channel_streamer'].get('premiums', [])
            streamer_resubs = msg['data']['channel_streamer'].get('resubs', {})
            self.process_active_premiums(streamer_id, streamer_premiums, streamer_resubs)

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

    def mark_user_online(self, channel_id, user_id, username):
        channel = Channel.objects.filter(channel_id=channel_id).first()
        if not channel:
            channel = Channel(channel_id=channel_id, streamer=None)
            channel.save()

        user = User.objects.filter(user_id=user_id).first()
        if not user:
            user = User(user_id=user_id, username=username)
            user.save()

        now = timezone.now()
        active_record = UserInChat.objects.filter(channel_id=channel_id, user_id=user_id,
                                                  end__gte=now - timezone.timedelta(minutes=35)).first()
        if active_record:
            active_record.end = now
            active_record.save()
        else:
            record = UserInChat(user_id=user_id, channel_id=channel_id, start=now, end=now)
            record.save()

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
