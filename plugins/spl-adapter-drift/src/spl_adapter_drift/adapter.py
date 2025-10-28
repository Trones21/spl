# plugins/spl-adapter-drift/src/spl_adapter_drift/adapter.py
from driftpy.drift_client import DriftClient
from driftpy.accounts import AccountSubscriptionConfig
from solana.rpc.async_api import AsyncClient
from anchorpy import Wallet
from solders.keypair import Keypair
from driftpy.constants.config import configs

from .execution_live import DriftExecutionLive

# Central entry point used by CLI resolver

# Responsibilities:
# - Read config (wallet, rpc, network).
# - Instantiate AsyncClient, Wallet, DriftClient.
# - Subscribe the client (once).
# - Create and store a SymbolMaps helper.
# - Expose factory methods:
#     - execution_live() → returns DriftExecutionLive
#     - market_data() → returns DriftMarketData

class SymbolMaps:
    def __init__(self, env: str):
        cfg = configs[env]
        self._perp = {m.symbol: m for m in cfg.perp_markets}

    def index_of(self, symbol: str) -> int:
        return self._perp[symbol].market_index

    class _Lots:
        def __init__(self, base_prec: int, price_prec: int):
            self.base_precision = base_prec
            self.price_precision = price_prec
        def base(self, sz: float) -> int:
            return int(round(sz * self.base_precision))
        def price(self, px: float) -> int:
            return int(round(px * self.price_precision))

    def lots(self, symbol: str) -> "_Lots":
        m = self._perp[symbol]
        # Adjust these to your driftpy version’s fields
        base_prec  = int(getattr(m, "base_asset_amount_step_size", 1000))
        price_prec = int(1_000_000)
        return self._Lots(base_prec, price_prec)

class DriftAdapter:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        env = cfg.get("network", "mainnet")
        self.syms = SymbolMaps(env)

        http = cfg["rpc"]["url"]
        ws   = cfg["rpc"].get("ws")
        commitment = cfg.get("commitment", "confirmed")

        kp = Keypair.from_bytes(open(cfg["wallet"]["keypair_path"], "rb").read())
        wallet = Wallet(kp)
        conn = AsyncClient(http, ws_url=ws, commitment=commitment)

        sub = AccountSubscriptionConfig(type="websocket", commitment=commitment)

        self.dc = DriftClient(conn, wallet=wallet, env=env, account_subscription=sub)
        # subscribe up-front
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.dc.subscribe())

    # ---- expose live execution that satisfies your IExecutionBackend
    def execution_live(self):
        return DriftExecutionLive(self.dc, self.syms.index_of, self.syms.lots)

    # (optional) expose a market-data impl matching your IMarketData later

