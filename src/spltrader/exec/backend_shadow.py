# spl/exec/backend_shadow.py
import time
from typing import Iterable, Dict
from ..core.interfaces import IExecutionBackend
from ..core.types import Quote, Trade, OrderReq, Fill, AccountSnapshot, Side, OrdType

class ShadowBackend(IExecutionBackend):
    def __init__(self, fee_bps: float = 0.0):
        self.fee = fee_bps / 10_000.0
        self.resting: Dict[str, OrderReq] = {}   # orders we “would” have sent
        self.positions: Dict[str, Dict[str, float]] = {}
        self.cash = 0.0

    def place(self, req: OrderReq) -> str:
        # store intent; do not send
        self.resting[req.client_id] = req
        return req.client_id

    def cancel(self, client_order_id: str) -> bool:
        return self.resting.pop(client_order_id, None) is not None

    def on_quote(self, q: Quote) -> Iterable[Fill]:
        # shadow doesn’t fill from quotes
        return []

    def on_trade(self, t: Trade) -> Iterable[Fill]:
        fills = []
        for cid, req in list(self.resting.items()):
            if req.symbol != req.symbol:
                continue
            # MARKET orders: treat first trade after placement as fill
            if req.type == OrdType.MARKET:
                px = t.price
                fee = abs(req.sz) * px * self.fee
                base = req.sz if req.side == Side.BUY else -req.sz
                pos = self.positions.setdefault(req.symbol, {"base": 0.0, "pnl_real": 0.0})
                pos["pnl_real"] -= base * px
                pos["base"] += base
                self.cash -= fee
                fills.append(Fill(ts=t.ts, client_id=cid, symbol=req.symbol, side=req.side, px=px, sz=req.sz, fee=fee))
                self.resting.pop(cid)
            # LIMIT: fill if trade price crosses our limit in the right direction
            elif req.type == OrdType.LIMIT and req.px is not None:
                if (req.side == Side.BUY and t.price <= req.px) or (req.side == Side.SELL and t.price >= req.px):
                    px = t.price
                    fee = abs(req.sz) * px * self.fee
                    base = req.sz if req.side == Side.BUY else -req.sz
                    pos = self.positions.setdefault(req.symbol, {"base": 0.0, "pnl_real": 0.0})
                    pos["pnl_real"] -= base * px
                    pos["base"] += base
                    self.cash -= fee
                    fills.append(Fill(ts=t.ts, client_id=cid, symbol=req.symbol, side=req.side, px=px, sz=req.sz, fee=fee))
                    self.resting.pop(cid)
        return fills

    def snapshot(self) -> AccountSnapshot:
        ts = int(time.time()*1000)
        return AccountSnapshot(ts=ts, balance=self.cash, positions=self.positions)
