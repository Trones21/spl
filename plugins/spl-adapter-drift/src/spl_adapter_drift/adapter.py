import threading, queue, time, anyio, websockets, orjson
from typing import Iterable
from spl.core.types import Quote, Trade, Side

DLOB_MAIN = "wss://dlob.drift.trade/ws"
DLOB_DEV  = "wss://master.dlob.drift.trade/ws"

class DriftMarket:
    def __init__(self, cfg: dict):
        net = (cfg or {}).get("network", "mainnet")
        self.ws_url = DLOB_DEV if net == "devnet" else DLOB_MAIN
        self._q_quotes = {}
        self._q_trades = {}
        self._threads = []

    def subscribe_quotes(self, symbol: str) -> Iterable[Quote]:
        coin = _to_drift_market(symbol)
        q = self._q_quotes.setdefault(symbol, queue.Queue(maxsize=10_000))
        self._ensure_stream(symbol, coin)
        while True:
            yield q.get()

    def subscribe_trades(self, symbol: str) -> Iterable[Trade]:
        coin = _to_drift_market(symbol)
        q = self._q_trades.setdefault(symbol, queue.Queue(maxsize=10_000))
        self._ensure_stream(symbol, coin)
        while True:
            yield q.get()

    def _ensure_stream(self, symbol: str, market: str):
        tag = f"{symbol}::{market}"
        if any(t.name == tag for t in self._threads):
            return
        t = threading.Thread(target=self._ws_worker, name=tag, args=(symbol, market), daemon=True)
        t.start()
        self._threads.append(t)

    def _ws_worker(self, symbol: str, market: str):
        anyio.run(self._ws_loop, symbol, market)

    async def _ws_loop(self, symbol: str, market: str):
        q_quotes = self._q_quotes.setdefault(symbol, queue.Queue(maxsize=10_000))
        q_trades = self._q_trades.setdefault(symbol, queue.Queue(maxsize=10_000))
        # DLOB server expects a subscribe message; channel names are “orderbook” per examples.
        # (Typescript examples in the drift-labs repos show usage; we focus on best bid/ask.) :contentReference[oaicite:2]{index=2}
        subs = [
            {"method": "subscribe", "channel": "orderbook", "market": market},
        ]
        backoff = 1.0
        while True:
            try:
                async with websockets.connect(self.ws_url, open_timeout=10) as ws:
                    for s in subs:
                        await ws.send(orjson.dumps(s).decode())
                    async for raw in ws:
                        try:
                            msg = orjson.loads(raw)
                        except Exception:
                            continue
                        ch = msg.get("channel")
                        data = msg.get("data")

                        if ch == "orderbook" and data and data.get("market") == market:
                            # Expect bids/asks arrays with price/size; take top levels.
                            bids = data.get("bids") or []
                            asks = data.get("asks") or []
                            if bids and asks:
                                bb = bids[0]; ba = asks[0]
                                ts = int(time.time() * 1000)
                                q = Quote(
                                    ts=ts,
                                    bid=float(bb["price"]),
                                    ask=float(ba["price"]),
                                    bid_sz=float(bb["size"]),
                                    ask_sz=float(ba["size"]),
                                )
                                _q_put(q_quotes, q)

                        # (Optional) if server emits trades/fills, map them:
                        if ch == "trades" and data and data.get("market") == market:
                            for trd in data.get("trades", []):
                                _q_put(q_trades, Trade(
                                    ts=int(trd["ts"]),
                                    price=float(trd["price"]),
                                    size=float(trd["size"]),
                                    side=Side.BUY if trd.get("side","buy").lower()=="buy" else Side.SELL,
                                ))

                backoff = 1.0
            except Exception:
                time.sleep(backoff)
                backoff = min(backoff * 2, 30.0)

def _q_put(q, item):
    try:
        q.put_nowait(item)
    except queue.Full:
        try: q.get_nowait()
        except Exception: pass
        q.put_nowait(item)

def _to_drift_market(symbol: str) -> str:
    # Map "SOL-PERP" -> "SOL-PERP" or whatever DLOB expects; adjust if needed.
    return symbol.upper()
