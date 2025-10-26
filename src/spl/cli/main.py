import click, tomllib
from pathlib import Path

from spl.cli.resolve import resolve_market
from spl.adapters.mock import MockMarket

from spl.exec.backend_shadow import ShadowBackend
from spl.exec.backend_paper import PaperBackend

from spl.storage.sqlite_store import SQLiteStore

from spl.risk.basic import BasicRisk
from spl.risk.allow_all import AllowAllRisk

from spl.engine.engine import Engine

from spl.strategies.demo_market_tick import DemoMarketTick
from spl.strategies.demo import RangeBounce

from spl.cli.helpers import (
    fail,
    ensure_instance,
    validate_config,
    validate_strategy,
    validate_market,
    diagnostics_summary,
    check_storage_health
)


@click.command()
@click.option("--config", required=True, help="Path to TOML config")
@click.option("--observe", is_flag=True, help="View quotes only; do not trade")
def run(config, observe):
    cfg = tomllib.load(Path(config).open("rb"))

    # Pre-validate config
    validate_config(cfg)

    mode = cfg.get("mode")
    exchange = cfg.get("exchange")
    symbol = cfg.get("symbol")

    # Market adapter
    if exchange == "mock":
        market = MockMarket(cfg)
    if exchange == "hyperliquid":
        market = HyperliquidMarket(cfg.get("hyperliquid", {}))
    else:
        raise NotImplementedError(f"Exchange adapter not wired: {exchange}")


   # Storage
    store_cfg = cfg.get("storage", {})
    check_storage_health(store_cfg)
    store = SQLiteStore(cfg)
    
    
    # Exec backend
    if mode == "shadow":
        exec_backend = ShadowBackend(store, fee_bps=cfg["fees"]["bps"])
    elif mode == "paper":
        exec_backend = PaperBackend(store, fee_bps=cfg["fees"]["bps"],
                                    slippage_bps=cfg["slippage"]["bps"])
    else:
        raise NotImplementedError("Live backend not wired in demo scaffold.")

    # Risk
    # risk = BasicRisk(cfg["risk"])
    risk = AllowAllRisk()

    # Strategy
    strat_kind = cfg.get("strategy", {}).get("kind", "range_bounce_demo")
    if strat_kind == "range_bounce_demo":
        strategy = RangeBounce(cfg)
    if strat_kind == "demo_market_tick":
        print("mtk")
        strategy = DemoMarketTick(cfg)
    else:
        raise NotImplementedError(f"Strategy not found: {strat_kind}")

# ----- DO NOT EDIT BENEATH THIS LINE UNLESS YOU KNOW WHAT YOU ARE DOING ------

    # Pre-Run Checks
    risk = ensure_instance(risk, typename="risk")
    validate_strategy(strategy)
    validate_market(market)

    # Print pre-run summary
    diagnostics_summary(
        cfg=cfg,
        market=market,
        exec_backend=exec_backend,
        store=store,
        risk=risk,
        strategy=strategy,
        observe=observe,
    )

    # Engine
    eng = Engine(market, exec_backend, store, risk)
    click.echo(f"[SPL] Running mode={mode} exchange={exchange} symbol={symbol}")

    # Pylance complains here because symbol: str | None, but validate_config takes care of this check for us
    eng.run(symbol, strategy, observe=observe) # type: ignore[arg-type]

if __name__ == "__main__":
    run()
