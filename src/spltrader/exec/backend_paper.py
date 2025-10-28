from typing import Iterable, Dict
from ..core.types import OrderReq, Quote, Fill, AccountSnapshot
from ..core.types import Side, OrdType
from ..core.utils import fee_from_bps
from ..engine.fill_paper import paper_px_for_market
import time

class PaperBackend:
    def __init__(self, store, fee_bps: float = 1.0, slippage_bps: float = 1.5):
        self.store = store
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps
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
        # market orders fill immediately against quote
        fills = []
        for cid, o in list(self._orders.items()):
            if o.type == OrdType.MARKET:
                px = paper_px_for_market(o.side, q, self.slippage_bps)
                fee = fee_from_bps(px * o.sz, self.fee_bps)
                f = Fill(ts=q.ts, client_id=cid, symbol=o.symbol, side=o.side, px=px, sz=o.sz, fee=fee)
                fills.append(f)
                self._fills.append(f)
                self._orders.pop(cid, None)
        return fills

    def on_trade(self, t) -> Iterable[Fill]:
        # paper backend ignores trades for filling
        return []

    def snapshot(self) -> AccountSnapshot:
        return AccountSnapshot(ts=int(time.time()*1000), balance=0.0, positions={})
