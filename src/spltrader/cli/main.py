import click, tomllib
from pathlib import Path

from spltrader.cli.resolve import resolve_market
from spltrader.mock_adapter.mock import MockMarket

from spltrader.exec.backend_shadow import ShadowBackend
from spltrader.exec.backend_paper import PaperBackend

from spltrader.storage.sqlite_store import SQLiteStore

from spltrader.risk.basic import BasicRisk
from spltrader.risk.allow_all import AllowAllRisk

from spltrader.engine.engine import Engine

from spltrader.strategies.demo_market_tick import DemoMarketTick
from spltrader.strategies.demo import RangeBounce

from spltrader.cli.helpers import (
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

    # Market adapter
    adapter = resolve_market(cfg["exchange"], cfg)
    if observe:
        # data-only; do not start Engine/strategy
        md = adapter.market_data()
        for q in md.subscribe_quotes(cfg["symbol"]):
            print(q)
        return

   # Storage
    store_cfg = cfg.get("storage", {})
    check_storage_health(store_cfg)
    store = SQLiteStore(cfg)
    
    
    # Exec backend
    # strategy runs for the 3 execution modes
    mode = cfg.get("mode", "paper")
    if mode == "paper":
        backend = PaperBackend(store=store, slippage_bps=cfg.get("paper", {}).get("slippage_bps", 1.0))
    elif mode == "shadow":
        backend = ShadowBackend(store=store)
    elif mode == "live":
        backend = adapter.execution_live()  # from your Drift adapter
    else:
        raise ValueError(f"unknown mode: {mode}")

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
