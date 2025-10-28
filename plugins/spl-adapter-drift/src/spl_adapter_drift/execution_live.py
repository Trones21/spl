# plugins/spl-adapter-drift/src/spl_adapter_drift/execution_live.py
from __future__ import annotations
import time, hashlib
from typing import Iterable, List
from spltrader.core.interfaces import IExecutionBackend  # your Protocol
from spltrader.core.types import Quote, Trade, OrderReq, Fill, AccountSnapshot, Side, OrdType

# Implements live execution backend matching IExecutionBackend
# Responsibilities:
# -Place/cancel real Drift orders.
# -Return account snapshot via DriftPy.
# -Translate OrderReq → DriftClient.place_perp_order(...).

def _u64_from_client_id(s: str) -> int:
    # Drift expects u64 for client_order_id. Hash string → 64-bit int.
    h = hashlib.blake2b(s.encode(), digest_size=8).digest()
    return int.from_bytes(h, "big", signed=False)

class DriftExecutionLive(IExecutionBackend):
    """
    Exchange-specific live executor for Drift that satisfies your IExecutionBackend.
    Assumes you pass in:
      - dc: driftpy.DriftClient (already subscribed)
      - index_of(symbol) -> market_index
      - lots(symbol).base(sz)->int, lots(symbol).price(px)->int
    """
    def __init__(self, dc, index_of, lots):
        self.dc = dc
        self.index_of = index_of
        self.lots = lots

    def place(self, req: OrderReq) -> str:
        idx = self.index_of(req.symbol)
        base_lots = self.lots(req.symbol).base(abs(req.sz))
        px_lots = None if (req.type == OrdType.MARKET or req.px is None) else self.lots(req.symbol).price(req.px)
        direction = "long" if req.side == Side.BUY else "short"

        client_order_id = _u64_from_client_id(req.client_id) if req.client_id else 0

        # TIF mapping (simple): GTC default; IOC if tif == "IOC"; post-only via meta flag
        order_type = None  # let SDK default; adjust if your driftpy exposes it
        immediate_or_cancel = (req.tif.upper() == "IOC")
        post_only = bool((req.meta or {}).get("post_only", False))
        reduce_only = bool((req.meta or {}).get("reduce_only", False))

        # NOTE: adapt parameter names to your driftpy version as needed.
        sig = self.dc._loop.run_until_complete(self.dc.place_perp_order(
            market_index=idx,
            base_asset_amount=base_lots,
            price=px_lots,
            direction=direction,
            reduce_only=reduce_only,
            client_order_id=client_order_id,
            immediate_or_cancel=immediate_or_cancel,
            post_only=post_only,
            # order_type=order_type,  # include only if your version supports it
        ))
        # Prefer returning your own client_id for deterministic cancel
        return req.client_id or str(client_order_id or sig)

    def cancel(self, client_order_id: str) -> bool:
        try:
            cid = _u64_from_client_id(client_order_id) if not client_order_id.isdigit() else int(client_order_id)
            self.dc._loop.run_until_complete(self.dc.cancel_order_by_user_id(cid))
            return True
        except Exception:
            return False

    def on_quote(self, q: Quote) -> Iterable[Fill]:
        # Live fills come from exchange/user events; quotes don't generate fills here.
        return []

    def on_trade(self, t: Trade) -> Iterable[Fill]:
        return []

    def snapshot(self) -> AccountSnapshot:
        u = self.dc._loop.run_until_complete(self.dc.get_user())
        # Map to your AccountSnapshot. Adjust scales to your driftpy version.
        ts = int(time.time() * 1000)
        balance = float(getattr(u, "total_collateral", 0)) / 1e6  # adjust if needed
        positions = {}  # fill in by iterating dc.get_user_positions() if you like
        return AccountSnapshot(ts=ts, balance=balance, positions=positions)
