import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient

from client import Client


async def main():
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    mongo = AsyncIOMotorClient('mongo', 27017)
    client = Client(mongo=mongo)
    await client.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
