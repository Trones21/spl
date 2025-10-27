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

Exactly — that structure predates your **plugin split** and now needs to reflect the modular setup.
Here’s an updated architecture block that matches your current and future layout (core + plugins + configs + tests + Docker).

---

## 🧱 Architecture

```
spl-trader/
├─ pyproject.toml               # Core package (engine + CLI)
├─ README.md
├─ INSTALL_AND_RUN.md
├─ TESTING.md
├─ config/                      # Example configs for each adapter
│  ├─ example.shadow.toml
│  ├─ example.hyperliquid.toml
│  └─ example.drift.toml
├─ src/
│  └─ spl/
│     ├─ core/                  # Shared domain models & utilities
│     │  ├─ types.py
│     │  ├─ interfaces.py
│     │  └─ utils.py
│     ├─ engine/                # Execution loop + fill logic
│     │  ├─ engine.py
│     │  ├─ fill_paper.py
│     │  └─ fill_shadow.py
│     ├─ exec/                  # Order execution backends
│     │  ├─ backend_paper.py
│     │  ├─ backend_shadow.py
│     │  └─ backend_live.py
│     ├─ storage/               # Persistence layers
│     │  ├─ sqlite_store.py
│     │  └─ parquet_store.py
│     ├─ risk/                  # Risk frameworks
│     │  ├─ basic.py
│     │  └─ allow_all.py
│     ├─ strategies/            # Strategy modules
│     │  ├─ demo.py
│     │  └─ demo_market_tick.py
│     └─ cli/                   # Entrypoints & helpers
│        ├─ main.py
│        ├─ helpers.py
│        └─ list_adapters.py
│
├─ plugins/                     # External market adapters (isolated Poetry pkgs)
│  ├─ spl-adapter-hyperliquid/
│  │  ├─ pyproject.toml
│  │  ├─ src/spl_adapter_hyperliquid/adapter.py
│  │  └─ tests/
│  └─ spl-adapter-drift/
│     ├─ pyproject.toml
│     ├─ src/spl_adapter_drift/adapter.py
│     └─ tests/
│
├─ tests/                       # Core unit/integration tests
│  ├─ test_engine.py
│  ├─ test_hyperliquid_ws.py
│  └─ test_mock_market.py
│
├─ docker/                      # Optional Docker setup
│  ├─ Dockerfile
│  └─ docker-compose.yml
└─ bin/                         # Local helper scripts (optional)
   ├─ spl-hl
   └─ spl-drift
```

```
┌──────────────┐        ┌──────────────────────────┐
│   CLI (spl)  │        │     Config (TOML)        │
│ spl.cli.main │◄──────►│ mode/exchange/symbol/... │
└──────┬───────┘        └──────────────────────────┘
       │
       │ resolve_market(exchange, cfg)
       ▼
┌───────────────────────────────┐      Entry points (installed plugins)
│  Adapter Resolver             │─────► group="spl.adapters"
│  spl.cli.resolve              │      e.g. "hyperliquid" → HyperliquidMarket
└──────────────┬────────────────┘
               │ MarketClass = ep.load()
               ▼
       ┌─────────────────┐
       │  Market Adapter │  (plugin)
       │  e.g. HyperliquidMarket / DriftMarket
       └──────┬──────────┘
              │ subscribe_quotes()/subscribe_trades()
              ▼
        (streaming events)
              ▼
┌────────────────────────────────────────────────────────────────┐
│                           Engine                               │
│                        spl.engine.engine                       │
│                                                                │
│  while True:                                                   │
│    q = next(quotes)                                            │
│    fills_q = exec_backend.on_quote(q)  ─┐                      │
│    for f in fills_q: store.write_fill(f), risk.on_fill(f)  ◄───┘
│    for req in strategy.on_event(q):                           │
│        if risk.pre_place(req): exec_backend.place(req)        │
│                                                                │
│    t = next(trades)                                           │
│    fills_t = exec_backend.on_trade(t) ─┐                      │
│    for f in fills_t: store.write_fill(f), risk.on_fill(f)  ◄──┘
│    for req in strategy.on_event(t):                           │
│        if risk.pre_place(req): exec_backend.place(req)        │
└────────────────────────────────────────────────────────────────┘
              ▲                        ▲                 ▲
              │                        │                 │
     ┌────────┴───────┐       ┌────────┴──────┐  ┌──────┴──────────┐
     │  Strategy      │       │ Exec Backend  │  │   Store          │
     │  spl.strategies│       │ spl.exec.*    │  │ spl.storage.*    │
     │ on_event(evt)  │       │ paper/shadow  │  │ (sqlite/parquet) │
     │ → [OrderReq...]│       │ place()/fills │  │ write_fill/event │
     └────────────────┘       └───────────────┘  └──────────────────┘
              ▲
              │ risk.pre_place(req) / on_fill(fill)
              │
        ┌─────┴─────┐
        │   Risk     │
        │ spl.risk.* │
        └────────────┘
```

---

### 🧩 Plugin Layout

Each adapter plugin is its own Poetry project:

```
plugins/spl-adapter-hyperliquid/
├─ pyproject.toml
├─ src/spl_adapter_hyperliquid/
│  ├─ __init__.py
│  └─ adapter.py     # Implements HyperliquidMarket
└─ tests/
   └─ test_hyperliquid_ws.py
```

✅ Each plugin:

* Declares the **core** as a path dependency
  (`spl-trader = { path = "../../", develop = true }`)
* Exposes an **entry point** under
  `[tool.poetry.plugins."spl.adapters"]`
* Can be installed independently without breaking others

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

ToDo: Rewrite

---

## 🔌 Adapter Info

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
