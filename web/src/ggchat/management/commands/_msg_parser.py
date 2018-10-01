import locale
import queue
import time

import requests
from ggchat.management.commands._common import setup_logger

import django
from django.utils import timezone
from ggchat.models import *


SAVE_STATS_PERIOD = 10 * 60


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
        if msg_type not in ['welcome', 'success_join', 'channel_counters', 'channels_list', 'error', 'message', 'channel_history']:
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

        if msg_type == 'welcome':
            pass

        elif msg_type == 'channels_list':
            pass

        elif msg_type == 'random_result':
            pass

        elif msg_type == 'new_poll':
            pass

        elif msg_type == 'error':
            pass

        elif msg_type == 'setting':
            pass

        elif msg_type == 'update_channel_info':
            pass

        elif msg_type == 'success_join':
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
                self.parse_message({'data': msg, 'history': True})

        elif msg_type == 'message':
            self.parse_message(msg)

        else:
            self.log.warning('Unknown type: {}'.format(msg))

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
            with requests.Session() as session:
                with session.get(url_gg) as resp:
                    if resp.status_code == 200:
                        answer_gg = resp.json()
                with session.get(url_all) as resp:
                    if resp.status_code == 200:
                        answer_all = resp.json()
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
                    player_stats = PlayerChannelStats(channel_id=channel_id,
                                                      chat=player_in_chat,
                                                      viewers=player_viewers,
                                                      viewers_gg=player_viewers_gg,
                                                      status=player_status,
                                                      status_gg=player_status_gg)
                    player_stats.save()
        self.log.info('periodic_processing end')

    def parse_ban(self, msg):
        channel_id = msg['data']['channel_id']
        user_id = msg['data']['user_id']
        username = msg['data']['user_name']
        moderator_id = msg['data']['moder_id']
        moderator_username = msg['data']['moder_name']
        reason = msg['data']['reason']
        duration = 0 if msg['data']['duration'] == '' else int(msg['data']['duration'])
        show = bool(msg['data']['show'])
        if 'permanent' in msg['data']:
            permanent = bool(msg['data']['permanent'])
        else:
            # Alice sends msg without 'permanent' key
            permanent = False

        channel = Channel.objects.filter(channel_id=channel_id).first()
        user = User(user_id=user_id, username=username)
        user.save()
        moderator = User(user_id=moderator_id, username=moderator_username)
        moderator.save()

        if not channel:
            channel = Channel(channel_id=channel_id, streamer=None)
            channel.save()

        ban = Ban(user=user, channel=channel, moderator=moderator, duration=duration,
                  reason=reason, show=show, permanent=permanent)
        ban.save()

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

    def parse_message(self, msg):
        is_history = msg.get('history', False)

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
            for premium_id in user_premiums:
                if str(premium_id) in user_resubs:
                    resubs = user_resubs[str(premium_id)]
                else:
                    resubs = 0

                channel = Channel.objects.filter(channel_id=premium_id).first()
                if channel:
                    last_premium = PremiumStatus.objects.filter(user=user, channel=channel).order_by('-modified').first()
                    if not last_premium or last_premium.ended is not None:
                        new_premium = PremiumStatus(user=user, channel=channel, ended=None, resubs=resubs)
                        new_premium.save()
                    else:
                        last_premium.modified = timezone.now()
                        last_premium.resubs = resubs
                        last_premium.save()

    def parse_payment(self, msg):
        channel_id = msg['data']['channel_id']
        username = msg['data']['userName']
        amount = msg['data']['amount']
        text = msg['data']['message']
        link = msg['data']['link']

        if 'voice' in msg['data']:
            voice = msg['data']['voice']
        else:
            voice = None

        user = User.objects.filter(username=username).first()
        if not user and username == 'Неизвестный':
            user = User(user_id=0, username='Неизвестный')
            user.save()

        # skip donations from not exists users
        if user:
            # donations to cups, showed on all subscribed channels
            if link:
                latest_donation_with_this_url = Donation.objects.filter(link=link, user=user,
                                                                        amount=amount,
                                                                        timestamp__gte=timezone.now() - timezone.timedelta(
                                                                            seconds=15)).first()
                if not latest_donation_with_this_url:
                    donation = Donation(user=user, channel=None, amount=amount, text=text, link=link, voice=voice)
                    donation.save()
            else:
                channel = Channel.objects.filter(channel_id=channel_id).first()
                if channel:
                    donation = Donation(user=user, channel=channel, amount=amount, text=text, link=link, voice=voice)
                    donation.save()
        else:
            self.log.info('Donation from non-existence user: {}'.format(msg))

    def parse_premium(self, msg):
        channel_id = msg['data']['channel_id']
        username = msg['data']['userName']
        user_resubs = msg['data']['resub']
        payment = msg['data']['payment']

        channel = Channel.objects.filter(channel_id=channel_id).first()
        if not channel:
            channel = Channel(channel_id=channel_id, streamer=None)
            channel.save()

        user = User.objects.filter(username=username).first()
        if user:
            last_premium = PremiumStatus.objects.filter(user=user, channel=channel).order_by('-modified').first()
            if not last_premium or last_premium.ended is not None:
                new_premium = PremiumStatus(user=user, channel=channel, ended=None, resubs=user_resubs)
                new_premium.save()
            else:
                # todo: had active premium and activated new, skip it?
                pass

            premium_status = PremiumActivation(user=user, channel=channel, resubs=user_resubs, payment=payment)
            premium_status.save()

    def parse_follower(self, msg):
        channel_id = msg['data']['channel_id']
        username = msg['data']['userName']

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
            # print('channel_streamer', channel_id)
        else:
            # print('NOT channel_streamer', channel_id)
            streamer = None

        # save channel
        channel = Channel(channel_id=channel_id, streamer=streamer)
        channel.save()

        # streamer premiums and resubs save
        if streamer:
            streamer_resubs = msg['data']['channel_streamer']['resubs'] if 'resubs' in msg['data'][
                'channel_streamer'] else {}
            streamer_premiums = msg['data']['channel_streamer']['premiums'] if 'premiums' in msg['data'][
                'channel_streamer'] else {}
            for premium_id in streamer_premiums:
                if str(premium_id) in streamer_resubs:
                    resubs = streamer_resubs[str(premium_id)]
                else:
                    resubs = 0
                last_premium = PremiumStatus.objects.filter(user=streamer, channel=channel).order_by(
                    '-modified').first()
                if not last_premium or last_premium.ended is not None:
                    new_premium = PremiumStatus(user=streamer, channel=channel, ended=None, resubs=resubs)
                    new_premium.save()
                else:
                    last_premium.modified = timezone.now()
                    last_premium.resubs = resubs
                    last_premium.save()

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
