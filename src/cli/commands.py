"""Typer CLI commands with Rich formatting."""

import asyncio
import time
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..services.operator_service import OperatorService

app = typer.Typer(
    name="csm",
    help="Lido CSM Operator Dashboard - Track your validator earnings",
)
console = Console()


def run_async(coro):
    """Helper to run async functions from sync CLI."""
    return asyncio.get_event_loop().run_until_complete(coro)


@app.command()
def check(
    address: str = typer.Argument(
        ..., help="Ethereum address (manager or rewards address)"
    ),
    operator_id: Optional[int] = typer.Option(
        None, "--id", "-i", help="Operator ID (skip address lookup)"
    ),
    rpc_url: Optional[str] = typer.Option(
        None, "--rpc", "-r", help="Custom RPC URL"
    ),
):
    """
    Check CSM operator rewards and earnings.

    Examples:
        csm check 0xYourAddress
        csm check 0xYourAddress --id 42
    """
    console.print()

    service = OperatorService(rpc_url)

    with console.status("[bold blue]Fetching operator data..."):
        if operator_id is not None:
            rewards = run_async(service.get_operator_by_id(operator_id))
        else:
            console.print(f"[dim]Looking up operator for address: {address}[/dim]")
            rewards = run_async(service.get_operator_by_address(address))

    if rewards is None:
        console.print("[red]No CSM operator found for this address/ID[/red]")
        raise typer.Exit(1)

    # Header panel
    console.print(
        Panel(
            f"[bold]CSM Operator #{rewards.node_operator_id}[/bold]\n"
            f"Manager: {rewards.manager_address}\n"
            f"Rewards: {rewards.reward_address}",
            title="Operator Info",
        )
    )

    # Validators table
    val_table = Table(title="Validators", show_header=False)
    val_table.add_column("Metric", style="cyan")
    val_table.add_column("Value", style="green")
    val_table.add_row("Total Validators", str(rewards.total_validators))
    val_table.add_row("Active Validators", str(rewards.active_validators))
    val_table.add_row("Exited Validators", str(rewards.exited_validators))
    console.print(val_table)
    console.print()

    # Rewards table
    rewards_table = Table(title="Earnings Summary")
    rewards_table.add_column("Metric", style="cyan")
    rewards_table.add_column("Value", style="green")
    rewards_table.add_column("Notes", style="dim")

    rewards_table.add_row(
        "Current Bond",
        f"{rewards.current_bond_eth:.6f} ETH",
        f"Required: {rewards.required_bond_eth:.6f} ETH",
    )
    rewards_table.add_row(
        "Excess Bond",
        f"[bold green]{rewards.excess_bond_eth:.6f} ETH[/bold green]",
        "Claimable",
    )
    rewards_table.add_row("", "", "")
    rewards_table.add_row(
        "Cumulative Rewards",
        f"{rewards.cumulative_rewards_shares:,} shares",
        "All-time total",
    )
    rewards_table.add_row(
        "Already Distributed",
        f"{rewards.distributed_shares:,} shares",
        "",
    )
    rewards_table.add_row(
        "Unclaimed Rewards",
        f"[bold green]{rewards.unclaimed_eth:.6f} ETH[/bold green]",
        f"({rewards.unclaimed_shares:,} shares)",
    )
    rewards_table.add_row("", "", "")
    rewards_table.add_row(
        "[bold]TOTAL CLAIMABLE[/bold]",
        f"[bold yellow]{rewards.total_claimable_eth:.6f} ETH[/bold yellow]",
        "Excess bond + unclaimed rewards",
    )

    console.print(rewards_table)
    console.print()


@app.command()
def watch(
    address: str = typer.Argument(..., help="Ethereum address to monitor"),
    interval: int = typer.Option(
        300, "--interval", "-i", help="Refresh interval in seconds"
    ),
    rpc_url: Optional[str] = typer.Option(
        None, "--rpc", "-r", help="Custom RPC URL"
    ),
):
    """
    Continuously monitor rewards with live updates.
    Press Ctrl+C to stop.
    """
    while True:
        console.clear()
        check(address, rpc_url=rpc_url)
        console.print(
            f"\n[dim]Refreshing every {interval} seconds... Press Ctrl+C to stop[/dim]"
        )
        time.sleep(interval)


@app.command(name="list")
def list_operators(
    rpc_url: Optional[str] = typer.Option(
        None, "--rpc", "-r", help="Custom RPC URL"
    ),
):
    """List all operators with rewards in the current tree."""
    service = OperatorService(rpc_url)

    with console.status("[bold blue]Fetching rewards tree..."):
        operator_ids = run_async(service.get_all_operators_with_rewards())

    console.print(f"\n[bold]Found {len(operator_ids)} operators with rewards:[/bold]")
    console.print(", ".join(str(op_id) for op_id in operator_ids))


if __name__ == "__main__":
    app()
