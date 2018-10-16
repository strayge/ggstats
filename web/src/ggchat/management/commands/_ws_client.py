import asyncio
import json
import time

import websockets

# from ggchat.management.commands._common import setup_logger

from ggchat.management.commands._ws_base import WsBaseClient

WS_ENDPOINT = 'wss://chat-1.goodgame.ru/chat2/'

PREDEFINED_CHANNELS = []  # '5', '94546', 'r128', '13214']

class ChatWsClient(WsBaseClient):
    def __init__(self, log_level, queue_msg_parse, queue_old_cmd, queue_old_cmd_resp):
        self.queue_msg_parse = queue_msg_parse
        self.queue_old_cmd = queue_old_cmd
        self.queue_old_cmd_resp = queue_old_cmd_resp

        self.joined_channels = set()
        self.last_channels_list_check = 0
        self.CHECK_CHANNELS_PERIOD = 5 * 60

        self.CHECK_USERS_PERIOD = 15 * 60
        self.last_users_check = time.time() - (self.CHECK_USERS_PERIOD - 60)  # start in 1 min after start
        super().__init__(log_level=log_level, endpoint=WS_ENDPOINT)

    async def ws_connected(self):
        self.joined_channels = set()
        self.last_channels_list_check = 0
        # for channel_id in PREDEFINED_CHANNELS:
        #     await self.join_channel(channel_id)

    async def ws_periodic_tasks(self):
        while not self.queue_old_cmd_resp.empty():
            received = self.queue_old_cmd_resp.get()
            await self.ws_received(received)
        if time.time() > self.last_users_check + self.CHECK_USERS_PERIOD:
            self.log.info('users check')
            self.last_users_check = time.time()
            for channel_id in self.joined_channels:
                query = {"type": "get_users_list2", "data": {"channel_id": str(channel_id)}}
                await self.send(query)

        now = time.time()
        if now > self.last_channels_list_check + self.CHECK_CHANNELS_PERIOD:
            self.last_channels_list_check = now
            await self.request_channels()

    async def join_channel(self, channel_id):
        self.queue_old_cmd.put({'type': 'join', 'data': channel_id})
        join_channel_query = {"type": "join", "data": {"channel_id": str(channel_id), "hidden": False}}
        await self.send(join_channel_query)

    async def request_channels(self):
        # sync channels
        self.queue_old_cmd.put({'type': 'channels', 'data': self.joined_channels})

        get_channels_query = {"type": "get_channels_list", "data": {"start": 0, "count": 200}}
        await self.send(get_channels_query)

    async def send(self, data):
        s = json.dumps(data)
        await self.ws.send(s)

    async def ws_received(self, received):
        msg = json.loads(received)
        self.queue_msg_parse.put(msg)
        msg_type = msg['type'] if 'type' in msg else ''
        # parse here only needed messages for ws working
        # don't slow read from socket
        if msg_type == 'welcome':
            pass
        elif msg_type == 'channels_list':
            self.log.info('channels_list answer ({} streams)'.format(len(msg['data']['channels'])))
            channels = set()
            for channel in msg['data']['channels']:
                channel_id = channel['channel_id']
                if channel_id not in self.joined_channels:
                    channels.add(str(channel_id))
            for channel_id in PREDEFINED_CHANNELS:
                if channel_id not in self.joined_channels:
                    channels.add(str(channel_id))
            for channel_id in channels:
                self.log.debug('founded new channel: {}'.format(channel_id))
                await self.join_channel(channel_id)

        elif msg_type == 'success_join':
            channel_id = str(msg['data']['channel_id'])
            self.joined_channels.add(channel_id)
            self.log.debug('joined new channel: {} (total {})'.format(channel_id, len(self.joined_channels)))
            query_fetch_history = {"type": "get_channel_history", "data": {"channel_id": str(channel_id), "from": 0}}
            await self.send(query_fetch_history)
