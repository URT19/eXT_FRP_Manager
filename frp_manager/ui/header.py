"""Universal top header — used by ALL menus for consistent design."""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich import box

console = Console()

# ─── Colors ───
C_BRAND = "#5b9bff"
C_PURPLE = "#a78bfa"
C_CYAN = "#56d4dd"
C_SUCCESS = "#7ec699"
C_MUTED = "#8e8e93"
C_TITLE = "#ffffff"
C_INFO = "#5b9bff"

PROTOCOL_COLORS = {
    "TCP": "#5b9bff",
    "KCP": "#a78bfa",
    "QUIC": "#56d4dd",
    "WebSocket": "#7ec699",
}

# ─── Logo letters ───
E = [
    "███████╗",
    "██╔════╝",
    "█████╗  ",
    "██╔══╝  ",
    "███████╗",
    "╚══════╝",
]
X = [
    "██╗  ██╗",
    "╚██╗██╔╝",
    " ╚███╔╝ ",
    " ██╔██╗ ",
    "██╔╝ ██╗",
    "╚═╝  ╚═╝",
]
T = [
    "████████╗",
    "╚══██╔══╝",
    "   ██║   ",
    "   ██║   ",
    "   ██║   ",
    "   ╚═╝   ",
]
R = [
    "██████╗ ",
    "██╔══██╗",
    "██████╔╝",
    "██╔══██╗",
    "██║  ██║",
    "╚═╝  ╚═╝",
]
M = [
    "███╗   ███╗",
    "████╗ ████║",
    "██╔████╔██║",
    "██║╚██╔╝██║",
    "██║ ╚═╝ ██║",
    "╚═╝     ╚═╝",
]
F = [
    "███████╗",
    "██╔════╝",
    "█████╗  ",
    "██╔══╝  ",
    "██║     ",
    "╚═╝     ",
]
P = [
    "██████╗ ",
    "██╔══██╗",
    "██████╔╝",
    "██╔═══╝ ",
    "██║     ",
    "╚═╝     ",
]

EXTREME = [E, X, T, R, E, M, E]
FRP = [F, R, P]

APP_VERSION = "3.7"
MIN_WIDTH = 95


def render_logo(version: str = APP_VERSION, width: int = MIN_WIDTH) -> None:
    """Render the EXTREME FRP logo in a fixed-width panel."""
    body = Text()
    for i in range(6):
        body.append("  ", style="")
        for L in EXTREME:
            body.append(L[i], style=f"bold {C_PURPLE}")
        body.append("    ", style="")
        for L in FRP:
            body.append(L[i], style=f"bold {C_CYAN}")
        body.append("\n", style="")

    # Subtitle: no gap between logo and separator
    body.append("  ", style="")
    body.append("─" * 60, style=f"dim {C_MUTED}")
    body.append("\n", style="")

    # One-line subtitle
    body.append("  ", style="")
    body.append("Multi-Protocol Tunnel Manager", style=f"bold {C_TITLE}")
    body.append("  ·  ", style=C_MUTED)
    body.append("TCP", style="#5b9bff")
    body.append("·", style=C_MUTED)
    body.append("KCP", style="#a78bfa")
    body.append("·", style=C_MUTED)
    body.append("QUIC", style="#56d4dd")
    body.append("·", style=C_MUTED)
    body.append("WebSocket", style="#7ec699")
    body.append("  ·  ", style=C_MUTED)
    body.append("HAProxy Aggregation", style=C_MUTED)

    if body.plain.endswith("\n"):
        body.right_crop(1)

    console.print(Panel(
        body,
        title=f"[{C_MUTED}] v{version} [/]",
        title_align="right",
        border_style=C_PURPLE,
        box=box.ROUNDED,
        padding=(0, 1),
        width=width,
    ))


def render_top_header(
    version: str = APP_VERSION,
    width: int = MIN_WIDTH,
) -> None:
    """Render the logo + subtitle at the top of any screen.

    Call this from the START of every menu function to keep design consistent.
    """
    console.clear()
    render_logo(version=version, width=width)
