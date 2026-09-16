"""Table rendering for FRP Manager v3 (Nodes / Routes / Channels)."""
from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich import box

from ..models import Node, Channel, Route
from ..system import systemd

console = Console()


def render_nodes(nodes: list[Node]) -> None:
    if not nodes:
        console.print("[yellow]No nodes configured yet.[/yellow]")
        return
    tbl = Table(title="Nodes", show_lines=False, box=box.ROUNDED)
    tbl.add_column("#", style="dim", width=3)
    tbl.add_column("Name", style="cyan bold")
    tbl.add_column("Host", style="yellow")
    tbl.add_column("Location", style="green")
    tbl.add_column("Note", style="dim")
    for i, n in enumerate(nodes, 1):
        tbl.add_row(str(i), n.name, n.host, n.location or "—", n.note or "—")
    console.print(tbl)


def render_channels(channels: list[Channel], role: str = "server") -> None:
    if not channels:
        console.print("[yellow]No channels configured yet.[/yellow]")
        return
    tbl = Table(title=f"Channels ({role})", show_lines=False, box=box.ROUNDED)
    tbl.add_column("Channel", style="cyan bold")
    tbl.add_column("Route")
    tbl.add_column("Node", style="yellow")
    tbl.add_column("Proto", style="magenta")
    tbl.add_column("Bind", justify="right")
    tbl.add_column("Remote", justify="right")
    tbl.add_column("Target", justify="right")
    tbl.add_column("Status")
    for ch in channels:
        svc = ch.frps_service if role == "server" else ch.frpc_service
        if systemd.is_active(svc):
            status = "[bright_green]● ONLINE[/]"
        else:
            status = "[bright_red]○ OFFLINE[/]"
        tbl.add_row(
            ch.name, ch.route_id, ch.node, ch.proto.upper(),
            str(ch.bind_port), str(ch.remote_port), str(ch.target_port),
            status,
        )
    console.print(tbl)


def render_routes(routes: list[Route], channels: dict[str, Channel]) -> None:
    if not routes:
        console.print("[yellow]No routes configured yet.[/yellow]")
        return
    tbl = Table(title="Routes", show_lines=True, box=box.ROUNDED)
    tbl.add_column("ID", style="cyan bold")
    tbl.add_column("Port", justify="right", style="yellow")
    tbl.add_column("Mode", style="magenta")
    tbl.add_column("Targets", style="green")
    for r in routes:
        rows = []
        for cname in r.channels:
            ch = channels.get(cname)
            if ch:
                rows.append(f"[cyan]{ch.name}[/cyan] → [dim]{ch.node}:{ch.target_port}[/dim]")
            else:
                rows.append(f"[red]{cname} (missing)[/red]")
        tbl.add_row(
            r.id, str(r.entry_port), r.mode,
            "\n".join(rows) if rows else "—",
        )
    console.print(tbl)
