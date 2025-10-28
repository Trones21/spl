| File                | Purpose                                  | Depends on                                           |
| ------------------- | ---------------------------------------- | ---------------------------------------------------- |
| `adapter.py`        | Factory/wiring entry point               | `client`, `symbols`, `execution_live`, `market_data` |
| `client.py`         | Manages RPC, wallet, and DriftClient     | `async_bridge`                                       |
| `execution_live.py` | Live trading backend (IExecutionBackend) | `interfaces`, `types`, `client`, `symbols`           |
| `market_data.py`    | Market data provider (IMarketData)       | `client`, `symbols`                                  |
| `symbols.py`        | Symbol ↔ index ↔ lot conversions         | `driftpy.constants.config`                           |
| `async_bridge.py`   | Async–sync bridge utility                | built-in `asyncio`, `threading`                      |
| `utils.py`          | Optional helper functions                | none                                                 |
| `__init__.py`       | Package init / re-exports                | —                                                    |
