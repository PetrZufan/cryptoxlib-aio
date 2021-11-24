import asyncio
import logging

from cryptoxlib.CryptoXLib import CryptoXLib
from cryptoxlib.clients.bitstamp.bitstampwebsocket import BitstampTradesSubscription, BitstampOrdersSubscription
from cryptoxlib.version_conversions import async_run, async_create_task

LOG = logging.getLogger("cryptoxlib")
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.StreamHandler())

print(f"Available loggers: {[name for name in logging.root.manager.loggerDict]}\n")


async def callback(response: dict) -> None:
    print(f"{response}")


async def start(client):
    client.compose_subscriptions([
        BitstampTradesSubscription("LTC", "EUR", callbacks=[callback]),
        BitstampOrdersSubscription("LTC", "EUR", callbacks=[callback]),
    ])
    await client.start_websockets()


async def stop(client):
    await asyncio.sleep(60)
    await client.unsubscribe_all()
    await client.close()


async def run():
    api_key = "api key"
    sec_key = b"api secret key"
    client = CryptoXLib.create_bitstamp_client(api_key, sec_key)

    tasks = [
        async_create_task(start(client)),
        async_create_task(stop(client))
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    async_run(run())
