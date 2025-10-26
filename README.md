# **SPL — Shadow · Paper · Live**

> A modular DIY trading execution platform that lets you run the **same strategy logic** across
> **Shadow**, **Paper**, and **Live** modes — without touching real liquidity until you choose to.

---

## 🌐 Overview

**SPL (Shadow · Paper · Live)** is a pluggable execution engine for running your trade strategies in three tiers:

| Mode       | Description                                         | Market Impact |
| ---------- | --------------------------------------------------- | ------------- |
| **Paper**  | Synthetic fills via quotes + slippage model         | None          |
| **Shadow** | Fills triggered by live trade tape (no orders sent) | None          |
| **Live**   | Real order placement with exchange SDK              | Real          |

Use the same indicator and signal code across all modes.
Switch environments by config — not by rewriting logic.

---

## 🧱 Architecture

```
spl/
├─ core/
│  ├─ types.py
│  ├─ interfaces.py
│  └─ utils.py
├─ engine/
│  ├─ engine.py
│  ├─ fill_paper.py
│  └─ fill_shadow.py
├─ adapters/
│  ├─ drift.py
│  └─ hyperliquid.py
├─ exec/
│  ├─ backend_paper.py
│  ├─ backend_shadow.py
│  └─ backend_live.py
├─ storage/
│  ├─ sqlite_store.py
│  └─ parquet_store.py
├─ risk/
│  └─ basic.py
└─ cli/
   └─ main.py
```

---

## ⚙️ Core Interfaces

*(abbreviated here for brevity)*

```python
from typing import Protocol, Iterable, Dict, Any
from .types import Quote, Trade, OrderReq, Fill, AccountSnapshot

class IMarketData(Protocol):
    def subscribe_quotes(self, symbol: str) -> Iterable[Quote]: ...
    def subscribe_trades(self, symbol: str) -> Iterable[Trade]: ...
    def get_funding(self, symbol: str) -> float: ...
    def get_mark_price(self, symbol: str) -> float: ...
```

…and similarly for `IExecutionBackend`, `IStorage`, and `IRisk`.

---

## 📊 Fill Models

(unchanged — same examples for Paper and Shadow fills)

---

## 🔌 Adapters

* **Drift:** uses [`driftpy`](https://github.com/drift-labs/driftpy) for live quotes/trades/funding.
* **Hyperliquid:** uses [`hyperliquid-python-sdk`](https://github.com/hyperliquid-dex/hyperliquid-python-sdk).
* Adapters only translate data → SPL’s core types.

---

## 🧾 Config (Mode, Market, Strategy, Risk, Storage, etc.)

```toml
# SPL configuration
# mode can be "shadow", "paper", or "live"
mode = "shadow"
exchange = "drift"
symbol = "SOL-PERP"

[fees]
bps = 1.0   # trading fee in basis points

[latency]
ms = 120

[slippage]
bps = 1.5

[risk]
max_attempts = 3
max_notional = 150000

[risk.circuit_breaker]
stops = 3
minutes = 10

[storage]
kind = "sqlite"
dsn = "sqlite:///spl.db"
path = "spl.db"
```
---

## 🧠 Design Philosophy

* **Pluggable:** Market data, execution, storage, risk all swappable.
* **Reproducible:** Config + run ID → reproducible behavior.
* **Safe:** Live mode opt-in with confirmation guard.
* **Unified:** Same logic runs identically in `paper`, `shadow`, or `live`.

---

## 🧩 Potential Future Work

* [ ] Async merge by timestamp
* [ ] Funding & fees models per venue
* [ ] Native OCO emulation
* [ ] Grafana/Prometheus metrics
* [ ] Historical replay ingestion
* [ ] Backtest vs. shadow performance comparison

---

## 📜 License

MIT — freely usable and forkable.
