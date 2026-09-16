"""Interactive prompt wrappers."""
from __future__ import annotations

import questionary
from rich.console import Console

console = Console()


def ask(prompt: str, default: str = "", allow_empty: bool = False) -> str:
    while True:
        val = questionary.text(prompt, default=default).ask()
        if val is None:
            raise KeyboardInterrupt
        val = val.strip() or default
        if val or allow_empty:
            return val
        console.print("[red]This field is required.[/red]")


def ask_int(prompt: str, default: int | None = None,
            min_v: int | None = None, max_v: int | None = None) -> int:
    while True:
        raw = questionary.text(
            prompt,
            default=str(default) if default is not None else "",
            validate=lambda v: v.isdigit() or "Must be a number",
        ).ask()
        if raw is None:
            raise KeyboardInterrupt
        v = int(raw)
        if min_v is not None and v < min_v:
            console.print(f"[red]Minimum is {min_v}[/red]")
            continue
        if max_v is not None and v > max_v:
            console.print(f"[red]Maximum is {max_v}[/red]")
            continue
        return v


def confirm(prompt: str, default: bool = True) -> bool:
    """Ask Y/N and return immediately without needing Enter.

    Uses questionary.confirm which handles single-key Y/N.
    """
    result = questionary.confirm(prompt, default=default).ask()
    if result is None:
        # Ctrl+C → treat as False (cancel)
        return False
    return bool(result)


def choose(prompt: str, choices: list[str]) -> str | None:
    return questionary.select(prompt, choices=choices).ask()


def choose_multi(prompt: str, choices: list[str]) -> list[str]:
    return questionary.checkbox(prompt, choices=choices).ask() or []


def password(prompt: str) -> str:
    return questionary.password(prompt).ask() or ""


def pause(msg: str = "Press Enter to return...") -> None:
    console.input(f"\n[dim]{msg}[/dim]")
