from ..core.types import OrderReq

class BasicRisk:
    def __init__(self, cfg: dict):
        self.cfg = cfg or {}
        self.max_notional = self.cfg.get("max_notional", 1e9)

    def pre_place(self, req: OrderReq) -> bool:
        # super basic: px * sz must be <= max_notional (skip if no px)
        notional = (req.px or 0.0) * req.sz
        return notional <= self.max_notional

    def on_fill(self, fill):  # hook for future accounting
        pass
