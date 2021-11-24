import enum


class Group(enum.Enum):
    ZERO = 0
    ONE = 1
    TWO = 2
    DEFAULT = 1


class Time(enum.Enum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    DEFAULT = "hour"


class Step(enum.Enum):
    MINUTE = 60
    THREE_MINUTES = 180
    FIVE_MINUTES = 300
    FIFTEEN_MINUTES = 900
    THIRTY_MINUTES = 1800
    HOUR = 3600
    TWO_HOURS = 7200
    FOUR_HOURS = 14400
    SIX_HOURS = 21600
    TWELVE_HOURS = 43200
    DAY = 86400
    THREE_DAYS = 259200


class Sort(enum.Enum):
    ASC = "asc"
    DESC = "desc"
    DEFAULT = "desc"


class Event(enum.Enum):
    SUBSCRIBE = "bts:subscribe"
    UNSUBSCRIBE = "bts:unsubscribe"
    SUBSCRIPTION_SUCCEED = "bts:subscription_succeeded"
    UNSUBSCRIPTION_SUCCEED = "bts:unsubscription_succeeded"
    HEARTBEAT = "bts:heartbeat"
    REQUEST_RECONNECT = "bts:request_reconnect"
    ERROR = "bts:error"


class Status(enum.Enum):
    SUCCESS = "success"


available_fiats = {"eur", "usd"}
available_cryptos = {"btc", "eth", "ltc", "xrp", "gbp", "pax", "usdt", "usdc", "uni"}
available_pairs = {"eur": {"btc": "btceur", "eth": "etheur", "ltc": "ltceur", "usd": "eurusd", "xrp": "xrpeur",
                           "gbp": "gbpeur", "uni": "unieur"},
                   "usd": {"btc": "btcusd", "eth": "ethusd", "eur": "eurusd", "ltc": "ltcusd", "xrp": "xrpusd",
                           "gbp": "gbpusd", "uni": "uniusd"},
                   "btc": {"eur": "btceur", "usd": "btcusd", "eth": "ethbtc", "ltc": "ltcbtc", "xrp": "xrpbtc",
                           "gbp": "btcgbp", "pax": "btcpax", "usdt": "btcusdt", "usdc": "btcusdc", "uni": "unibtc"},
                   "eth": {"eur": "etheur", "usd": "ethusd", "btc": "ethbtc", "gbp": "ethgbp", "pax": "ethpax",
                           "usdt": "ethusdt", "usdc": "ethusdc"},
                   "xrp": {"eur": "xrpeur", "usd": "xrpusd", "btc": "xrpbtc", "gbp": "xrpgbp", "pax": "xrppax",
                           "usdt": "xrpusdt"},
                   "ltc": {"eur": "ltceur", "usd": "ltcusd", "btc": "ltcbtc", "gbp": "ltcgbp"},
                   "gbp": {"eur": "gbpeur", "usd": "gbpusd", "btc": "btcgbp", "eth": "ethgbp", "xrp": "xrpgbp",
                           "ltc": "ltcgbp"},
                   "pax": {"btc": "btcpax", "eth": "ethpax", "xrp": "xrppax"},
                   "usdt": {"btc": "btcusdt", "eth": "ethusdt", "xrp": "xrpusdt"},
                   "usdc": {"btc": "btcusdc", "eth": "ethusdtc"},
                   "uni": {"eur": "unieur", "usd": "uniusd", "btc": "unibtc"}
                   }

# btcusd, btceur, btcgbp, btcpax, btcusdt, btcusdc, \
# gbpusd, gbpeur,\
# eurusd, \
# ethusd, etheur, ethbtc, ethgbp, ethpax, ethusdt, ethusdc, \
# xrpusd, xrpeur, xrpbtc, xrpgbp, xrppax, xrpusdt, \
# uniusd, unieur, unibtc, \
# ltcusd, ltceur, ltcbtc, ltcgbp, \
# TODO: add more pairs (followings)
# linkusd, linkeur, linkbtc, linkgbp, linketh, \
# maticusd, maticeur,\
# xlmusd, xlmeur, xlmbtc, xlmgbp,
# fttusd, ftteur,
# bchusd, bcheur, bchbtc, bchgbp,
# aaveusd, aaveeur, aavebtc,
# axsusd, axseur,
# algousd, algoeur, algobtc,
# compusd, compeur, compbtc,
# snxusd, snxeur, snxbtc,
# hbarusd, hbareur,
# chzusd, chzeur,
# celusd, celeur,
# enjusd, enjeur,
# batusd, bateur, batbtc,
# mkrusd, mkreur, mkrbtc,
# zrxusd, zrxeur, zrxbtc,
# audiousd, audioeur, audiobtc,
# sklusd, skleur,
# yfiusd, yfieur, yfibtc,
# sushiusd, sushieur,
# alphausd, alphaeur,
# storjusd, storjeur,
# sxpusd, sxpeur,
# grtusd, grteur,
# umausd, umaeur, umabtc,
# omgusd, omgeur, omgbtc, omggbp,
# kncusd, knceur, kncbtc,
# crvusd, crveur, crvbtc,
# sandusd, sandeur,
# fetusd, feteur,
# rgtusd, rgteur,
# eurtusd, eurteur,
# usdtusd, usdteur,
# usdcusd, usdceur, usdcusdt,
# daiusd,
# paxusd, paxeur, paxgbp,
# eth2eth, gusdusd
