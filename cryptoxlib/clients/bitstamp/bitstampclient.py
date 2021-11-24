import ssl
import logging
import hmac
import hashlib
import uuid
import json
from urllib.parse import urlencode

from multidict import CIMultiDictProxy
from typing import List, Optional

from cryptoxlib.CryptoXLibClient import CryptoXLibClient, RestCallType, ContentType
from cryptoxlib.Pair import Pair
from cryptoxlib.clients.bitstamp.bitstampwebsocket import BitstampWebsocket
from cryptoxlib.clients.bitstamp.enums import Group, Time, Step, Sort
from cryptoxlib.clients.bitstamp.exceptions import BitstampRestException, BitstampException, BitstampSignatureException
from cryptoxlib.clients.bitstamp.functions import map_pair
from cryptoxlib.WebsocketMgr import WebsocketMgr, Subscription

LOG = logging.getLogger(__name__)


class BitstampClient(CryptoXLibClient):
    """
    see: https://www.bitstamp.net/api/
    """
    PROTOCOL = "https://"
    HOST = "www.bitstamp.net"
    VERSION = "v2"
    PATH_PREFIX = "/api/" + VERSION + "/"
    REST_API_URI = PROTOCOL + HOST + PATH_PREFIX
    HOSTNAME = "BITSTAMP"

    def __init__(self,
                 api_key: str = None,
                 sec_key: bytes = None,
                 api_trace_log: bool = False,
                 ssl_context: ssl.SSLContext = None
                 ) -> None:
        super().__init__(api_trace_log, ssl_context)
        self.api_key = api_key
        self.sec_key = sec_key

    def _get_rest_api_uri(self) -> str:
        return self.REST_API_URI

    # data = post
    # params = get
    # resource = path
    def _sign_payload(self,
                      rest_call_type: RestCallType,
                      resource: str,
                      data: dict = None,
                      params: dict = None,
                      headers: dict = None,
                      signature_data: Optional[dict] = None
                      ) -> None:

        timestamp = str(self._get_current_timestamp_ms())
        nonce = str(uuid.uuid4())
        content_type = "" if data is None else "application/x-www-form-urlencoded"
        query = "" if params is None or params == {} else "?" + urlencode(params)
        payload = "" if data is None else urlencode(data)

        message = self.HOSTNAME + " " + self.api_key + \
                  rest_call_type.value + \
                  self.HOST + \
                  self.PATH_PREFIX + resource + \
                  query + \
                  content_type + \
                  nonce + \
                  timestamp + \
                  self.VERSION + \
                  payload

        message = message.encode("utf-8")
        signature = hmac.new(self.sec_key, msg=message, digestmod=hashlib.sha256).hexdigest()
        headers.update({
            "X-Auth": self.HOSTNAME + " " + self.api_key,
            "X-Auth-Signature": signature,
            "X-Auth-Nonce": nonce,
            "X-Auth-Timestamp": timestamp,
            "X-Auth-Version": self.VERSION,
            "Connection": "keep-alive"
        })
        if not content_type == "":
            headers["Content-Type"] = content_type

        signature_data.update({
            "nonce": nonce,
            "timestamp": timestamp
        })

    def _preprocess_rest_response(self,
                                  status_code: int,
                                  headers: 'CIMultiDictProxy[str]',
                                  body: Optional[dict],
                                  signature_data: Optional[dict] = None
                                  ) -> None:
        if str(status_code)[0] != '2':
            raise BitstampRestException(status_code, body)
        if signature_data["signed"]:
            string_to_sign = (signature_data["nonce"] + signature_data["timestamp"] + headers.get("Content-Type")).encode('utf-8') + json.dumps(body).encode("utf-8")
            signature_check = hmac.new(self.sec_key, msg=string_to_sign, digestmod=hashlib.sha256).hexdigest()
            if not headers.get("X-Server-Auth-Signature") == signature_check:
                raise BitstampSignatureException(status_code, body)

    def _get_websocket_mgr(self,
                           subscriptions: List[Subscription],
                           startup_delay_ms: int = 0,
                           ssl_context: ssl.SSLContext = None
                           ) -> WebsocketMgr:
        return BitstampWebsocket(subscriptions=subscriptions,
                                 client=self,
                                 account_id=None,
                                 ssl_context=ssl_context,
                                 startup_delay_ms=startup_delay_ms)

    # public api

    async def get_ticker(self, base: str, quote: str) -> dict:
        currency_pair = map_pair(Pair(base, quote))
        return await self._create_get(f"ticker/{currency_pair}/", signed=False)

    async def get_hourly_ticker(self, base: str, quote: str) -> dict:
        currency_pair = map_pair(Pair(base, quote))
        return await self._create_get(f"ticker_hour/{currency_pair}/", signed=False)

    async def get_order_book(self, base: str, quote: str, group: Group = None) -> dict:
        currency_pair = map_pair(Pair(base, quote))
        params = {"group": group.value} if group is not None else None
        return await self._create_get(f"order_book/{currency_pair}/", params=params, signed=False)

    async def get_transactions(self, base: str, quote: str, time: Time = None) -> dict:
        currency_pair = map_pair(Pair(base, quote))
        params = {"time": time.value} if time is not None else None
        return await self._create_get(f"transactions/{currency_pair}/", params=params, signed=False)

    async def get_trading_pairs_info(self) -> dict:
        return await self._create_get("trading-pairs-info/", signed=False)

    async def get_ohlc_data(self, base: str, quote: str, step: Step, limit: int, start: int = None, stop: int = None) -> dict:
        """
        :param base:
        :param quote:
        :param step: Timeframe in seconds. Possible options are 60, 180, 300, 900, 1800, 3600, 7200, 14400, 21600, 43200, 86400, 259200
        :param limit: Limit OHLC results (minimum: 1; maximum: 1000)
        :param start: Unix timestamp from when OHLC data will be started.
        :param stop: Unix timestamp to when OHLC data will be shown.
        :return: success - Returns a dictionary of tick data for selected trading pair. Each tick in the dictionary is represented as a list of OHLC data.
        """
        params = {"step": step.value, "limit": limit}
        if start is not None:
            params["start"] = start
        if stop is not None:
            params["stop"] = stop

        currency_pair = map_pair(Pair(base, quote))
        return await self._create_get(f"ohlc/{currency_pair}/", params=params, signed=False)

    async def get_eur_usd_conversion_rate(self) -> dict:
        return await self._create_get("eur_usd/", signed=False)

    # private api

    async def get_balances(self) -> dict:
        return await self._create_post("balance/", signed=True, content_type=ContentType.URL_ENCODED)

    async def get_balance(self, base: str, quote: str) -> dict:
        currency_pair = map_pair(Pair(base, quote))
        return await self._create_post(f"balance/{currency_pair}/", signed=True, content_type=ContentType.URL_ENCODED)

    async def get_user_transactions(self, offset: int, limit: int, sort: Sort, since_timestamp: int = None, since_id: int = None) -> dict:
        data = {
            "offset": str(offset),
            "limit": str(limit),
            "sort": sort.value
        }
        if since_timestamp is not None:
            data["since_timestamp"] = str(since_timestamp)
        if since_id is not None:
            data["since_id"] = str(since_id)

        return await self._create_post("user_transactions/", signed=True, content_type=ContentType.URL_ENCODED)

    async def get_user_transaction(self, base: str, quote: str, offset: int, limit: int, sort: Sort, since_timestamp: int = None, since_id: int = None) -> dict:

        data = {
            "offset": str(offset),
            "limit": str(limit),
            "sort": sort.value
        }
        if since_timestamp is not None:
            data["since_timestamp"] = str(since_timestamp)
        if since_id is not None:
            data["since_id"] = str(since_id)

        currency_pair = map_pair(Pair(base, quote))
        return await self._create_post(f"user_transactions/{currency_pair}/", data=data, signed=True, content_type=ContentType.URL_ENCODED)

    async def get_crypto_transactions(self, offset: int, limit: int, include_ious: bool = None) -> dict:

        data = {
            "offset": str(offset),
            "limit": str(limit)
        }
        if include_ious is not None:
            data["since_timestamp"] = str(include_ious)

        return await self._create_post(f"crypto-transactions/", data=data, signed=True, content_type=ContentType.URL_ENCODED)

    async def get_open_orders_all(self) -> dict:
        return await self._create_post("open_orders/all/", signed=True, content_type=ContentType.URL_ENCODED)

    async def get_open_orders(self, base: str, quote: str) -> dict:
        currency_pair = map_pair(Pair(base, quote))
        return await self._create_post(f"open_orders/{currency_pair}/", signed=True, content_type=ContentType.URL_ENCODED)

    async def get_order_status(self, id: int, client_order_id: str = None) -> dict:
        data = {"id": str(id)}
        if client_order_id is not None:
            data["client_order_id"] = client_order_id
        return await self._create_post("order_status/", data=data, signed=True, content_type=ContentType.URL_ENCODED)

    async def get_cancel_order(self, id: int) -> dict:
        data = {"id": str(id)}
        return await self._create_post("cancel_order/", data=data, signed=True, content_type=ContentType.URL_ENCODED)

    async def cancel_orders(self, base: str, quote: str) -> dict:
        currency_pair = map_pair(Pair(base, quote))
        return await self._create_post(f"cancel_all_orders/{currency_pair}/", signed=True, content_type=ContentType.URL_ENCODED)

    async def cancel_all_orders(self) -> dict:
        return await self._create_post(f"cancel_all_orders/", signed=True, content_type=ContentType.URL_ENCODED)

    async def buy_limit_order(self,
                              base: str,
                              quote: str,
                              amount: int,
                              price: int,
                              limit_price: int = None,
                              daily_order: bool = None,
                              ioc_order: bool = None,
                              fok_order: bool = None,
                              client_order_id: str = None
                              ) -> dict:
        """
        :param base:
        :param quote:
        :param amount: Amount
        :param price: Price
        :param limit_price: If the order gets executed, a new sell order will be placed, with "limit_price" as its price.
        :param daily_order: Opens buy limit order which will be canceled at 0:00 UTC unless it already has been executed. Possible value: True
        :param ioc_order: An Immediate-Or-Cancel (IOC) order is an order that must be executed immediately. Any portion of an IOC order that cannot be filled immediately will be cancelled. Possible value: True
        :param fok_order: A Fill-Or-Kill (FOK) order is an order that must be executed immediately in its entirety. If the order cannot be immediately executed in its entirety, it will be cancelled. Possible value: True
        :param client_order_id: Unique client order id set by client. Client order id needs to be unique string. Client order id value can only be used once.
        :return:
        """

        data = {
            "amount": str(amount),
            "price": str(price)
        }
        if limit_price is not None:
            data["limit_price"] = str(limit_price)
        if daily_order is not None:
            data["daily_order"] = str(daily_order)
        if ioc_order is not None:
            data["ioc_order"] = str(ioc_order)
        if fok_order is not None:
            data["fok_order"] = str(fok_order)
        if client_order_id is not None:
            data["client_order_id"] = str(client_order_id)

        currency_pair = map_pair(Pair(base, quote))
        return await self._create_post(f"buy/{currency_pair}/", data=data, signed=True, content_type=ContentType.URL_ENCODED)

    async def buy_market_order(self,
                              base: str,
                              quote: str,
                              amount: int
                              ) -> dict:
        """
        :param base:
        :param quote:
        :param amount: Amount in base currency (Example: For BTC/USD pair, amount is quoted in BTC)
        :return:
        """

        data = {
            "amount": str(amount)
        }
        currency_pair = map_pair(Pair(base, quote))
        return await self._create_post(f"buy/market/{currency_pair}/", data=data, signed=True, content_type=ContentType.URL_ENCODED)

    async def buy_instant_order(self,
                                base: str,
                                quote: str,
                                amount: int
                                ) -> dict:
        """
        :param base:
        :param quote:
        :param amount: Amount in counter currency (Example: For BTC/USD pair, amount is quoted in USD)
        :return:
        """

        data = { "amount": str(amount) }
        currency_pair = map_pair(Pair(base, quote))
        return await self._create_post(f"buy/instant/{currency_pair}/", data=data, signed=True,
                                       content_type=ContentType.URL_ENCODED)

    async def sell_limit_order(self,
                               base: str,
                               quote: str,
                               amount: int,
                               price: int,
                               limit_price: int = None,
                               daily_order: bool = None,
                               ioc_order: bool = None,
                               fok_order: bool = None,
                               client_order_id: str = None
                               ) -> dict:
        """
        :param base:
        :param quote:
        :param amount: Amount
        :param price: Price
        :param limit_price: If the order gets executed, a new sell order will be placed, with "limit_price" as its price.
        :param daily_order: Opens buy limit order which will be canceled at 0:00 UTC unless it already has been executed. Possible value: True
        :param ioc_order: An Immediate-Or-Cancel (IOC) order is an order that must be executed immediately. Any portion of an IOC order that cannot be filled immediately will be cancelled. Possible value: True
        :param fok_order: A Fill-Or-Kill (FOK) order is an order that must be executed immediately in its entirety. If the order cannot be immediately executed in its entirety, it will be cancelled. Possible value: True
        :param client_order_id: Unique client order id set by client. Client order id needs to be unique string. Client order id value can only be used once.
        :return:
        """

        data = {
            "amount": str(amount),
            "price": str(price)
        }
        if limit_price is not None:
            data["limit_price"] = str(limit_price)
        if daily_order is not None:
            data["daily_order"] = str(daily_order)
        if ioc_order is not None:
            data["ioc_order"] = str(ioc_order)
        if fok_order is not None:
            data["fok_order"] = str(fok_order)
        if client_order_id is not None:
            data["client_order_id"] = str(client_order_id)

        currency_pair = map_pair(Pair(base, quote))
        return await self._create_post(f"sell/{currency_pair}/", data=data, signed=True, content_type=ContentType.URL_ENCODED)

    async def sell_market_order(self,
                                base: str,
                                quote: str,
                                amount: int
                                ) -> dict:
        """
        :param base:
        :param quote:
        :param amount: Amount in base currency (Example: For BTC/USD pair, amount is quoted in BTC)
        :return:
        """

        data = { "amount": str(amount) }
        currency_pair = map_pair(Pair(base, quote))
        return await self._create_post(f"sell/market/{currency_pair}/", data=data, signed=True, content_type=ContentType.URL_ENCODED)

    async def sell_instant_order(self,
                                 base: str,
                                 quote: str,
                                 amount: int,
                                 amount_in_counter: bool = None,
                                 client_order_id: str = None
                                 ) -> dict:
        """
        :param base:
        :param quote:
        :param amount: Amount in base currency (Example: For BTC/USD pair, amount is quoted in BTC)x
        :param amount_in_counter: Instant sell orders allow you to sell an amount of the base currency determined by the value of it in the counter-currency. Amount_in_counter sets the amount parameter to refer to the counter currency instead of the base currency of the selected trading pair. Possible value: True
        :param client_order_id: Unique client order id set by client. Client order id needs to be unique string. Client order id value can only be used once.
        :return:
        """

        data = {"amount": str(amount)}
        if amount_in_counter is not None:
            data["amount_in_counter"] = amount_in_counter
        if client_order_id is not None:
            data["client_order_id"] = client_order_id
        currency_pair = map_pair(Pair(base, quote))
        return await self._create_post(f"sell/instant/{currency_pair}/", data=data, signed=True,
                                       content_type=ContentType.URL_ENCODED)

    async def withdrawal_request(self, timedelta: int = None) -> dict:
        data = None
        if timedelta is not None:
            data = { "timedelta": str(timedelta) }
        return await self._create_post("withdrawal-requests/", data=data, signed=True, content_type=ContentType.URL_ENCODED)

    async def coin_withdrawal(self,
                              instrument: str,
                              amount: int,
                              address: str,
                              memo_id: str = None,
                              destination_tag: str = None
                              ) -> dict:
        """
        :param instrument: coin to withdraw
        :param amount: coin amount
        :param address: coin address
        :param memo_id: Address memo id. Only for Stellar Lumens coin or Hedera Hashgraph coin.
        :param destination_tag: Address destination tag. Only for XRP coin.
        :return:
        """
        data = {"amount": amount, "address": address}
        if memo_id is not None:
            data["memo_id"] = memo_id
        if destination_tag is not None:
            data["destination_tag"] = destination_tag
        return await self._create_post(f"{instrument.lower()}_withdrawal/", data=data, signed=True, content_type=ContentType.URL_ENCODED)

    async def ripple_withdrawal(self,
                                amount: int,
                                address: str,
                                currency: str
                                ) -> dict:
        """
        :param amount: Currency amount.
        :param address: XRP address.
        :param currency: Currency.
        :return:
        """
        data = {"amount": amount, "address": address, "currency": currency}
        return await self._create_post("ripple_withdrawal/", data=data, signed=True, content_type=ContentType.URL_ENCODED)

    async def coin_deposit(self, instrument: str) -> dict:
        """
        Returns your instrument deposit address
        """
        return await self._create_post(f"{instrument.lower()}_address/", signed=True, content_type=ContentType.URL_ENCODED)

    async def ripple_deposit(self) -> dict:
        """
        Returns your ripple IOU deposit address
        """
        return await self._create_post("ripple_address/", signed=True, content_type=ContentType.URL_ENCODED)

    async def unconfirmed_btc_deposit(self) -> dict:
        """
        Returns list of unconfirmed bitcoin transactions.
        """
        return await self._create_post("btc_unconfirmed/", signed=True, content_type=ContentType.URL_ENCODED)

    async def transfer_sub_to_main(self,
                                   amount: int,
                                   currency: str,
                                   sub_account: str
                                   ) -> dict:
        """
        :param amount: Amount
        :param currency: Currency
        :param sub_account: The Sub Account unique identifier.
        :return:
        """
        data = {
            "amount": amount,
            "currency": currency,
            "subAccount": sub_account
        }
        return await self._create_post("transfer-to-main/", data=data, signed=True, content_type=ContentType.URL_ENCODED)

    async def transfer_main_to_sub(self,
                                   amount: int,
                                   currency: str,
                                   sub_account: str
                                   ) -> dict:
        """
        :param amount: Amount
        :param currency: Currency
        :param sub_account: The Sub Account unique identifier.
        :return:
        """
        data = {
            "amount": amount,
            "currency": currency,
            "subAccount": sub_account
        }
        return await self._create_post("transfer-from-main/", data=data, signed=True, content_type=ContentType.URL_ENCODED)

    # TODO: add more api calls

    async def get_websocket_token(self) -> dict:
        return await self._create_post("websockets_token/", signed=True, content_type=ContentType.URL_ENCODED)


if __name__ == "__main__":
    from cryptoxlib.CryptoXLib import CryptoXLib
    from cryptoxlib.version_conversions import async_run

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

    async_run(run())
