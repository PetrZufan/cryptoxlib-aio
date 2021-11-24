import abc
import asyncio
import json
import logging
import ssl
from abc import ABC
from typing import List, Any

from cryptoxlib.Pair import Pair
from cryptoxlib.WebsocketMgr import Subscription, WebsocketMgr, WebsocketMessage, Websocket, CallbacksType
from cryptoxlib.clients.bitstamp.enums import Event, Status
from cryptoxlib.clients.bitstamp.exceptions import BitstampException
from cryptoxlib.clients.bitstamp.functions import map_pair
from cryptoxlib.version_conversions import async_create_task

LOG = logging.getLogger(__name__)


class BitstampWebsocket(WebsocketMgr):
    """
    see: https://www.bitstamp.net/websocket/v2/
    """
    WEBSOCKET_URI = "wss://ws.bitstamp.net"
    MAX_MESSAGE_SIZE = 3 * 1024 * 1024  # 3MB

    def __init__(self,
                 subscriptions: List[Subscription],
                 client,
                 account_id: str = None,
                 ssl_context: ssl.SSLContext = None,
                 startup_delay_ms: int = 0
                 ) -> None:
        super().__init__(websocket_uri=self.WEBSOCKET_URI,
                         subscriptions=subscriptions,
                         ssl_context=ssl_context,
                         builtin_ping_interval=None,
                         auto_reconnect=True,
                         max_message_size=self.MAX_MESSAGE_SIZE,
                         periodic_timeout_sec=30,
                         startup_delay_ms=startup_delay_ms)

        self.client = client
        self.account_id = account_id

    def get_websocket(self) -> Websocket:
        return self.get_aiohttp_websocket()

    @staticmethod
    def get_subscription_messages(subscriptions: List[Subscription]):
        return [
            {
                "event": Event.SUBSCRIBE.value,
                "data": subscription.get_subscription_message()
            }
            for subscription in subscriptions
        ]

    @staticmethod
    def get_unsubscription_messages(subscriptions: List[Subscription]):
        return [
            {
                "event": Event.UNSUBSCRIBE.value,
                "data": subscription.get_unsubscription_message()
            }
            for subscription in subscriptions
        ]

    async def send_subscription_message(self, subscriptions: List[Subscription]):
        messages = self.get_subscription_messages(subscriptions)
        LOG.debug(f"> {messages}")
        tasks = [async_create_task(self.websocket.send(json.dumps(message))) for message in messages]
        await asyncio.gather(*tasks)

    async def send_unsubscription_message(self, subscriptions: List[Subscription]):
        messages = self.get_unsubscription_messages(subscriptions)
        LOG.debug(f"> {messages}")
        tasks = [async_create_task(self.websocket.send(json.dumps(message))) for message in messages]
        await asyncio.gather(*tasks)

    async def _process_message(self, websocket: Websocket, message: str) -> None:
        response = json.loads(message)

        if response["event"] == Event.ERROR.value:
            LOG.error(f"Subscription error. Response [{response}]")
            raise BitstampException(f"Subscription error. Response [{response}]")

        elif response["event"] == Event.SUBSCRIPTION_SUCCEED.value:
            LOG.info(f"Subscription succeeded. Response: [{response}]")

        elif response["event"] == Event.UNSUBSCRIPTION_SUCCEED.value:
            LOG.info(f"Unsubscription succeeded. Response: [{response}]")

        elif response["event"] == Event.HEARTBEAT.value:
            if response["data"]["status"] == Status.SUCCESS.value:
                LOG.info(f"Successful heartbeat. Response[{response}]")
            else:
                LOG.error(f"Unsuccessful heartbeat. Response[{response}]")

        elif response["event"] == Event.REQUEST_RECONNECT.value:
            await self.reconnect()
            LOG.info(f"Successful reconnect'. Response[{response}]")

        else:
            LOG.info(f"Response: [{response}]")
            await self.publish_message(
                WebsocketMessage(
                    subscription_id=response["channel"],
                    message=response
                )
            )

    async def send_heartbeat_message(self):
        message = {"event": Event.HEARTBEAT.value}
        await self.websocket.send(json.dumps(message))

    async def _process_periodic(self, websocket: Websocket) -> None:
        await self.send_heartbeat_message()


class BitstampSubscription(Subscription, ABC):
    def __init__(self, base: str, quote: str, callbacks: CallbacksType = None):
        super().__init__(callbacks)
        self.base: str = base
        self.quote: str = quote
        self.pair_str: str = map_pair(Pair(base, quote))

    def construct_subscription_id(self) -> Any:
        return self.get_unsubscription_message()["channel"]

    @abc.abstractmethod
    def get_subscription_message(self, **kwargs) -> dict:
        pass

    @abc.abstractmethod
    def get_unsubscription_message(self, **kwargs) -> dict:
        pass


class BitstampTradesSubscription(BitstampSubscription):
    def get_subscription_message(self, **kwargs) -> dict:
        return {"channel": f"live_trades_{self.pair_str}"}

    def get_unsubscription_message(self, **kwargs) -> dict:
        return {"channel": f"live_trades_{self.pair_str}"}


class BitstampOrdersSubscription(BitstampSubscription):
    def get_subscription_message(self, **kwargs) -> dict:
        return {"channel": f"live_orders_{self.pair_str}"}

    def get_unsubscription_message(self, **kwargs) -> dict:
        return {"channel": f"live_orders_{self.pair_str}"}


class BitstampOrderBookSubscription(BitstampSubscription):
    def get_subscription_message(self, **kwargs) -> dict:
        return {"channel": f"order_book_{self.pair_str}"}

    def get_unsubscription_message(self, **kwargs) -> dict:
        return {"channel": f"order_book_{self.pair_str}"}


class BitstampDetailOrderBookSubscription(BitstampSubscription):
    def get_subscription_message(self, **kwargs) -> dict:
        return {"channel": f"detail_order_book_{self.pair_str}"}

    def get_unsubscription_message(self, **kwargs) -> dict:
        return {"channel": f"detail_order_book_{self.pair_str}"}


class BitstampFullOrderBookSubscription(BitstampSubscription):
    def get_subscription_message(self, **kwargs) -> dict:
        return {"channel": f"diff_order_book_{self.pair_str}"}

    def get_unsubscription_message(self, **kwargs) -> dict:
        return {"channel": f"diff_order_book_{self.pair_str}"}


class BitstampPrivateOrdersSubscription(BitstampSubscription):
    def __init__(self, base: str, quote: str, user_id: str, token: str, callbacks: CallbacksType = None):
        super().__init__(base, quote, callbacks)
        self.user_id = user_id
        self.token = token

    def get_subscription_message(self, **kwargs) -> dict:
        return {
            "channel": f"private-my_orders_{self.pair_str}-{self.user_id}",
            "auth": f"{self.token}"
        }

    def get_unsubscription_message(self, **kwargs) -> dict:
        return {"channel": f"private-my_orders_{self.pair_str}"}


class BitstampPrivateTradesSubscription(BitstampSubscription):
    def __init__(self, base: str, quote: str, user_id: str, token: str, callbacks: CallbacksType = None):
        super().__init__(base, quote, callbacks)
        self.user_id = user_id
        self.token = token

    def get_subscription_message(self, **kwargs) -> dict:
        return {
            "channel": f"private-my_trades_{self.pair_str}-{self.user_id}",
            "auth": f"{self.token}"
        }

    def get_unsubscription_message(self, **kwargs) -> dict:
        return {"channel": f"private-my_trades_{self.pair_str}"}
