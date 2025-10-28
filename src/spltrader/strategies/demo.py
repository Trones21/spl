import time
from ..core.types import OrderReq, OrdType, Side

class RangeBounce:
    """
    Very simple demo strategy:
    - If price > range_high: place a short limit just below it.
    - If price < range_low: place a long limit just above it.
    This is intentionally naive; replace with your real signal logic.
    """
    def __init__(self, cfg):
        s = cfg.get("strategy", {})
        self.range_low = float(s.get("range_low", 99.5))
        self.range_high = float(s.get("range_high", 100.5))
        self.size = float(s.get("size", 1.0))
        self.symbol = cfg.get("symbol", "SOL-PERP")

    def on_event(self, event):

        # Works with Quote or Trade (both have price info one way or another)
        price = getattr(event, "price", None)
        if price is None:
            # if Quote, derive mid
            if hasattr(event, "bid") and hasattr(event, "ask"):
                price = (event.bid + event.ask) / 2.0
            else:
                return []

        orders = []
        ts = int(time.time()*1000)

        if price >= self.range_high:
            orders.append(OrderReq(
                client_id=f"short-{ts}",
                symbol=self.symbol,
                side=Side.SELL,
                type=OrdType.LIMIT,
                px=self.range_high - 0.01,
                sz=self.size,
            ))
        elif price <= self.range_low:
            orders.append(OrderReq(
                client_id=f"long-{ts}",
                symbol=self.symbol,
                side=Side.BUY,
                type=OrdType.LIMIT,
                px=self.range_low + 0.01,
                sz=self.size,
            ))

        return orders
