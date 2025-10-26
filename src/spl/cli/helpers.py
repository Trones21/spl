import os
import click
from pathlib import Path
from typing import Any, Mapping


# ----------------------- #
#   VALIDATION HELPERS    #
# ----------------------- #

def fail(msg: str) -> None:
    """Raise a friendly CLI error."""
    raise click.ClickException(msg)


def ensure_instance(obj, typename="component"):
    """Warn if user passed a class instead of an instance, and auto-instantiate."""
    if isinstance(obj, type):
        click.secho(f"[WARN] {typename} was a class ({obj.__name__}); auto-instantiating.", fg="yellow")
        return obj()
    return obj


def validate_config(cfg: Mapping[str, Any]) -> None:
    """Validate required top-level config keys and field types."""
    for key in ("mode", "exchange", "symbol"):
        if key not in cfg:
            fail(f"Config missing required key: {key}")

    fees = cfg.get("fees", {})
    if "bps" not in fees or not isinstance(fees["bps"], (int, float)):
        fail("Config [fees].bps must be set (float bps)")

    if cfg["mode"] == "paper":
        sl = cfg.get("slippage", {})
        if "bps" not in sl or not isinstance(sl["bps"], (int, float)):
            fail("Config [slippage].bps must be set for paper mode")

    if cfg["exchange"] == "hyperliquid":
        hl = cfg.get("hyperliquid", {})
        net = hl.get("network", "mainnet")
        if net not in ("mainnet", "testnet"):
            fail("hyperliquid.network must be 'mainnet' or 'testnet'")

    # Storage path must exist or be creatable
    storage_cfg = cfg.get("storage", {})
    db_path = storage_cfg.get("path")

    if not db_path:
        # Explicit warning instead of silent default
        click.secho("[WARN] No [storage].path specified in config; using default 'spl.db' in repo root.", fg="yellow")
        db_path = "spl.db"
        cfg.setdefault("storage", {})["path"] = db_path  # write back into cfg for later use

    resolved_path = Path(db_path).expanduser().resolve()
    parent = resolved_path.parent

    if not os.access(parent, os.W_OK):
        raise click.ClickException(f"Storage path not writeable: {parent}")

    # Print where we’ll write
    click.secho(f"[STORE] Using database at: {resolved_path}", fg="cyan")


def validate_strategy(strategy) -> None:
    """Ensure the strategy implements the expected interface."""
    if not hasattr(strategy, "on_event") or not callable(strategy.on_event):
        fail("Strategy must define an on_event(evt) method returning a list of OrderReqs")


def validate_market(market) -> None:
    """Ensure the market adapter exposes the required interface."""
    for fn in ("subscribe_quotes", "subscribe_trades"):
        if not hasattr(market, fn):
            fail(f"Market adapter missing required method: {fn}")


def check_storage_health(cfg):
    """Ensure SQLite storage path is writable and file can be created."""
    db_path = Path(cfg.get("storage", {}).get("path", "spl.db")).expanduser().resolve()
    parent = db_path.parent

    # Ensure parent exists
    parent.mkdir(parents=True, exist_ok=True)

    try:
        # Try touching the file
        with open(db_path, "a"):
            pass
        click.secho(f"[STORE] OK: writable at {db_path}", fg="cyan")
    except Exception as e:
        raise click.ClickException(f"[STORE] Cannot write to {db_path}: {e}")


# ----------------------- #
#   DIAGNOSTIC SUMMARY    #
# ----------------------- #

def diagnostics_summary(
    *,
    cfg: Mapping[str, Any],
    market,
    exec_backend,
    store,
    risk,
    strategy,
    observe: bool = False,
) -> None:
    """Prints a concise, colorized overview of the run context."""
    click.secho("\n╔════════════════════════════════════════╗", fg="cyan")
    click.secho("║         SPL Pre-Run Diagnostics        ║", fg="cyan", bold=True)
    click.secho("╚════════════════════════════════════════╝", fg="cyan")

    click.secho(f" Mode:       {cfg.get('mode', '???')}", fg="green")
    click.secho(f" Exchange:   {cfg.get('exchange', '???')}", fg="green")
    hl = cfg.get("hyperliquid", {})
    if cfg.get("exchange") == "hyperliquid":
        click.secho(f" Network:    {hl.get('network', 'mainnet')}", fg="green")

    click.secho(f" Symbol:     {cfg.get('symbol', '???')}", fg="green")
    click.secho(f" Observe:    {'Yes' if observe else 'No'}", fg="green")

    # --- Storage info ---
    db_path = Path(cfg.get("storage", {}).get("path", "spl.db")).expanduser().resolve()
    click.secho(f" Storage DB: {db_path}", fg="blue")
    
    click.secho(f"")
    # Component health indicators
    ok = lambda name: click.style("✅", fg="green") + f" {name}"
    warn = lambda name: click.style("⚠️ ", fg="yellow") + f" {name}"

    components = [
        ("Market", hasattr(market, "subscribe_quotes")),
        ("ExecBackend", hasattr(exec_backend, "on_quote")),
        ("Store", hasattr(store, "write_fill")),
        ("Risk", hasattr(risk, "pre_place")),
        ("Strategy", hasattr(strategy, "on_event")),
    ]

    for name, status in components:
        click.echo(f" {ok(name) if status else warn(name)}")

    click.secho("\nEverything looks good. Launching engine...\n", fg="cyan", bold=True)
