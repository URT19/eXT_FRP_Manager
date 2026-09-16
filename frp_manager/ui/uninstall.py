"""Interactive uninstall helper for FRP Manager."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text
from rich import box

console = Console()

# Colors (matches cli.py palette)
C_SUCCESS = "#7ec699"
C_INFO = "#5b9bff"
C_WARNING = "#ffb86c"
C_DANGER = "#ff6b6b"
C_MUTED = "#8e8e93"
C_TITLE = "#ffffff"
C_IRAN = "#f5d76e"
C_KHAREJ = "#56d4dd"


# ═══════════════════════════════════════════════════════════════════════════
#  Inventory: what exists on the system
# ═══════════════════════════════════════════════════════════════════════════

def _check_service(unit: str) -> bool:
    r = subprocess.run(
        ["systemctl", "list-unit-files", unit],
        capture_output=True, text=True,
    )
    return unit in r.stdout


def _list_running_units(pattern: str) -> list[str]:
    r = subprocess.run(
        ["systemctl", "list-units", "--all", "--no-legend",
         "--plain", pattern],
        capture_output=True, text=True,
    )
    return [line.split()[0] for line in r.stdout.splitlines() if line.strip()]


def inventory() -> dict:
    """Return a dict describing everything that exists."""
    app_dir = Path("/opt/frp-manager")
    data_dir = app_dir / "data"
    venv_dir = app_dir / "venv"
    systemd_dir = Path("/etc/systemd/system")

    frps_units = _list_running_units("frps@*.service")
    frpc_units = _list_running_units("frpc@*.service")

    return {
        "app_dir": app_dir.exists(),
        "data_dir": data_dir.exists(),
        "venv": venv_dir.exists(),
        "bin_links": [
            p for p in [
                Path("/usr/local/bin/frp-manager"),
                Path("/usr/local/bin/frp-cli"),
                Path("/usr/local/bin/frp-tui"),
                Path("/usr/local/bin/frp-export"),
            ] if p.exists() or p.is_symlink()
        ],
        "frps_unit": _check_service("frps@.service"),
        "frpc_unit": _check_service("frpc@.service"),
        "haproxy_unit": _check_service("haproxy-frp-agg.service"),
        "haproxy_cfg": Path("/opt/frp-manager/data/haproxy/haproxy-agg.cfg").exists(),
        "frps_running": frps_units,
        "frpc_running": frpc_units,
        "frps_binary": Path("/usr/local/bin/frps").exists(),
        "frpc_binary": Path("/usr/local/bin/frpc").exists(),
    }


def _render_inventory(inv: dict) -> None:
    """Show what's installed."""
    console.print(f"[bold {C_TITLE}]Installed components:[/]\n")

    def row(icon: str, label: str, value: str,
            color: str = C_INFO) -> None:
        console.print(f"  [{color}]{icon}[/]  {label:<26} {value}")

    # App directory
    if inv["app_dir"]:
        row("●", "Application directory", "/opt/frp-manager", C_SUCCESS)
    else:
        row("○", "Application directory", "not found", C_MUTED)

    # Data
    if inv["data_dir"]:
        row("●", "Data directory", "/opt/frp-manager/data", C_SUCCESS)
    else:
        row("○", "Data directory", "not found", C_MUTED)

    # Venv
    if inv["venv"]:
        row("●", "Virtual environment", "/opt/frp-manager/venv", C_SUCCESS)
    else:
        row("○", "Virtual environment", "not found", C_MUTED)

    # Binaries
    if inv["frps_binary"] and inv["frpc_binary"]:
        row("●", "FRP binaries", "/usr/local/bin/frps + frpc", C_SUCCESS)
    else:
        row("○", "FRP binaries", "not found", C_MUTED)

    # Entrypoints
    if inv["bin_links"]:
        names = ", ".join(p.name for p in inv["bin_links"])
        row("●", "CLI entrypoints", names, C_SUCCESS)
    else:
        row("○", "CLI entrypoints", "none", C_MUTED)

    # Systemd units
    if inv["frps_unit"]:
        row("●", "frps@.service", "installed", C_SUCCESS)
    else:
        row("○", "frps@.service", "not installed", C_MUTED)

    if inv["frpc_unit"]:
        row("●", "frpc@.service", "installed", C_SUCCESS)
    else:
        row("○", "frpc@.service", "not installed", C_MUTED)

    if inv["haproxy_unit"]:
        row("●", "haproxy-frp-agg.service", "installed", C_SUCCESS)
    else:
        row("○", "haproxy-frp-agg.service", "not installed", C_MUTED)

    if inv["haproxy_cfg"]:
        row("●", "HAProxy config", "present", C_SUCCESS)

    # Running units
    n_frps = len(inv["frps_running"])
    n_frpc = len(inv["frpc_running"])
    if n_frps:
        row("●", "Running frps channels", str(n_frps), C_IRAN)
    if n_frpc:
        row("●", "Running frpc channels", str(n_frpc), C_KHAREJ)


# ═══════════════════════════════════════════════════════════════════════════
#  Confirmation helpers
# ═══════════════════════════════════════════════════════════════════════════

def _confirm_destructive(prompt: str) -> bool:
    """Require typing 'yes' for destructive actions."""
    console.print(f"\n[bold {C_DANGER}]{prompt}[/]")
    console.print(f"[{C_WARNING}]Type [bold]yes[/bold] to confirm, anything else to cancel:[/]")
    ans = Prompt.ask(">").strip().lower()
    return ans == "yes"


# ═══════════════════════════════════════════════════════════════════════════
#  Actual operations
# ═══════════════════════════════════════════════════════════════════════════

def _systemctl_stop(unit: str) -> None:
    subprocess.run(
        ["systemctl", "disable", "--now", unit],
        capture_output=True, text=True,
    )


def _stop_all_tunnels(inv: dict) -> None:
    """Stop all frps@/frpc@ instances + haproxy."""
    console.print(f"\n[{C_INFO}]Stopping services...[/]")

    for unit in inv["frps_running"]:
        _systemctl_stop(unit)
        console.print(f"  [{C_MUTED}]stopped[/] {unit}")

    for unit in inv["frpc_running"]:
        _systemctl_stop(unit)
        console.print(f"  [{C_MUTED}]stopped[/] {unit}")

    if inv["haproxy_unit"]:
        _systemctl_stop("haproxy-frp-agg.service")
        console.print(f"  [{C_MUTED}]stopped[/] haproxy-frp-agg.service")


def _remove_systemd_units(inv: dict) -> None:
    console.print(f"\n[{C_INFO}]Removing systemd units...[/]")
    units = []
    if inv["frps_unit"]:
        units.append(Path("/etc/systemd/system/frps@.service"))
    if inv["frpc_unit"]:
        units.append(Path("/etc/systemd/system/frpc@.service"))
    if inv["haproxy_unit"]:
        units.append(Path("/etc/systemd/system/haproxy-frp-agg.service"))

    for u in units:
        if u.exists():
            u.unlink()
            console.print(f"  [{C_MUTED}]removed[/] {u}")

    subprocess.run(["systemctl", "daemon-reload"], capture_output=True)


def _remove_bin_links(inv: dict) -> None:
    console.print(f"\n[{C_INFO}]Removing CLI entrypoints...[/]")
    for p in inv["bin_links"]:
        try:
            p.unlink()
            console.print(f"  [{C_MUTED}]removed[/] {p}")
        except Exception as e:
            console.print(f"  [{C_DANGER}]failed[/] {p}: {e}")


def _remove_frp_binaries(inv: dict) -> None:
    if not (inv["frps_binary"] or inv["frpc_binary"]):
        return
    console.print(f"\n[{C_INFO}]Removing FRP binaries...[/]")
    for p in (Path("/usr/local/bin/frps"), Path("/usr/local/bin/frpc")):
        if p.exists():
            p.unlink()
            console.print(f"  [{C_MUTED}]removed[/] {p}")


def _remove_data() -> None:
    console.print(f"\n[{C_INFO}]Removing data directory...[/]")
    data = Path("/opt/frp-manager/data")
    if data.exists():
        shutil.rmtree(data)
        console.print(f"  [{C_MUTED}]removed[/] {data}")


def _remove_app() -> None:
    console.print(f"\n[{C_INFO}]Removing application directory...[/]")
    app = Path("/opt/frp-manager")
    if app.exists():
        shutil.rmtree(app)
        console.print(f"  [{C_MUTED}]removed[/] {app}")


# ═══════════════════════════════════════════════════════════════════════════
#  High-level operations
# ═══════════════════════════════════════════════════════════════════════════

def stop_services_only() -> None:
    """Option 1: only stop, don't remove anything."""
    inv = inventory()
    if not (inv["frps_running"] or inv["frpc_running"] or inv["haproxy_unit"]):
        console.print(f"[{C_MUTED}]Nothing running to stop.[/]")
        return
    _stop_all_tunnels(inv)
    console.print(f"\n[{C_SUCCESS}]All services stopped.[/]")
    console.print(f"[{C_MUTED}]Data and configs are preserved.[/]")
    console.print(f"[{C_MUTED}]To start again: sudo frp-cli → menu [5] → restart[/]")


def remove_haproxy_only() -> None:
    """Option 2: remove HAProxy aggregation, keep tunnels."""
    inv = inventory()
    if not inv["haproxy_unit"] and not inv["haproxy_cfg"]:
        console.print(f"[{C_MUTED}]HAProxy is not installed.[/]")
        return

    console.print(f"\n[bold {C_WARNING}]This will remove:[/]")
    console.print(f"  • haproxy-frp-agg.service")
    console.print(f"  • /opt/frp-manager/data/haproxy/haproxy-agg.cfg")
    console.print(f"[{C_MUTED}]Tunnels and configs are kept.[/]")

    if not _confirm_destructive("Remove HAProxy aggregation?"):
        console.print(f"[{C_MUTED}]Cancelled.[/]")
        return

    if inv["haproxy_unit"]:
        _systemctl_stop("haproxy-frp-agg.service")
        Path("/etc/systemd/system/haproxy-frp-agg.service").unlink(missing_ok=True)
        subprocess.run(["systemctl", "daemon-reload"], capture_output=True)

    cfg = Path("/opt/frp-manager/data/haproxy/haproxy-agg.cfg")
    if cfg.exists():
        cfg.unlink()

    console.print(f"\n[{C_SUCCESS}]HAProxy removed.[/]")


def full_uninstall() -> None:
    """Option 3: remove everything including data."""
    inv = inventory()

    if not inv["app_dir"]:
        console.print(f"[{C_MUTED}]FRP Manager is not installed.[/]")
        return

    console.print(f"\n[bold {C_DANGER}]⚠  FULL UNINSTALL[/]")
    console.print(f"[{C_WARNING}]This will permanently remove:[/]\n")
    console.print(f"  • All running FRP channels")
    console.print(f"  • frps@.service, frpc@.service")
    console.print(f"  • haproxy-frp-agg.service")
    console.print(f"  • /usr/local/bin/frp-manager, frp-cli, frp-tui, frp-export")
    console.print(f"  • /usr/local/bin/frps, frpc")
    console.print(f"  • /opt/frp-manager/  (including ALL data, configs, tokens)")

    console.print(f"\n[bold {C_DANGER}]Data loss warning:[/]")
    console.print(f"  All Nodes, Routes, Channels, tokens, and configs will be gone.")

    console.print(f"\n[{C_WARNING}]Backup first?[/]")
    console.print(f"  → Cancel and run [11] Backup / Restore, or")
    console.print(f"  → Cancel and run: sudo frp-export")

    if not _confirm_destructive("Are you absolutely sure?"):
        console.print(f"[{C_MUTED}]Cancelled.[/]")
        return

    _stop_all_tunnels(inv)
    _remove_systemd_units(inv)
    _remove_bin_links(inv)
    _remove_frp_binaries(inv)
    _remove_data()
    _remove_app()

    console.print(f"\n[{C_SUCCESS}]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
    console.print(f"[{C_SUCCESS}]  FRP Manager fully removed.[/]")
    console.print(f"[{C_SUCCESS}]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
    console.print(f"\n[{C_MUTED}]The script will now exit.[/]")


def reset_defaults_only() -> None:
    """Option 4: delete only state.json and configs, keep binary + code."""
    inv = inventory()
    if not inv["data_dir"]:
        console.print(f"[{C_MUTED}]No data directory found.[/]")
        return

    console.print(f"\n[bold {C_WARNING}]This will remove:[/]")
    console.print(f"  • /opt/frp-manager/data/state.json")
    console.print(f"  • /opt/frp-manager/data/configs/*.toml")
    console.print(f"  • /opt/frp-manager/data/haproxy/*.cfg")
    console.print(f"  • /opt/frp-manager/data/exports/*.txt")
    console.print(f"[{C_MUTED}]Code, venv, and FRP binaries are kept.[/]")

    if not _confirm_destructive("Reset all data?"):
        console.print(f"[{C_MUTED}]Cancelled.[/]")
        return

    _stop_all_tunnels(inv)

    data = Path("/opt/frp-manager/data")
    for sub in ("configs", "haproxy", "exports", "backups", "logs"):
        d = data / sub
        if d.exists():
            shutil.rmtree(d)
            d.mkdir(parents=True, exist_ok=True)
            console.print(f"  [{C_MUTED}]cleared[/] {d}")

    state = data / "state.json"
    if state.exists():
        state.unlink()
        console.print(f"  [{C_MUTED}]removed[/] {state}")

    console.print(f"\n[{C_SUCCESS}]Data reset. Start fresh with: sudo frp-cli[/]")


# ═══════════════════════════════════════════════════════════════════════════
#  Main entry
# ═══════════════════════════════════════════════════════════════════════════

def show_menu() -> None:
    """Interactive uninstall menu."""
    while True:
        console.clear()
        console.print()
        console.print(f"[bold {C_DANGER}]╭──────────────────────────────────────────────────────────────╮[/]")
        console.print(f"[bold {C_DANGER}]│[/]  🗑   [bold {C_TITLE}]UNINSTALL / CLEANUP[/]                                [bold {C_DANGER}]│[/]")
        console.print(f"[bold {C_DANGER}]╰──────────────────────────────────────────────────────────────╯[/]")
        console.print()

        inv = inventory()
        _render_inventory(inv)

        console.print(f"\n[bold {C_TITLE}]Choose an action:[/]\n")
        console.print(f"  [{C_INFO}]1[/]  Stop all services            [{C_MUTED}](keep everything)[/]")
        console.print(f"  [{C_WARNING}]2[/]  Remove HAProxy only           [{C_MUTED}](keep tunnels)[/]")
        console.print(f"  [{C_WARNING}]3[/]  Reset all data                [{C_MUTED}](keep code + binary)[/]")
        console.print(f"  [{C_DANGER}]4[/]  Full uninstall                [{C_MUTED}](remove everything)[/]")
        console.print(f"  [{C_MUTED}]0[/]  Back to main menu")
        console.print()

        choice = Prompt.ask(
            f"[bold {C_INFO}]Choose[/]",
            choices=["0", "1", "2", "3", "4"],
            default="0",
            show_choices=False,
        )

        try:
            if choice == "0":
                return
            elif choice == "1":
                stop_services_only()
            elif choice == "2":
                remove_haproxy_only()
            elif choice == "3":
                reset_defaults_only()
            elif choice == "4":
                full_uninstall()
                console.print(f"\n[{C_MUTED}]Goodbye.[/]\n")
                import sys
                sys.exit(0)
        except KeyboardInterrupt:
            console.print(f"\n[{C_MUTED}]Interrupted.[/]")

        if choice != "0":
            Prompt.ask(f"\n[{C_MUTED}]Press Enter to continue[/]", default="")
