

class Parser:
    def parse(self, msg):
        msg = json.loads(received)

        if msg['type'] not in ('welcome', 'error', 'success_join', 'channel_counters', 'channels_list', 'message',
                               'follower'):
            self.log.info('{}'.format(msg))
        if msg['type'] == 'error' and 'You are already connected to the channel' not in str(msg):
                self.log.warning('{}'.format(msg))
        # self.save_common_message(msg['type'], msg['data'])
        # else:


        if msg['type'] == 'welcome':
            # {'type': 'welcome',
            #  'data': {'protocolVersion': 1.1,
            #           'serverIdent': 'GG-chat/1.0 beta'}}
            pass

        elif msg['type'] == 'channels_list':
            # {'type': 'channels_list',
            #  'data': {'channels': [{'channel_id': '5',
            #                         'channel_name': 'Разное',
            #                         'clients_in_channel': '2264',
            #                         'users_in_channel': 1086},
            #                        {'channel_id': '39803',
            #                         'channel_name': 'PUBG RU (EU SERVER) - 132 WINS (22 SOLO, 75 DUO, 35 SQUAD)',
            #                         'clients_in_channel': '1067',
            #                         'users_in_channel': 603},
            #                        {'channel_id': '36628',
            #                         'channel_name': 'JesusAVGN',
            #                         'clients_in_channel': '1431',
            #                         'users_in_channel': 481},
            #                        {'channel_id': '1644',
            #                         'channel_name': 'Starline #4 - группа C',
            #                         'clients_in_channel': '745',
            #                         'users_in_channel': 361},
            #                        {'channel_id': '6968',
            #                         'channel_name': 'Happy stream! NetEase\\w3arena + 20:00 MooCup (random race/hero)!',
            #                         'clients_in_channel': '686',
            #                         'users_in_channel': 349}
            #                        ]
            #          }
            # }
            for channel in msg['data']['channels']:
                channel_id = channel['channel_id']
                if channel_id not in self.joined_channels:
                    # print('"{}" not in {}'.format(channel_id, self.joined_channels))
                    join_channel_query = {"type": "join", "data": {"channel_id": str(channel_id), "hidden": False}}
                    await ws.send(json.dumps(join_channel_query))

        elif msg['type'] == 'success_join':
            # {'type': 'success_join',
            #  'data': {'channel_id': 5,
            #           'channel_name': 'Разное',
            #           'channel_streamer': {'id': '1',
            #                                'name': 'Miker',
            #                                'avatar': '1_BObO.gif',
            #                                'rights': 50,
            #                                'payments': '3',
            #                                'premiumChannels': [0, 5, 84308],
            #                                'premium': True},
            #           'motd': '<a target="_blank" rel="nofollow" href="https://goodgame.ru/multigg/miker/igorghk/">https://goodgame.ru/multigg/miker/igorghk/</a>\\n\\nЛучшие моменты по BATTLEGROUNDS\\n<a target="_blank" rel="nofollow" href="https://goodgame.ru/video/46502">https://goodgame.ru/video/46502</a>',
            #           'slowmod': 0,
            #           'smiles': 1,
            #           'smilePeka': 1,
            #           'clients_in_channel': '2265',
            #           'users_in_channel': 1086,
            #           'user_id': 0,
            #           'name': '',
            #           'access_rights': 0,
            #           'premium_only': 0,
            #           'started': 1493048388,
            #           'room_privacy': 0,
            #           'room_role': 0,
            #           'premium': 0,
            #           'premiums': [],
            #           'stuff': [],
            #           'is_banned': False,
            #           'banned_time': 0,
            #           'reason': '',
            #           'permanent': 0,
            #           'payments': 0,
            #           'paidsmiles': []
            #           }
            #  }

            # {'type': 'success_join',
            #  'data': {'channel_id': 56532,
            #           'channel_name': 'Top 2 Tinker DotabuFF, Tinker, Invoker, Storm gameplay',
            #           'channel_streamer': {},
            #           'motd': '',
            #           'slowmod': 0,
            #           'smiles': 1,
            #           'smilePeka': 1,
            #           'clients_in_channel': '9',
            #           'users_in_channel': 5,
            #           'user_id': 0, 'name': '',
            #           'access_rights': 0,
            #           'premium_only': 0,
            #           'started': 1498752541,
            #           'room_privacy': 0,
            #           'room_role': 0,
            #           'premium': 0,
            #           'premiums': [],
            #           'notifies': {},
            #           'resubs': {},
            #           'staff': [],
            #           'is_banned': False,
            #           'banned_time': 0,
            #           'reason': '',
            #           'permanent': 0,
            #           'payments': 0,
            #           'paidsmiles': []
            #           }
            #  }

            # keep joined channels to avoid retrying connections to it
            channel_id = str(msg['data']['channel_id'])
            self.joined_channels.append(channel_id)

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
                streamer_resubs = msg['data']['channel_streamer']['premiumResubs']
                streamer_premiums = msg['data']['channel_streamer']['premiumChannels']
                for premium_id in streamer_premiums:
                    if str(premium_id) in streamer_resubs:
                        resubs = streamer_resubs[str(premium_id)]
                    else:
                        resubs = 0
                    last_premium = PremiumStatus.objects.filter(user=streamer, channel=channel).order_by('-modified').first()
                    if not last_premium or last_premium.ended is not None:
                        new_premium = PremiumStatus(user=streamer, channel=channel, ended=None, resubs=resubs)
                        new_premium.save()
                    else:
                        last_premium.modified = timezone.now()
                        last_premium.resubs = resubs
                        last_premium.save()

        elif msg['type'] == 'channel_counters':
            # {'type': 'channel_counters',
            #  'data': {'channel_id': '39803',
            #           'clients_in_channel': '1126',
            #           'users_in_channel': 633}}
            channel_id = msg['data']['channel_id']
            users = int(msg['data']['users_in_channel'])
            clients = int(msg['data']['clients_in_channel'])

            try:
                last_status = ChannelStats.objects.filter(channel_id=channel_id).latest('timestamp')
                last_timestamp = last_status.timestamp
            except ChannelStats.DoesNotExist:
                last_timestamp = None

            # one time per SAVE_STATS_PERIOD//60 minutes save counter for each channel
            if not last_timestamp or timezone.now() > last_timestamp + timezone.timedelta(minutes=SAVE_STATS_PERIOD // 60):
                current_status = ChannelStats(channel_id=channel_id, users=users, clients=clients)
                current_status.save()

        elif msg['type'] == 'premium':
            # {'type': 'premium',
            #  'data': {'channel_id': 58636,
            #           'userName': 'dmitrii.93'}}
            # {'type': 'premium',
            #  'data': {'channel_id': 5,
            #           'resub': '1',
            #           'userName': 'dudeonthehorse',
            #           'payment': '1'
            #           }
            #  }

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

        elif msg['type'] == 'update_channel_info':
            # {'type': 'update_channel_info',
            #    'data': {'channel_id': '58636',
            #             'premium_only': 0,
            #             'started': 1493051455}
            #  }
            pass

        elif msg['type'] == 'payment':
            # {'type': 'payment',
            #    'data': {'channel_id': 54105,
            #             'userName': 'kaprisulya',
            #             'amount': '100.00',
            #             'message': 'на монокль для Дяди Вани',
            #             'total': 0,
            #             'title': '',
            #             'link': ''}
            #  }
            # {'type': 'payment',
            #  'data': {'total': 0,
            #           'amount': '100.00',
            #           'channel_id': 27338,
            #           'title': '',
            #           'userName': 'Aard',
            #           'message': '╨í╨╛╤é╨╡╨╜╤ç╨╕╨║ ╨╜╨░ ╨┐╨╕╨▓╨░╤ü. ╨ö╨╛╨╗╨│╨╛ ╨╡╤ë╨╡ ╨║╨░╤é╨░╤é╤î ╨▒╤â╨┤╨╡╤ê╤î?',
            #           'link': ''
            #           }
            #  }
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
                        amount=amount, timestamp__gte=timezone.now() - timezone.timedelta(seconds=15)).first()
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

        elif msg['type'] == 'user_ban':
            # {'type': 'user_ban',
            #  'data': {'channel_id': 5,
            #           'user_id': '72941',
            #           'user_name': 'Qhardcore',
            #           'moder_id': 843678,
            #           'moder_name': 'gersern',
            #           'moder_rights': 10,
            #           'moder_premium': True,
            #           'duration': 2592000,
            #           'permanent': 0,
            #           'reason': 'На месяц',
            #           'show': True}}

            # {'type': 'user_ban',
            #  'data': {'reason': '╨¥╨░ ╨╝╨╡╤ü╤Å╤å',
            #           'user_id': '290711',
            #           'permanent': 0,
            #           'moder_rights': 10,
            #           'moder_name': 'METALLman',
            #           'channel_id': 21793,
            #           'user_name': 'iloveoov13',
            #           'moder_id': 52304,
            #           'duration': 2592000,
            #           'show': True,
            #           'moder_premium': True
            #           }
            # }
            #
            # {'type': 'user_ban',
            #  'data': {'channel_id': 1644,
            #           'user_id': 559101,
            #           'user_name': 'Nerazim',
            #           'moder_id': 108148,
            #           'moder_name': 'Alice',
            #           'moder_rights': 40,
            #           'moder_premium': 1,
            #           'duration': 3600,
            #           'reason': 'Маты, оскорбления',
            #           'show': True}}
            channel_id = msg['data']['channel_id']
            user_id = msg['data']['user_id']
            username = msg['data']['user_name']
            moderator_id = msg['data']['moder_id']
            moderator_username = msg['data']['moder_name']
            reason = msg['data']['reason']
            duration = int(msg['data']['duration'])
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

        elif msg['type'] == 'user_warn':
            # {'type': 'user_warn',
            #  'data': {'channel_id': 9348,
            #           'user_id': 800206,
            #           'user_name': 'ekvilior',
            #           'moder_id': 108148,
            #           'moder_name': 'Alice',
            #           'moder_rights': 40,
            #           'moder_premium': 1,
            #           'reason': ''}}
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

        elif msg['type'] == 'remove_message':
            # {'type': 'remove_message',
            #  'data': {'channel_id': 39803,
            #           'message_id': 207609,
            #           'adminName': 'iLame_ru'}}

            channel_id = msg['data']['channel_id']
            message_id = msg['data']['message_id']
            moderator_username = msg['data']['adminName']

            removed_message = Message.objects.filter(message_id=message_id).order_by('-timestamp').first()

            if removed_message:
                removed_message.removed = True
                moderator = User.objects.filter(username=moderator_username).first()
                if moderator:
                    removed_message.removed_by = moderator
                removed_message.save()

        elif msg['type'] == 'setting':
            # {'type': 'setting',
            #  'data': {'channel_id': 24477,
            #           'name': 'motd',
            #           'value': 'Stalker Shadow of Chernobyl ПРОЙДЕН\\nТекущая игра Stalker Clear Sky без смертей, Мах Сложность \\nЗа спойлер, лжеспойлер по сюжету или луту - БАН\\n\\n2: <a target="_blank" rel="nofollow" href="https://goodgame.ru/clip/54018/">https://goodgame.ru/clip/54018/</a> \\n3: <a target="_blank" rel="nofollow" href="https://goodgame.ru/clip/54189/">https://goodgame.ru/clip/54189/</a> чудо пули и дерево\\n5: <a target="_blank" rel="nofollow" href="https://goodgame.ru/clip/54279/">https://goodgame.ru/clip/54279/</a> трахокабан\\n6: <a target="_blank" rel="nofollow" href="https://goodgame.ru/clip/54578/">https://goodgame.ru/clip/54578/</a> ерись\\n9: <a target="_blank" rel="nofollow" href="https://goodgame.ru/clip/55262/">https://goodgame.ru/clip/55262/</a> кушай лимончик чики брики\\n\\nWerwik сделал нарезку гуфов по S.T.A.L.K.E.R. приятного просмотра! \\nПоддержите плюсом если вам понравилось.\\n<a target="_blank" rel="nofollow" href="https://goodgame.ru/video/46532/">https://goodgame.ru/video/46532/</a>\\n\\nТак же прошлый клип по Fallout 4 \\n<a target="_blank" rel="nofollow" href="https://goodgame.ru/video/46086">https://goodgame.ru/video/46086</a>\\nНовый комикс <a target="_blank" rel="nofollow" href="http://imgur.com/a/XHXOb">http://imgur.com/a/XHXOb</a>',
            #           'moder_id': 120126,
            #           'moder_name': 'Werwik',
            #           'moder_rights': 10,
            #           'moder_premium': True,
            #           'silent': 1}}
            pass

        elif msg['type'] == 'follower':
            # {'type': 'follower',
            #  'data': {'channel_id': 32399,
            #           'userName': 'Timorfiys'}}
            channel_id = msg['data']['channel_id']
            username = msg['data']['userName']

            user = User.objects.filter(username=username).first()

            if user:
                follow = Follow(user=user, channel_id=channel_id)
                follow.save()

        elif msg['type'] == 'random_result':
            # {'type': 'random_result',
            #  'data': {'channel_id': 5,
            #           'success': True,
            #           'data': {'id': '165231',
            #                    'name': 'DWD_MECH',
            #                    'rights': 0,
            #                    'premium': False,
            #                    'premiums': [],
            #                    'banned': False,
            #                    'baninfo': False,
            #                    'payments': '0',
            #                    'hidden': False,
            #                    'stuff': '0'
            #                    }
            #           }
            # }
            pass

        elif msg['type'] == 'new_poll':
            # {{'type': 'new_poll',
            #   'data': {'channel_id': 184,
            #            'moder_id': 48996,
            #            'moder_name': 'ZERGTV',
            #            'title': '?',
            #            'answers': [{'id': 1, 'text': 'прибытие'},
            #                        {'id': 2, 'text': 'бен гур'},
            #                        {'id': 3, 'text': 'из машины'},
            #                        {'id': 4, 'text': 'шиндлер'}]
            #            }
            # }
            pass

        elif msg['type'] == 'error':
            # {'type': 'error',
            #  'data': {'channel_id': 5,
            #           'error_num': 0,
            #           'errorMsg': 'You are already connected to the channel `5`.'}}
            pass

        elif msg['type'] == 'message':
            # {'type': 'message',
            #  'data': {'channel_id': 96424,
            #           'user_id': 152472,
            #           'user_name': 'QuicklyDotaTV',
            #           'user_rights': 20,
            #           'premium': 0,
            #           'premiums': [86096],
            #           'resubs': {'86096': 1},
            #           'staff': '0',
            #           'hideIcon': 0,
            #           'color': 'streamer',
            #           'icon': 'none',
            #           'isStatus': 0,
            #           'mobile': 0,
            #           'payments': '0',
            #           'paidsmiles': [],
            #           'message_id': 19423,
            #           'timestamp': 1498743747,
            #           'text': 'если будет стрим, зовите :D',
            #           'parsed': 'если будет стрим, зовите :D'
            #           }
            #  }
            # {'type': 'message',
            #  'data': {'channel_id': 53637,
            #           'user_id': 237309,
            #           'user_name': 'Sleepman',
            #           'user_rights': 0,
            #           'premium': 0,
            #           'premiums': [],
            #           'resubs': {},
            #           'staff': '0',
            #           'hideIcon': 0,
            #           'color': 'simple',
            #           'icon': 'none',
            #           'isStatus': 0,
            #           'mobile': 0,
            #           'payments': '0',
            #           'paidsmiles': [],
            #           'message_id': 251406,
            #           'timestamp': 1498743736,
            #           'text': 'ner_uto, <a target="_blank" rel="nofollow" href="https://eu.battle.net/download/getInstaller?os=win&amp;installer=StarCraft-Setup.exe">https://eu.battle.net/download/getInstaller?os=win&amp;installer=StarCraft-Setup.exe</a> - попробуй',
            #           'parsed': 'ner_uto, <a target="_blank" rel="nofollow" href="https://eu.battle.net/download/getInstaller?os=win&amp;installer=StarCraft-Setup.exe">https://eu.battle.net/download/getInstaller?os=win&amp;installer=StarCraft-Setup.exe</a> - попробуй'
            #           }
            #  }

            channel_id = msg['data']['channel_id']
            user_id = msg['data']['user_id']
            message_id = msg['data']['message_id']
            username = msg['data']['user_name']

            message_text = msg['data']['text']

            # if message_text.startswith('gif:'):
            #     self.log.info(msg)

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

        else:
            # unknown type
            self.log.warning('Unknown type: {}'.format(msg))
            # print('unknown type:', msg)