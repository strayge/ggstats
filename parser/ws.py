import asyncio
import json
import time

from websockets.legacy.client import Connect, WebSocketClientProtocol


class WsClient:
    def __init__(
        self,
        url: str = 'wss://chat-1.goodgame.ru/chat2/',
        period: int = 5 * 60,
        send_interval: float = 0.15,
    ):
        self.url = url
        self.ws: WebSocketClientProtocol = None
        self._period = period
        self._last_periodic: float = 0
        self._send_queue = asyncio.Queue()
        self._send_interval = send_interval
        self._last_send: float = 0

    async def run(self):
        try:
            async with Connect(self.url) as ws:
                self.ws = ws
                self._last_periodic = time.monotonic()
                await self.on_start()
                while True:
                    if time.monotonic() - self._last_periodic > self._period:
                        self._last_periodic = time.monotonic()
                        await self.on_periodic()
                    if msg := await self.recv():
                        await self.on_msg(msg)
                    if time.monotonic() - self._last_send > self._send_interval:
                        if not self._send_queue.empty():
                            self._last_send = time.monotonic()
                            await self._send(self._send_queue.get_nowait())
        except Exception as e:
            raise e

    async def send(self, msg: dict):
        await self._send_queue.put(msg)

    async def _send(self, msg: dict):
        await self.on_send(msg)
        await self.ws.send(json.dumps(msg))

    async def recv(self) -> dict | None:
        try:
            msg = await asyncio.wait_for(self.ws.recv(), timeout=0.1)
            return json.loads(msg)
        except asyncio.TimeoutError:
            return None

    async def on_start(self):
        pass

    async def on_msg(self, msg: dict):
        pass

    async def on_send(self, msg: dict):
        pass

    async def on_periodic(self):
        pass
