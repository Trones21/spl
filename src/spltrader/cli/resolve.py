# src/spl/cli/resolve.py
import click
from importlib.metadata import entry_points

def resolve_market(exchange: str, cfg: dict):
    eps = entry_points(group="spltrader.adapters")
    reg = {ep.name: ep for ep in eps}
    if exchange not in reg:
        raise click.ClickException(
            f"Adapter '{exchange}' not found.\n"
            "Install a plugin, e.g.:\n"
            "  pip install -e plugins/spl-adapter-hyperliquid\n"
            "  pip install -e plugins/spl-adapter-drift"
        )

    # build merged config
    merged = {**cfg, **cfg.get(exchange, {})}
    Market = reg[exchange].load()
    return Market(merged)
