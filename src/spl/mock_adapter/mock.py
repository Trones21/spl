import time, math, random
from typing import Iterable
from ..core.types import Quote, Trade, Side

class MockMarket:
    """
    Emits a synthetic mean-reverting price around 100 with small noise.
    Useful for booting the engine end-to-end without external deps.
    """
    def __init__(self, cfg):
        self.cfg = cfg
        self._p = 100.0

    def subscribe_quotes(self, symbol: str) -> Iterable[Quote]:
        while True:
            # small random walk around mid; generate tight spread
            self._p += math.sin(time.time()/3.0)*0.005 + random.uniform(-0.01, 0.01)
            bid = round(self._p - 0.01, 4)
            ask = round(self._p + 0.01, 4)
            yield Quote(ts=int(time.time()*1000), bid=bid, ask=ask, bid_sz=5.0, ask_sz=5.0)
            time.sleep(1)

    def subscribe_trades(self, symbol: str) -> Iterable[Trade]:
        while True:
            px = round(self._p + random.uniform(-0.02, 0.02), 4)
            side = Side.BUY if random.random() > 0.5 else Side.SELL
            yield Trade(ts=int(time.time()*1000), price=px, size=0.5, side=side)
            time.sleep(0.08)

    def get_mark_price(self, symbol: str) -> float:
        return self._p

    def get_funding(self, symbol: str) -> float:
        return 0.0
