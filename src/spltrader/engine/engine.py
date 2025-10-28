from typing import Iterable
from ..core.types import Quote, Trade

class Engine:
    def __init__(self, market, exec_backend, store, risk):
        self.market = market
        self.exec_backend = exec_backend
        self.store = store
        self.risk = risk

    def run(self, symbol: str, strategy=None, observe=False):
        quotes = self.market.subscribe_quotes(symbol)
        trades = self.market.subscribe_trades(symbol)

        if observe:
            for q in quotes:
                print(f"{q.ts} | bid {q.bid:.4f} ask {q.ask:.4f}")
            return

        while True:
            q = next(quotes)
            print(f"[ENG] quote {symbol} {q.ts} {q.bid:.4f}/{q.ask:.4f}")

            fills = self.exec_backend.on_quote(q)
            for f in fills:
                print(f"[ENG] fill@quote id={f.client_id} side={f.side.value} px={f.px} sz={f.sz}")
                self.store.write_fill(f)
                self.risk.on_fill(f)

            reqs = list(strategy.on_event(q))
            if reqs:
                print(f"[ENG] strategy returned {len(reqs)} orders")
            for req in reqs:
                print(req)
                if self.risk.pre_place(req):
                    print(f"[ENG] place {req.client_id} {req.side.value} {req.type.value} sz={req.sz} px={req.px}")
                    self.exec_backend.place(req)
                else:
                    print(f"[ENG] blocked by risk: {req}")

            t = next(trades)
            # (optional) same style logging here
            fills = self.exec_backend.on_trade(t)
            for f in fills:
                print(f"[ENG] fill@trade id={f.client_id} side={f.side.value} px={f.px} sz={f.sz}")
                self.store.write_fill(f)
                self.risk.on_fill(f)

            reqs = list(strategy.on_event(t))
            for req in reqs:
                if self.risk.pre_place(req):
                    print(f"[ENG] place {req.client_id} {req.side.value} {req.type.value} sz={req.sz} px={req.px}")
                    self.exec_backend.place(req)
                else:
                    print(f"[ENG] blocked by risk: {req}")