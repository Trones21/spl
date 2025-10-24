import click, tomllib
from pathlib import Path

from spl.adapters.mock import MockMarket
from spl.exec.backend_shadow import ShadowBackend
from spl.exec.backend_paper import PaperBackend
from spl.storage.sqlite_store import SQLiteStore
from spl.risk.basic import BasicRisk
from spl.engine.engine import Engine
from spl.strategies.demo import RangeBounce

@click.command()
@click.option("--config", required=True, help="Path to TOML config")
def run(config):
    cfg = tomllib.load(Path(config).open("rb"))

    mode = cfg.get("mode", "shadow")
    exchange = cfg.get("exchange", "mock")
    symbol = cfg.get("symbol", "SOL-PERP")

    # 1) Market adapter (mock for now)
    if exchange == "mock":
        market = MockMarket(cfg)
    else:
        raise NotImplementedError(f"Exchange adapter not wired: {exchange}")

    # 2) Exec backend
    store = SQLiteStore(cfg)
    if mode == "shadow":
        exec_backend = ShadowBackend(store, fee_bps=cfg["fees"]["bps"])
    elif mode == "paper":
        exec_backend = PaperBackend(store, fee_bps=cfg["fees"]["bps"],
                                    slippage_bps=cfg["slippage"]["bps"])
    else:
        raise NotImplementedError("Live backend not wired in demo scaffold.")

    # 3) Risk
    risk = BasicRisk(cfg["risk"])

    # 4) Strategy
    strat_kind = cfg.get("strategy", {}).get("kind", "range_bounce_demo")
    if strat_kind == "range_bounce_demo":
        strategy = RangeBounce(cfg)
    else:
        raise NotImplementedError(f"Strategy not found: {strat_kind}")

    # 5) Engine
    eng = Engine(market, exec_backend, store, risk)
    click.echo(f"[SPL] Running mode={mode} exchange={exchange} symbol={symbol}")
    eng.run(symbol, strategy)

if __name__ == "__main__":
    run()
