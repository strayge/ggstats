import asyncio
# import json
# import websockets
# from ggchat.management.commands._common import setup_logger
import json

from ggchat.management.commands._ws_base import WsBaseClient


WS_ENDPOINT = 'wss://chat.goodgame.ru/chat/websocket'

class ChatWsClientOld(WsBaseClient):
    def __init__(self, log_level, queue_old_cmd, queue_old_cmd_resp):
        self.queue_old_cmd = queue_old_cmd
        self.queue_old_cmd_resp = queue_old_cmd_resp

        self.joined_channels = set()

        super().__init__(log_level=log_level, endpoint=WS_ENDPOINT)

    async def ws_connected(self):
        self.joined_channels = set()

    async def ws_periodic_tasks(self):
        while not self.queue_old_cmd.empty():
            cmd = self.queue_old_cmd.get(block=False)
            cmd_type = cmd['type']
            if cmd_type == 'send':
                await self.send(cmd['data'])
            elif cmd_type == 'channels':
                for channel_id in cmd['data']:
                    if channel_id not in self.joined_channels:
                        await self.join_channel(channel_id)
            elif cmd_type == 'join':
                channel_id = cmd['data']
                if channel_id not in self.joined_channels:
                    await self.join_channel(channel_id)
            # await asyncio.sleep(0.2)  # workaroung for bug with ignoring too fast messages

    async def ws_received(self, received):
        msg = json.loads(received)
        msg_type = msg['type'] if 'type' in msg else ''

        # if msg_type not in ['welcome', 'success_join', 'channel_counters', 'channels_list', 'error', 'message']:
        #     import locale
        #     encoding = locale.getpreferredencoding()
        #     s = msg.__repr__().encode(encoding, 'ignore').decode(encoding)
        #     self.log.info('{}'.format(s))

        if msg_type == 'success_join':
            channel_id = str(msg['data']['channel_id'])
            self.joined_channels.add(channel_id)

        if msg_type in ['follower', 'channels_list']:
            self.queue_old_cmd_resp.put(received)

    async def send(self, data):
        s = json.dumps(data)
        if 'type' in data and data['type'] == 'get_channels_list':
            await asyncio.sleep(0.5)
        await self.ws.send(s)

    async def join_channel(self, channel_id):
        join_channel_query = {"type": "join", "data": {"channel_id": str(channel_id), "hidden": False}}
        await self.send(join_channel_query)
