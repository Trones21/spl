# Implements IMarketData

# Responsibilities:
# Poll or stream Drift oracle/AMM prices.
# Yield Quote and Trade objects in your core format.
# Use AsyncBridge for async Drift calls.

# plugins/spl-adapter-drift/src/spl_adapter_drift/market_data.py
from __future__ import annotations

import time
from typing import Iterable, Generator, Optional

from spltrader.core.interfaces import IMarketData
from spltrader.core.types import Quote, Trade

# Local imports from this adapter package
from .client import DriftHandle
from .symbols import SymbolMaps


class DriftMarketData(IMarketData):
    """
    Drift-backed market data provider that satisfies your IMarketData Protocol.

    - subscribe_quotes(symbol): yields Quote(ts,bid,ask,bid_sz,ask_sz) by polling a mark/oracle price.
      * We set bid=ask=mark (or oracle) and sizes to 0.0 (you can wire orderbook later).
    - subscribe_trades(symbol): placeholder generator (no trade tape yet).
    - get_mark_price(symbol): best-effort mark/oracle read.
    - get_funding(symbol): best-effort funding metric (instantaneous or twap) if available.

    Notes:
    * This implementation prefers websocket account subscription for freshness (configured in client.py).
    * To avoid version pin issues, price/funding readers try multiple field names.
    """

    def __init__(self, handle: DriftHandle, symbols: SymbolMaps, poll_sec: float = 0.5):
        self.h = handle           # DriftHandle with .dc (DriftClient) and async bridge
        self.syms = symbols       # SymbolMaps with index_of(...)
        self.poll_sec = float(poll_sec)

    # -------------------------
    # Public API (IMarketData)
    # -------------------------

    def subscribe_quotes(self, symbol: str) -> Iterable[Quote]:
        """
        Simple polling generator. Emits a Quote whenever the price changes
        (bid=ask=mark/oracle; sizes are 0.0 as we aren't wiring orderbook yet).
        """
        idx = self.syms.index_of(symbol)

        def gen() -> Generator[Quote, None, None]:
            last_px: Optional[float] = None
            while True:
                px = self._read_mark_or_oracle(idx)
                # Only emit on change (reduces spam)
                if px is not None and px != last_px:
                    ts = int(time.time() * 1000)
                    yield Quote(ts=ts, bid=px, ask=px, bid_sz=0.0, ask_sz=0.0)
                    last_px = px
                time.sleep(self.poll_sec)

        return gen()

    def subscribe_trades(self, symbol: str) -> Iterable[Trade]:
        """
        Placeholder: drift trades via logs/user events can be wired later.
        Returns an empty generator for now.
        """
        def _empty():
            if False:
                yield  # pragma: no cover
        return _empty()

    def get_mark_price(self, symbol: str) -> float:
        idx = self.syms.index_of(symbol)
        px = self._read_mark_or_oracle(idx)
        if px is None:
            raise RuntimeError(f"Unable to read mark/oracle price for {symbol} (index={idx})")
        return px

    def get_funding(self, symbol: str) -> float:
        """
        Best-effort funding. Depending on DriftPy/program version, different fields may exist.
        Returns a *per-period* rate (not annualized). You can scale as needed.
        """
        idx = self.syms.index_of(symbol)
        mkt = self.h.bridge.run(self.h.dc.get_perp_market_account(idx))

        # Try several likely locations/field names across versions
        # 1) Direct field on market (e.g., 'last_funding_rate' or 'last_funding_rate_8h')
        for name in (
            "last_funding_rate",
            "last_funding_rate_8h",
            "last_funding_rate_per_hour",
            "estimated_funding_rate",
        ):
            v = getattr(mkt, name, None)
            if v is not None:
                try:
                    return float(v)
                except Exception:
                    pass

        # 2) Funding on amm sub-struct (some versions keep rollups there)
        amm = getattr(mkt, "amm", None)
        if amm is not None:
            for name in (
                "last_funding_rate",
                "last_funding_rate_8h",
                "funding_period",
                "funding_last_measured",
            ):
                v = getattr(amm, name, None)
                if isinstance(v, (int, float)):
                    try:
                        return float(v)
                    except Exception:
                        pass

        # 3) Fallback: zero if we can't read it
        return 0.0

    # -------------------------
    # Internals
    # -------------------------

    def _read_mark_or_oracle(self, market_index: int) -> Optional[float]:
        """
        Attempts to read a sensible 'mark' price for the perp market.
        Strategy (robust to DriftPy version variance):
          1) Try an explicit oracle price accessor if present.
          2) Try market's cached/mark price fields.
          3) As a last resort, read oracle price data for the market and scale.
        Returns None if all attempts fail.
        """
        # 1) Try a convenient SDK helper if available
        try:
            # Some versions expose this helper:
            pd = self.h.bridge.run(self.h.dc.get_oracle_price_data_for_perp_market(market_index))
            # Commonly Pyth prices are 1e6 scaled
            if hasattr(pd, "price"):
                return float(pd.price) / 1_000_000.0
        except AttributeError:
            # Helper not available — continue to next attempt
            pass
        except Exception:
            # Accessor failed — continue
            pass

        # 2) Read market account and look for a cached mark
        try:
            mkt = self.h.bridge.run(self.h.dc.get_perp_market_account(market_index))

            # Try common mark/cached fields (different releases use different names)
            for name in (
                "mark_price_twap",                # already scaled or needs scaling?
                "mark_price",                     # cached integer mark
                "last_mark_price_twap",           # variant
            ):
                v = getattr(mkt, name, None)
                if v is not None:
                    # Heuristic: if it's a big int, assume 1e6 scaling
                    fv = float(v)
                    return fv / 1_000_000.0 if fv > 10_000 else fv

            # Try through amm sub-struct
            amm = getattr(mkt, "amm", None)
            if amm is not None:
                for name in (
                    "mark_price",                 # integer
                    "last_mark_price_twap",       # integer
                    "oracle_price_twap",          # integer
                ):
                    v = getattr(amm, name, None)
                    if v is not None:
                        fv = float(v)
                        return fv / 1_000_000.0 if fv > 10_000 else fv
        except Exception:
            pass

        # 3) Read oracle price data directly (generic path)
        try:
            pd = self.h.bridge.run(self.h.dc.get_oracle_price_data_for_perp_market(market_index))
            if hasattr(pd, "price"):
                return float(pd.price) / 1_000_000.0
        except Exception:
            pass

        # If everything failed, return None
        return None
