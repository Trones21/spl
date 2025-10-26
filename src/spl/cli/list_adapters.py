import click
from importlib.metadata import entry_points

@click.command("list-adapters")
def list_adapters():
    """List installed SPL adapter plugins."""
    eps = entry_points(group="spl.adapters")
    adapters = sorted([(ep.name, ep.value) for ep in eps])

    click.secho("\n🔌 Installed SPL Adapters\n", fg="cyan", bold=True)
    if not adapters:
        click.echo("No adapters found.\n")
        click.echo("Install one with:")
        click.echo("  pip install -e plugins/spl-adapter-hyperliquid")
        click.echo("  pip install -e plugins/spl-adapter-drift\n")
        raise SystemExit(1)

    for name, path in adapters:
        click.echo(f"• {name:<15} → {path}")

    click.secho("\n✅ Total:", fg="green", nl=False)
    click.echo(f" {len(adapters)} adapter(s) installed.\n")

if __name__ == "__main__":
    list_adapters()
