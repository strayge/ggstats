import logging
import time
import httpx

from motor.motor_asyncio import AsyncIOMotorClient

from ws import WsClient


class Client(WsClient):
    COUNTERS_INTERVAL = 10 * 60

    def __init__(self, mongo: AsyncIOMotorClient):
        super().__init__()
        self.mongo = mongo
        self._connected_channels = set()
        self._last_counters_ts = int(time.time()) - self.COUNTERS_INTERVAL + 60
        self._counters = {}
        self.http = httpx.AsyncClient()
        self.mongo.gg.premiums.create_index([('channel_id', 1)])
        self.mongo.gg.payments.create_index([('channel_id', 1)])
        self.mongo.gg.messages.create_index([('channel_id', 1)])
        self.mongo.gg.counters.create_index([('channel_id', 1)])

    async def on_start(self):
        logging.info('start')
        await self.send_get_channels_list()

    async def on_msg(self, msg: dict):
        msg_type = msg.get('type', '')
        if msg_type == 'channels_list':
            # {'type': 'channels_list', 'data': {'channels': [{'channel_id': '187877', 'clients_in_channel': 138, 'users_in_channel': 113}, {'channel_id': '15365', 'clients_in_channel': 104, 'users_in_channel': 73}, {'channel_id': '5', 'clients_in_channel': 35, 'users_in_channel': 26}, {'channel_id': '9348', 'clients_in_channel': 12, 'users_in_channel': 8}, {'channel_id': '103526', 'clients_in_channel': 12, 'users_in_channel': 8}, {'channel_id': 'r128', 'clients_in_channel': 21, 'users_in_channel': 6}, {'channel_id': 'cup:642ab9c7cddb590015abe39f.298fcf07-e5a5-45b9-b325-5cb81eb8f625', 'clients_in_channel': 0, 'users_in_channel': 0}, {'channel_id': '164639', 'clients_in_channel': 9, 'users_in_channel': 3}]}}
            await self.join_new_channels(msg['data']['channels'])
        elif msg_type == 'success_join':
            # {'type': 'success_join', 'data': {'channel_id': '26281', 'channel_name': 'сложность максимум', 'channel_key': 'kazam1984', 'channel_streamer': {'baninfo': False, 'banned': False, 'hidden': False, 'id': 299045, 'name': 'Otrod1e', 'avatar': '299045_eog8.jpg', 'payments': 7, 'premium': 1, 'premiums': ['26281'], 'resubs': {'26281': 7}, 'rights': 20, 'staff': 0, 'regtime': 1411513285, 'ggPlusTier': 0, 'role': ''}, 'motd': '', 'room_type': 'stream', 'room_premium': True, 'premium_price': 79, 'donate_buttons': '', 'clients_in_channel': 7, 'users_in_channel': 3, 'user_id': 0, 'name': '', 'access_rights': 0, 'premium_only': 0, 'premium': False, 'premiums': [], 'notifies': {}, 'resubs': {}, 'gg_plus_tier': 0, 'is_banned': False, 'banned_time': 0, 'reason': '', 'permanent': False, 'payments': 0, 'paymentsAll': {}, 'jobs': '1'}}
            channel_id = msg['data']['channel_id']
            self._connected_channels.add(channel_id)
            await self.send_get_users_list(channel_id)
        elif msg_type == 'unjoin':
            # {'type': 'unjoin', 'data': {'success': True}}
            ...
        elif msg_type == 'users_list':
            # {'type': 'users_list', 'data': {'channel_id': '195305', 'clients_in_channel': 0, 'users_in_channel': 2, 'users': [{'baninfo': False, 'banned': False, 'hidden': 0, 'id': 1125580, 'name': 'GorynychTV', 'avatar': '1125580_qzSb.png', 'payments': 0, 'premium': 0, 'premiums': ['148111'], 'resubs': {'148111': 7}, 'rights': 0, 'staff': 0, 'regtime': 1527779050, 'ggPlusTier': 0, 'role': ''}, {'baninfo': False, 'banned': False, 'hidden': 0, 'id': 764650, 'name': 'azenhorn', 'avatar': '764650_90VI.jpg', 'payments': 7, 'premium': 1, 'premiums': ['0', '195305'], 'resubs': {'0': 1, '195305': 7}, 'rights': 20, 'staff': 0, 'regtime': 1466958614, 'ggPlusTier': 2, 'role': ''}]}}
            await self.save_users_list(msg['data'])
        elif msg_type == 'message':
            # {'type': 'message', 'data': {'channel_id': '15365', 'user_id': 162675, 'user_name': 'Resmile', 'user_rights': 0, 'premium': 1, 'premiums': ['15365', '40756'], 'resubs': {'15365': 4, '40756': 2}, 'staff': 0, 'color': 'silver', 'icon': 'none', 'role': '', 'mobile': 0, 'payments': 2, 'paymentsAll': {'5': 2, '6515': 2, '13940': 1, '15365': 2, '35821': 2, '55600': 3, '90156': 1, '140682': 1, '176069': 1, '183946': 1}, 'gg_plus_tier': 0, 'isStatus': 0, 'message_id': 1693043578692, 'timestamp': 1693043579, 'text': 'marked0ne, :panic:', 'regtime': 1371037120}}
            await self.save_message(msg['data'])
        elif msg_type == 'channel_counters':
            # {'type': 'channel_counters', 'data': {'channel_id': '187877', 'clients_in_channel': 134, 'users_in_channel': 115}}
            channel_id = msg['data']['channel_id']
            users = msg['data']['users_in_channel']
            if users == 0:
                await self.send_leave_channel(channel_id)
            else:
                self._counters[channel_id] = msg['data']
                now = int(time.time())
                if now - self._last_counters_ts > self.COUNTERS_INTERVAL:
                    await self.save_counters()
                    self._last_counters_ts = now
                    self._counters.clear()
        elif msg_type == 'update_channel_info':
            # {'type': 'update_channel_info', 'data': {'channel_id': '5', 'premium_only': 0, 'started': 0}}
            ...
        elif msg_type == 'remove_message':
            # {'type': 'remove_message', 'data': {'channel_id': '163568', 'message_id': 1693044447764, 'adminName': 'HomoStarr'}}
            ...
        elif msg_type == 'setting':
            # {'type': 'setting', 'data': {'channel_id': '1239', 'name': 'motd', 'value': 'https://challonge.com/ru/3fuc0dqa', 'moder_id': 21210, 'moder_name': 'Strange', 'moder_rights': 20, 'moder_premium': True, 'silent': 1}}
            if msg['data'].get('name') != 'motd':
                logging.info(str(msg))
        elif msg_type == 'new_poll':
            # {'type': 'new_poll', 'data': {'channel_id': '32558', 'title': '1', 'answers': [{'id': 0, 'text': 'варвар', 'voters': 0}, {'id': 1, 'text': 'жрец', 'voters': 0}, {'id': 2, 'text': 'плут', 'voters': 0}], 'moder_id': 254310, 'moder_name': 'MyToH'}}
            ...
        elif msg_type == 'follower':
            # {'type': 'follower', 'data': {'userId': 58559, 'user_id': 58559, 'username': 'MyDream', 'userName': 'MyDream', 'channel_id': 158456}}
            ...
        elif msg_type == 'user_warn':
            # {'type': 'user_warn', 'data': {'channel_id': '190074', 'user_id': 532735, 'user_name': 'Yogurtkill', 'moder_id': 94363, 'moder_name': 'Gojji', 'moder_rights': 10, 'moder_premium': True, 'reason': ''}}
            ...
        elif msg_type == 'user_ban':
            # {'type': 'user_ban', 'data': {'channel_id': '45507', 'user_id': 116718, 'user_name': 'Smit_Bir', 'moder_id': 470771, 'moder_name': 'D1sconnect4', 'moder_rights': 20, 'moder_premium': True, 'duration': 1200, 'type': 0, 'reason': '', 'show': True}}
            ...
        elif msg_type == 'payment':
            # {'type': 'payment', 'data': {'userId': '779436', 'userName': 'marked0ne', 'channel_id': '15365', 'amount': '1111.00', 'message': 'ну с ДР. С НГ тада', 'voice': '', 'total': 0, 'title': '', 'link': '', 'gift': 0, 'is_commission_covered': False}}
            await self.save_payment(msg['data'])
        elif msg_type == 'premium':
            # {'type': 'premium', 'data': {'channel_id': '139026', 'userId': '1605798', 'userName': 'Agroshkolnik42', 'payment': 0, 'resub': '1'}}
            await self.save_premium(msg['data'])
        elif msg_type == 'gifted_premiums':
            # {'type': 'gifted_premiums', 'data': {'channel_id': 190074, 'title': 'Премиум на 30 дней на канал jokie', 'payer': 'marked0ne', 'users': [{'id': 1234163, 'username': 'Krommm_77'}]}}
            await self.save_gifted_premiums(msg['data'])
        else:
            logging.info(str(msg))

    async def on_send(self, msg: dict):
        ...

    async def on_periodic(self):
        logging.info(f'periodic channels: {len(self._connected_channels)}')
        await self.send_get_channels_list()
        for channel_id in self._connected_channels:
            await self.send_get_users_list(channel_id)

    async def join_new_channels(self, channels: list[dict]):
        for channel in channels:
            channel_id = channel['channel_id']
            users = channel['users_in_channel']
            if channel_id.startswith('cup:'):
                continue
            if channel_id not in self._connected_channels and users > 0:
                await self.send_join_channel(channel_id)

    async def send_get_channels_list(self):
        msg = {"type": "get_channels_list", "data": {"start": 0, "count": 500}}
        await self.send(msg)

    async def send_join_channel(self, channel_id: str):
        msg = {"type": "join", "data": {"channel_id": channel_id}}
        await self.send(msg)

    async def send_leave_channel(self, channel_id: str):
        msg = {"type": "unjoin", "data": {"channel_id": channel_id}}
        await self.send(msg)
        self._connected_channels.remove(channel_id)

    async def send_get_users_list(self, channel_id: str):
        msg = {"type": "get_users_list2", "data": {"channel_id": channel_id}}
        await self.send(msg)

    async def save_users_list(self, msg: dict):
        channel_id = msg['channel_id']
        now = int(time.time())
        users = []
        for user_data in msg['users']:
            user = {
                'channel_id': channel_id,
                'timestamp': now,
                'user_id': int(user_data['id']),
                'username': user_data['name'],
                'rights': int(user_data['rights']),
                'is_sub': bool(user_data['premium']),
                'plus_tier': int(user_data['ggPlusTier']),
                'pay_tier': int(user_data['payments']),
                'is_banned': bool(user_data['banned']),
            }
            users.append(user)
        if users:
            await self.mongo.gg.users.insert_many(users)

    async def save_counters(self):
        channels = list(self._counters.keys())
        request = await self.http.get(f'https://goodgame.ru/api/4/streams/2/ids?ids={",".join(channels)}')
        request.raise_for_status()
        request_json = request.json()
        now = int(time.time())
        counters = []
        for channel_id, chat_counters in self._counters.items():
            counters.append({
                'channel_id': channel_id,
                'timestamp': now,
                'clients': chat_counters['clients_in_channel'],
                'users': chat_counters['users_in_channel'],
                'viewers': request_json.get(channel_id, {}).get('viewers'),
            })
        await self.mongo.gg.counters.insert_many(counters)

    async def save_message(self, msg: dict):
        now = int(time.time())
        message = {
            'channel_id': msg['channel_id'],
            'timestamp': now,
            'user_id': int(msg['user_id']),
            'username': msg['user_name'],
            'rights': int(msg['user_rights']),
            'is_sub': bool(msg['premium']),
            'plus_tier': int(msg['gg_plus_tier']),
            'pay_tier': int(msg['payments']),
            'is_mobile': bool(msg['mobile']),
            'text': msg['text'],
        }
        await self.mongo.gg.messages.insert_one(message)

    async def save_payment(self, msg: dict):
        now = int(time.time())
        payment = {
            'channel_id': msg['channel_id'],
            'timestamp': now,
            'user_id': int(msg['userId']),
            'username': msg['userName'],
            'amount': float(msg['amount']),
            'text': msg['message'],
            'voice': bool(msg['voice']),
            'comission_covered': bool(msg['is_commission_covered']),
        }
        await self.mongo.gg.payments.insert_one(payment)

    async def save_premium(self, msg: dict):
        now = int(time.time())
        premium = {
            'channel_id': msg['channel_id'],
            'timestamp': now,
            'user_id': int(msg['userId']),
            'username': msg['userName'],
            'text': '',
            'payed_by': '',
            'gift': False,
        }
        await self.mongo.gg.premiums.insert_one(premium)

    async def save_gifted_premiums(self, msg: dict):
        now = int(time.time())
        channel_id = msg['channel_id']
        text = msg['title']
        payed_by = msg['payer']
        gifts = []
        for user_data in msg['users']:
            gift = {
                'channel_id': channel_id,
                'timestamp': now,
                'user_id': int(user_data['id']),
                'username': user_data['username'],
                'text': text,
                'payed_by': payed_by,
                'gift': True,
            }
            gifts.append(gift)
        if gifts:
            await self.mongo.gg.premiums.insert_many(gifts)
