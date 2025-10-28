import time
from ..core.types import OrderReq, OrdType, Side

class DemoMarketTick:
    def __init__(self, cfg):
        self.last_ts = 0
        self.cooldown_ms = int(cfg.get("cooldown_ms", 3000))
        self.qty = float(cfg.get("qty", 0.01))
        self.symbol = cfg.get("symbol", "SOL-PERP")

    def on_event(self, evt):
        # Fire only on quotes and only every cooldown interval
        if not hasattr(evt, "bid"):  # skip trades
            return []
        now = evt.ts
        if now - self.last_ts < self.cooldown_ms:
            return []
        self.last_ts = now

        mid = (evt.bid + evt.ask) / 2
        client_id = f"demo-{now}"

        print(
            f"[STRAT] firing market BUY {self.qty} {self.symbol} "
            f"at mid={mid:.4f} (bid={evt.bid:.4f} ask={evt.ask:.4f})"
        )

        return [
            OrderReq(
                client_id=client_id,
                symbol=self.symbol,
                side=Side.BUY,
                type=OrdType.MARKET,
                px=None,  # fine for market orders
                sz=self.qty,
            )
        ]
