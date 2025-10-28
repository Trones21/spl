# plugins/spl-adapter-drift/src/spl_adapter_drift/symbols.py
from dataclasses import dataclass
from driftpy.constants.config import configs

@dataclass
class Lots:
    base_precision: int  # e.g., 1e3 lots per 1 base
    price_precision: int # e.g., 1e6 quote units per 1

    def base(self, size_base: float) -> int:
        return int(round(size_base * self.base_precision))

    def price(self, px: float) -> int:
        return int(round(px * self.price_precision))

class SymbolMaps:
    def __init__(self, env: str):
        cfg = configs[env]
        self._perp = {m.symbol: m for m in cfg.perp_markets}
        # You can add spot if needed

    def index_of(self, symbol: str) -> int:
        return self._perp[symbol].market_index

    def lots(self, symbol: str) -> Lots:
        m = self._perp[symbol]
        # drift uses integer lot sizes; adjust if your version exposes fields differently
        return Lots(
            base_precision = int(m.base_asset_amount_step_size),  # or m.amm.base_asset_reserve_precision
            price_precision= int(1_000_000),                      # conservative default
        )
