# **SPL — Shadow · Paper · Live**

> A modular DIY trading execution platform that lets you run the **same strategy logic** across
> **Shadow**, **Paper**, and **Live** modes — without touching real liquidity until you choose to.

---

## 🌐 Overview

Note that this is current just the very beginning, still in the POC / buildout phase.

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

## 🧮 Engine

(unchanged; core event loop same as before)

---

## 🧾 Config (Now in TOML)

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
```
---

## 🖥️ CLI

```bash
spl run --config config/drift.shadow.toml
```

### Example Python Entry

```python
import click, tomllib
from pathlib import Path
from spl.adapters.drift import DriftMarket
from spl.exec.backend_shadow import ShadowBackend
from spl.storage.sqlite_store import SQLiteStore
from spl.risk.basic import BasicRisk
from spl.engine.engine import Engine
from spl.strategies.demo import RangeBounce

@click.command()
@click.option("--config", required=True)
def run(config):
    cfg = tomllib.load(Path(config).open("rb"))
    market = DriftMarket(cfg)
    exec_ = ShadowBackend(SQLiteStore(cfg), fee_bps=cfg["fees"]["bps"])
    risk = BasicRisk(cfg["risk"])
    eng = Engine(market, exec_, SQLiteStore(cfg), risk)
    strat = RangeBounce(cfg)
    eng.run(cfg["symbol"], strat)

if __name__ == "__main__":
    run()
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

## ⚡ Installation

```bash
pip install -e .
spl run --config config/drift.shadow.toml
```

---

## 📜 License

MIT — freely usable and forkable.
