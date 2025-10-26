import threading, json, queue, time
from dataclasses import dataclass
from typing import Iterable, Optional
import anyio
import websockets
import orjson

from ..core.types import Quote, Trade, Side

HL_MAINNET_WS = "wss://api.hyperliquid.xyz/ws"
HL_TESTNET_WS = "wss://api.hyperliquid-testnet.xyz/ws"


@dataclass(frozen=True)
class _SubSpec:
    type: str           # "trades" | "l2Book"
    coin: str           # e.g., "SOL"
    n_levels: Optional[int] = None  # for l2Book; defaults to 20 on server


class HyperliquidMarket:
    """
    Bridges Hyperliquid WS -> blocking generators for Engine.subscribe_*.
    Uses a background task per stream that pushes into Queue.
    """
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.net = cfg.get("network", "mainnet")  # "mainnet" | "testnet"
        self.ws_url = HL_TESTNET_WS if self.net == "testnet" else HL_MAINNET_WS
        self._lock = threading.Lock()
        self._q_quotes: dict[str, queue.Queue] = {}
        self._q_trades: dict[str, queue.Queue] = {}
        self._threads: list[threading.Thread] = []
        print("Hyperliquid Network: ", self.net)

    def _ensure_queues(self, symbol: str) -> None:
        self._q_quotes.setdefault(symbol, queue.Queue(maxsize=10_000))
        self._q_trades.setdefault(symbol, queue.Queue(maxsize=10_000))

    # --- public API expected by Engine ---
    def subscribe_quotes(self, symbol: str) -> Iterable[Quote]:
        """
        symbol: your internal like "SOL-PERP" -> we map to HL coin "SOL".
        """
        coin = _to_hl_coin(symbol)
        self._ensure_stream(symbol, coin)
        q = self._q_quotes[symbol]
        while True:
            yield q.get()  # blocks until new Quote

    def subscribe_trades(self, symbol: str) -> Iterable[Trade]:
        coin = _to_hl_coin(symbol)
        self._ensure_stream(symbol, coin)
        q = self._q_trades[symbol]
        while True:
            yield q.get()

    # --- internals ---
    def _ensure_stream(self, symbol: str, coin: str) -> None:
        tag = f"{symbol}::{coin}"
        with self._lock:
            if any(t.name == tag for t in self._threads):
                return
            # make sure both queues exist BEFORE starting the worker
            self._ensure_queues(symbol)
            t = threading.Thread(target=self._ws_worker, name=tag, args=(symbol, coin), daemon=True)
            t.start()
            self._threads.append(t)


    def _ws_worker(self, symbol: str, coin: str) -> None:
        """
        Runs an anyio event loop in this thread; holds a single WS conn,
        subscribes to both l2Book and trades for `coin`, and pushes
        parsed messages to the symbol queues.
        """
        anyio.run(self._ws_loop, symbol, coin)

    async def _ws_loop(self, symbol: str, coin: str) -> None:
        self._ensure_queues(symbol) 
        q_quotes = self._q_quotes[symbol]
        q_trades = self._q_trades[symbol]
        
        # Subscription payloads per HL docs
        # example: {"method":"subscribe","subscription":{"type":"trades","coin":"SOL"}}
        #          {"method":"subscribe","subscription":{"type":"l2Book","coin":"SOL"}}
        subs = [
            {"method": "subscribe", "subscription": {"type": "trades", "coin": coin}},
            {"method": "subscribe", "subscription": {"type": "l2Book", "coin": coin}},
        ]

        backoff = 1.0
        while True:
            try:
                async with websockets.connect(self.ws_url, open_timeout=10) as ws:
                    # subscribe
                    for s in subs:
                        await ws.send(orjson.dumps(s).decode())

                    # main receive loop
                    async for raw in ws:
                        try:
                            msg = orjson.loads(raw)
                        except Exception:
                            continue

                        # Message routing:
                        # trades: {"channel":"trades","data":{"coin":"SOL","time":ms,"side":"B"/"S","px":float,"sz":float,...}}
                        # l2Book: {"channel":"l2Book","data":{"coin":"SOL","levels":{"bids":[[px,sz],...],"asks":[[px,sz],...]}}}
                        ch = msg.get("channel")
                        data = msg.get("data")

                        # ignore acks
                        if ch == "subscriptionResponse":
                            continue

                        if ch == "trades" and data:
                            # data is a list of trades
                            for trd in data:
                                if trd.get("coin") != coin:
                                    continue
                                ts = int(trd["time"])
                                px = float(trd["px"])
                                sz = float(trd["sz"])
                                side = Side.BUY if trd.get("side") in ("B", "Buy", "buy") else Side.SELL
                                _q_put(q_trades, Trade(ts=ts, price=px, size=sz, side=side))

                        elif ch == "l2Book" and data and data.get("coin") == coin:
                            # levels is [bids[], asks[]]; each level is a dict {px, sz, n}
                            bids, asks = data.get("levels", [[], []])
                            if bids and asks:
                                best_bid = bids[0]
                                best_ask = asks[0]
                                ts = int(data.get("time", int(time.time() * 1000)))
                                _q_put(q_quotes, Quote(
                                    ts=ts,
                                    bid=float(best_bid["px"]),
                                    ask=float(best_ask["px"]),
                                    bid_sz=float(best_bid["sz"]),
                                    ask_sz=float(best_ask["sz"]),
                                ))

                    # if loop exits normally, reset backoff
                    backoff = 1.0

            except Exception:
                # simple backoff + reconnect
                time.sleep(backoff)
                backoff = min(backoff * 2, 30.0)


def _q_put(q: queue.Queue, item):
    try:
        q.put_nowait(item)
    except queue.Full:
        # drop oldest to avoid blocking
        try:
            q.get_nowait()
        except Exception:
            pass
        q.put_nowait(item)


def _to_hl_coin(symbol: str) -> str:
    """
    Map your internal symbol (e.g., 'SOL-PERP') to HL 'coin' (e.g., 'SOL').
    Extend as needed.
    """
    s = symbol.upper()
    if s.endswith("-PERP"):
        return s.split("-")[0]
    return s
