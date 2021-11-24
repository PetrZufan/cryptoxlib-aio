import time
from typing import List

from cryptoxlib.Pair import Pair
from cryptoxlib.clients.bitstamp.enums import available_pairs


def map_pair(pair: Pair) -> str:
    return available_pairs[pair.base.lower()][pair.quote.lower()]


def map_multiple_pairs(pairs: List[Pair], sort: bool = False) -> List[str]:
    pairs = [map_pair(pair) for pair in pairs]

    if sort:
        return sorted(pairs)
    else:
        return pairs
