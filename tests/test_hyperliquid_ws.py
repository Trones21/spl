# tests/test_hyperliquid_ws.py
import os
import time
import queue
import threading
import pytest

from spl.adapters.hyperliquid import HyperliquidMarket

@pytest.mark.integration
def test_hyperliquid_quotes_and_trades_smoke():
    """
    Connects to Hyperliquid WS (testnet by default) and asserts we receive
    at least one Quote and one Trade within a short timeout.
    """
    network = os.getenv("HL_NETWORK", "testnet")   # "mainnet" or "testnet"
    symbol  = os.getenv("HL_SYMBOL",  "SOL-PERP")  # e.g., "BTC-PERP", "SOL-PERP"

    market = HyperliquidMarket({"network": network})

    qgen = market.subscribe_quotes(symbol)
    tgen = market.subscribe_trades(symbol)

    out = queue.Queue()

    def pull_one(gen, tag):
        try:
            item = next(gen)  # blocking
            out.put((tag, item, None))
        except Exception as e:
            out.put((tag, None, e))

    # kick off two threads to avoid blocking the test
    threading.Thread(target=pull_one, args=(qgen, "quote"), daemon=True).start()
    threading.Thread(target=pull_one, args=(tgen, "trade"), daemon=True).start()

    seen = set()
    deadline = time.time() + 20.0  # generous timeout for CI / cold start

    while time.time() < deadline and seen != {"quote", "trade"}:
        try:
            tag, item, err = out.get(timeout=0.5)
        except queue.Empty:
            continue

        assert err is None, f"{tag} stream error: {err!r}"

        if tag == "quote":
            # basic sanity check
            assert item.bid < item.ask, f"bad quote: {item}"
            seen.add("quote")
        else:
            # trade sanity check
            assert item.price > 0 and item.size > 0, f"bad trade: {item}"
            seen.add("trade")

    assert seen == {"quote", "trade"}, f"did not receive both streams, got={seen}"
