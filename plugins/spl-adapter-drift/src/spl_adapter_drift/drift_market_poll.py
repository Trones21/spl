# spl/markets/drift_market.py
import asyncio, time, queue
from dataclasses import dataclass
from typing import Iterable
from driftpy.drift_client import DriftClient
from driftpy.account_subscription_config import AccountSubscriptionConfig
from driftpy.constants.numeric_constants import PRICE_PRECISION
from driftpy.types import MarketType
from anchorpy.provider import Wallet
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey

from spl.core.types import Quote, Trade, Side

@dataclass(frozen=True)
class DriftMarket:
    """
    Drift Market adapter matching Engine expectations.
    Uses polling for quotes (no WebSocket subscription flood).
    """
    cfg: dict

    def __post_init__(self):
        key_path = self.cfg["wallet"]["keypair_path"]
        rpc_url = self.cfg["rpc"]["url"]
        sub_account_id = self.cfg.get("sub_account_id", 0)

        kp = Keypair.from_bytes(bytes(open(key_path, "rb").read()))
        wallet = Wallet(kp)
        conn = AsyncClient(rpc_url)

        self.dc = DriftClient(
            conn,
            wallet,
            "mainnet",
            account_subscription=AccountSubscriptionConfig("polling"),
            active_sub_account_id=sub_account_id,
        )

        # Use explicit event loop for async ops
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.dc.subscribe())
        print("[Drift] Subscribed via polling mode.")

    def subscribe_quotes(self, symbol: str) -> Iterable[Quote]:
        """Yield best bid/ask quotes periodically."""
        market_index = self._resolve_market_index(symbol)
        while True:
            px_data = self.dc.get_oracle_price_data_for_perp_market(market_index)
            if not px_data:
                time.sleep(1)
                continue
            px = px_data.price / PRICE_PRECISION
            ts = int(time.time() * 1000)
            q = Quote(ts=ts, bid=px * 0.999, ask=px * 1.001, bid_sz=1.0, ask_sz=1.0)
            yield q
            time.sleep(1.0)  # adjustable poll rate

    def subscribe_trades(self, symbol: str) -> Iterable[Trade]:
        """Mock trades from oracle movement."""
        for q in self.subscribe_quotes(symbol):
            side = Side.BUY if q.bid > q.ask * 0.999 else Side.SELL
            yield Trade(ts=q.ts, price=q.ask if side == Side.BUY else q.bid, size=0.01, side=side)

    def _resolve_market_index(self, symbol: str) -> int:
        # For now just 0=SOL-PERP, extend later
        return 0
