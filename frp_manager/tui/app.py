"""TUI placeholder — v3 rewrite in progress."""
from rich.console import Console

console = Console()


def run() -> None:
    console.print()
    console.print("[bold yellow]╭────────────────────────────────────────────╮[/]")
    console.print("[bold yellow]│  TUI is under rewrite for v3 architecture   │[/]")
    console.print("[bold yellow]│  Please use the CLI for now:                │[/]")
    console.print("[bold yellow]│                                             │[/]")
    console.print("[bold yellow]│      sudo frp-cli                           │[/]")
    console.print("[bold yellow]╰────────────────────────────────────────────╯[/]")
    console.print()
