import time

import asyncio
import websockets

GG_CHAT_API2_ENDPOINT = 'ws://chat.goodgame.ru:8081/chat/websocket'
PERIODIC_PROCESSING_INTERVAL = 5 * 60


class WebsocketClient():
    def __init__(self):
        pass

    async def parse_received(self, ws, received):
        print(received)
        exit()

    async def periodic_processing(self, ws):
        pass

    async def run(self):
        while True:
            try:
                ws = await websockets.connect(GG_CHAT_API2_ENDPOINT)
                last_periodic_processing = time.time()
                while True:
                    if time.time() > last_periodic_processing + PERIODIC_PROCESSING_INTERVAL:
                        last_periodic_processing = time.time()
                        await self.periodic_processing(ws)
                    received = await ws.recv()
                    await self.parse_received(ws, received)
            except (KeyboardInterrupt, SystemExit):
                break
            except websockets.exceptions.ConnectionClosed:
                print(1)
                time.sleep(10)
            except websockets.exceptions.InvalidHandshake:
                print(2)
                time.sleep(10)
            except websockets.exceptions.WebSocketProtocolError:
                print(3)
                time.sleep(10)
            except websockets.exceptions.PayloadTooBig:
                print(4)
                time.sleep(10)
            except:
                print(5)
                import traceback
                print(traceback.format_exc())
                time.sleep(60)

    def start_forever(self):
        asyncio.get_event_loop().run_until_complete(self.run())
