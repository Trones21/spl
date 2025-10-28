from typing import Iterable, Dict
from ..core.types import OrderReq, Quote, Trade, Fill, AccountSnapshot
from ..core.types import OrdType
from ..core.utils import fee_from_bps
from ..engine.fill_shadow import trade_crosses_limit
import time

class ShadowBackend:
    def __init__(self, store, fee_bps: float = 1.0):
        self.store = store
        self.fee_bps = fee_bps
        self._orders: Dict[str, OrderReq] = {}
        self._fills: list[Fill] = []

    def place(self, req: OrderReq) -> str:
        self._orders[req.client_id] = req
        self.store.write_event("place", req.__dict__)
        return req.client_id

    def cancel(self, client_order_id: str) -> bool:
        ok = self._orders.pop(client_order_id, None) is not None
        if ok: self.store.write_event("cancel", {"client_id": client_order_id})
        return ok

    def on_quote(self, q: Quote) -> Iterable[Fill]:
        return []  # shadow uses trades for filling

    def on_trade(self, t: Trade) -> Iterable[Fill]:
        fills = []
        for cid, o in list(self._orders.items()):
            if o.type == OrdType.LIMIT and o.px is not None and trade_crosses_limit(o.side, o.px, t.price):
                # simple full-fill model; you can extend to partials using t.size
                fee = fee_from_bps(t.price * o.sz, self.fee_bps)
                f = Fill(ts=t.ts, client_id=cid, symbol=o.symbol, side=o.side, px=t.price, sz=o.sz, fee=fee)
                fills.append(f)
                self._fills.append(f)
                self._orders.pop(cid, None)
        return fills

    def snapshot(self) -> AccountSnapshot:
        return AccountSnapshot(ts=int(time.time()*1000), balance=0.0, positions={})
