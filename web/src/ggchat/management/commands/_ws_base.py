import asyncio
import json
import logging

import websockets

from ggchat.management.commands._common import setup_logger


class WsBaseClient:
    def __init__(self, endpoint, log_level=logging.INFO):
        self.log = setup_logger(log_level)
        self.endpoint = endpoint
        self.ws = None
        self.start_async()

    def start_async(self):
        try:
            asyncio.get_event_loop().run_until_complete(self.ws_loop())
        except (KeyboardInterrupt, SystemExit):
            self.log.info('KeyboardInterrupt')

    async def ws_loop(self):
        while True:
            try:
                self.log.info('ws connecting...')
                self.ws = await websockets.connect(self.endpoint)
                await self.ws_connected()
                while True:
                    await self.ws_periodic_tasks()
                    try:
                        msg = await asyncio.wait_for(self.ws.recv(), timeout=5)
                    except asyncio.TimeoutError:
                        try:
                            pong = await self.ws.ping()
                            await asyncio.wait_for(pong, timeout=10)
                        except asyncio.TimeoutError:
                            self.log.warning('ping timeout')
                            break
                        except:
                            self.log.exception('unknown error during ping')
                            break
                        self.log.debug('ping ok')
                        continue
                    await self.ws_received(msg)
            except (websockets.exceptions.ConnectionClosed,
                    websockets.exceptions.InvalidHandshake,
                    websockets.exceptions.WebSocketProtocolError,
                    websockets.exceptions.PayloadTooBig):
                self.log.error('WS error')
            except:
                self.log.exception('Unknown error')
            finally:
                if self.ws and not self.ws.closed:
                    await self.ws.close()
                    self.ws = None
                await asyncio.sleep(10)

    async def ws_connected(self):
        pass

    async def ws_periodic_tasks(self):
        pass

    async def ws_received(self, received):
        pass
