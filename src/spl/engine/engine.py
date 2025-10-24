from typing import Iterable
from ..core.types import Quote, Trade

class Engine:
    def __init__(self, market, exec_backend, store, risk):
        self.m = market
        self.x = exec_backend
        self.s = store
        self.r = risk

    def run(self, symbol: str, strategy):
        # naive interleaving loop for demo; replace with asyncio later
        quotes = self.m.subscribe_quotes(symbol)
        trades = self.m.subscribe_trades(symbol)

        while True:
            q = next(quotes)
            fills = self.x.on_quote(q)
            for f in fills: self.s.write_fill(f); self.r.on_fill(f)
            for req in strategy.on_event(q):
                if self.r.pre_place(req): self.x.place(req)

            t = next(trades)
            fills = self.x.on_trade(t)
            for f in fills: self.s.write_fill(f); self.r.on_fill(f)
            for req in strategy.on_event(t):
                if self.r.pre_place(req): self.x.place(req)
