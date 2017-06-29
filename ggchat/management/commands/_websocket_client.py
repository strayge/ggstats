import asyncio
import json
import time
import logging

import websockets
from django.utils import timezone

from ggchat import models
from ggchat.models import CommonMessage, User, Channel, ChannelStatus, ChannelStats, Follow, Message

GG_CHAT_API2_ENDPOINT = 'ws://chat.goodgame.ru:8081/chat/websocket'
PERIODIC_PROCESSING_INTERVAL = 5 * 60


class WebsocketClient():
    def __init__(self):
        self.reset()
        logging.basicConfig()
        self.log = logging.getLogger()
        self.log.setLevel(logging.INFO)

    def reset(self):
        self.joined_channels = []

    def save_common_message(self, type, data):
        common_msg = CommonMessage(type=type, data=data)
        common_msg.save()
        # print('saved', type)

    async def parse_received(self, ws, received):
        # print(received)
        msg = json.loads(received)

        if msg['type'] not in ('welcome', 'error', 'success_join', 'channel_counters', 'message', 'channels_list'):
            self.log.info('{}'.format(msg))
        #     self.save_common_message(msg['type'], msg['data'])
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
            channel_id = str(msg['data']['channel_id'])
            self.joined_channels.append(channel_id)
            #self.log.info('joined: {}'.format(self.joined_channels))

            streamer_id = msg['data']['channel_streamer']['id']
            streamer_username = msg['data']['channel_streamer']['name']
            streamer = User(user_id=streamer_id, username=streamer_username)
            streamer.save()

            channel = Channel(channel_id=channel_id, streamer=streamer)
            channel.save()

            # streamer premiums and resubs save

        elif msg['type'] == 'channel_counters':
            # {'type': 'channel_counters',
            #  'data': {'channel_id': '39803',
            #           'clients_in_channel': '1126',
            #           'users_in_channel': 633}}
            channel_id = msg['data']['channel_id']
            users = int(msg['data']['users_in_channel'])
            clients = int(msg['data']['clients_in_channel'])

            try:
                last_status = ChannelStatus.objects.filter(channel_id=channel_id).latest('timestamp')
                last_timestamp = last_status.timestamp
            except ChannelStatus.DoesNotExist:
                last_timestamp = None
            if not last_timestamp or timezone.now() > last_timestamp + timezone.timedelta(minutes=5):
                current_status = ChannelStats(channel_id=channel_id, users=users, clients=clients)
                current_status.save()

        elif msg['type'] == 'premium':
            # {'type': 'premium',
            #  'data': {'channel_id': 58636,
            #           'userName': 'dmitrii.93'}}
            # print(msg)

            # {'type': 'premium', 'data': {'channel_id': 5, 'resub': '1', 'userName': 'dudeonthehorse', 'payment': '1'}}

            pass

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
            # print(msg)

            # {'type': 'payment', 'data': {'total': 0, 'amount': '100.00', 'channel_id': 27338, 'title': '', 'userName': 'Aard', 'message': '╨í╨╛╤é╨╡╨╜╤ç╨╕╨║ ╨╜╨░ ╨┐╨╕╨▓╨░╤ü. ╨ö╨╛╨╗╨│╨╛ ╨╡╤ë╨╡ ╨║╨░╤é╨░╤é╤î ╨▒╤â╨┤╨╡╤ê╤î?', 'link': ''}}


            channel_id = msg['data']['channel_id']
            username = msg['data']['userName']
            amount = msg['data']['amount']
            text = msg['data']['message']

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

            # {'type': 'user_ban', 'data': {'reason': '╨¥╨░ ╨╝╨╡╤ü╤Å╤å', 'user_id': '290711', 'permanent': 0, 'moder_rights': 10, 'moder_name': 'METALLman', 'channel_id': 21793, 'user_name': 'iloveoov13', 'moder_id': 52304, 'duration': 2592000, 'show': True, 'moder_premium': True}}
            pass

        elif msg['type'] == 'remove_message':
            # {'type': 'remove_message',
            #  'data': {'channel_id': 39803,
            #           'message_id': 207609,
            #           'adminName': 'iLame_ru'}}

            channel_id = msg['data']['channel_id']
            message_id = msg['data']['message_id']
            moderator_username = msg['data']['adminName']

            removed_message = Message.objects.filter(message_id=message_id).first()
            # todo: exception here?
            if removed_message:
                removed_message.removed=True
                moderator = User.objects.filter(username=moderator_username).first()
                # todo: exception here?
                if moderator:
                    removed_message.removed_by=moderator
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
            # todo: exception here?
            if user:
                follow = Follow(user=user, channel_id=channel_id)
                follow.save()

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
            pass

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
            #  'data': {'channel_id': 3893,
            #           'user_id': 322403,
            #           'user_name': 'Xippy',
            #           'user_rights': 0,
            #           'premium': True,
            #           'premiums': [3893],
            #           'stuff': '0',
            #           'hideIcon': 0,
            #           'color': 'premium-personal',
            #           'icon': 'star',
            #           'isStatus': 0,
            #           'mobile': 0,
            #           'payments': '0',
            #           'paidsmiles': [],
            #           'message_id': 203096,
            #           'timestamp': 1493061113,
            #           'text': 'ну из них же бандиты не очень', 'parsed': 'ну из них же бандиты не очень'
            #           }
            #  }
            # {'type': 'message',
            #  'data': {'channel_id': 26967,
            #           'user_id': 513167,
            #           'user_name': 'Nigruma',
            #           'user_rights': 10,
            #           'premium': True,
            #           'premiums': [0, 11123, 17966, 26967, 30023, 65484],
            #           'stuff': '0',
            #           'hideIcon': 0,
            #           'color': 'streamer',
            #           'icon': 'helper',
            #           'isStatus': 0,
            #           'mobile': 0,
            #           'payments': '4',
            #           'paidsmiles': [],
            #           'message_id': 215033,
            #           'timestamp': 1493061526,
            #           'text': 'Pontya, прекрасно выглядишь)', 'parsed': 'Pontya, прекрасно выглядишь)'
            #           }
            #  }
            # print(msg)
            channel_id = msg['data']['channel_id']
            user_id = msg['data']['user_id']
            message_id = msg['data']['message_id']
            username = msg['data']['user_name']
            user_premiums = msg['data']['premiums']
            message_text = msg['data']['text']

            # user = User.objects.filter(user_id=user_id).first()
            user = User(user_id=user_id, username=username)
            user.save()

            channel = Channel.objects.filter(channel_id=channel_id).first()
            if not channel:
                channel = Channel(channel_id=channel_id, streamer=None)
                channel.save()

            message = Message(message_id=message_id, channel=channel, user=user, text=message_text)
            message.save()

            # todo: processing payments and resubs?


        else:
            # unknown type
            self.log.warning('Unknown type: {}'.format(msg))
            # print('unknown type:', msg)

    async def periodic_processing(self, ws):
        print('periodic_processing')
        for i in range(5):
            # overlapping by 5
            get_channels_query = {"type": "get_channels_list", "data": {"start": str(i * 45), "count": "50"}}
            await ws.send(json.dumps(get_channels_query))

    async def run(self):
        while True:
            try:
                self.reset()
                ws = await websockets.connect(GG_CHAT_API2_ENDPOINT)
                last_periodic_processing = 0
                while True:
                    if time.time() > last_periodic_processing + PERIODIC_PROCESSING_INTERVAL:
                        last_periodic_processing = time.time()
                        await self.periodic_processing(ws)
                    received = await ws.recv()
                    await self.parse_received(ws, received)
            except (KeyboardInterrupt, SystemExit):
                break
            except (websockets.exceptions.ConnectionClosed,
                    websockets.exceptions.InvalidHandshake,
                    websockets.exceptions.WebSocketProtocolError,
                    websockets.exceptions.PayloadTooBig):
                print('WS error')
                time.sleep(10)
            except:
                print('Unknown error')
                import traceback
                print(traceback.format_exc())
                time.sleep(60)

    def start_forever(self):
        asyncio.get_event_loop().run_until_complete(self.run())
