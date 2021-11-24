import logging

from cryptoxlib.CryptoXLib import CryptoXLib
from cryptoxlib.clients.bitstamp.enums import Group
from cryptoxlib.clients.bitstamp.exceptions import BitstampException
from cryptoxlib.version_conversions import async_run

LOG = logging.getLogger("cryptoxlib")
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.StreamHandler())

print(f"Available loggers: {[name for name in logging.root.manager.loggerDict]}")


async def run():
    api_key = "api key"
    sec_key = b"api secret key"
    client = CryptoXLib.create_bitstamp_client(api_key, sec_key)

    # public api
    print("order book:")
    try:
        response = await client.get_order_book("btc", "eur", Group.ZERO)
        print(response)
    except BitstampException as e:
        print(e)

    # private api
    print("Account balance:")
    try:
        response = await client.get_balances()
        print(response)
    except BitstampException as e:
        print(e)

    await client.close()


if __name__ == "__main__":
    async_run(run())
