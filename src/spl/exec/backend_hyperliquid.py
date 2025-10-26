# spl/exec/backend_hyperliquid.py
import time
from ..core.types import OrderReq, Fill  # whatever your types are

class HyperliquidExec:
    def __init__(self, cfg, store):
        """
        cfg['hyperliquid'] should include:
          network: "mainnet" | "testnet"
          account_address: "0x..."    # main wallet address
          secret_key: "..."           # API wallet private key (keep in env!)
        """
        from hyperliquid import Hyperliquid  # from official SDK or ccxt-hyperliquid
        self.cfg = cfg
        self.store = store
        self.hl = Hyperliquid({
            "network": cfg.get("network","mainnet"),
            "account_address": cfg["account_address"],
            "secret_key": cfg["secret_key"],
        })

    def place(self, req: OrderReq):
        # translate your OrderRequest -> HL order payload (price tick, size lot)
        # example (pseudo):
        side = "buy" if req.side == "buy" else "sell"
        res = self.hl.create_limit_order(req.symbol, "limit", side, req.sz, req.px)
        # store pending order id, etc.
        return res

    def on_quote(self, q):
        return []  # real matching happens on-chain; no synthetic fills for live

    def on_trade(self, t):
        # poll user fills via WS "userFills" or Info endpoint
        # return [Fill(...), ...] to keep Engine behavior consistent
        return []
