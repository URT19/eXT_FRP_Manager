"""'EXTREME FRP' uppercase two-color header."""
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

# ─── Colors ───
C_PURPLE = "#a78bfa"
C_CYAN = "#56d4dd"
C_BLUE = "#5b9bff"
C_GREEN = "#7ec699"
C_MUTED = "#8e8e93"
C_TITLE = "#ffffff"

# ─── Block letters ───
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

PROTOCOL_COLORS = {
    "TCP": "#5b9bff",
    "KCP": "#a78bfa",
    "QUIC": "#56d4dd",
    "WebSocket": "#7ec699",
}


def show(version: str = "3.1", protocols: str = "", width: int = 120) -> None:
    """Print EXTREME FRP logo (purple EXTREME, cyan FRP)."""
    console.clear()

    body = Text()

    # ─── Logo rows (6 lines, no leading blank) ───
    for i in range(6):
        body.append("  ", style="")
        for L in EXTREME:
            body.append(L[i], style=f"bold {C_PURPLE}")
        body.append("    ", style="")
        for L in FRP:
            body.append(L[i], style=f"bold {C_CYAN}")
        body.append("\n", style="")

    # ─── Separator (right after logo, no gap) ───
    body.append("  ", style="")
    body.append("\u2500" * 87, style=f"dim {C_MUTED}")
    body.append("\n", style="")

    # ─── Subtitle (one line) ───
    body.append("  ", style="")
    body.append("Multi-Protocol Tunnel Manager", style=f"bold {C_TITLE}")
    body.append("  \u00b7  ", style=C_MUTED)
    body.append("TCP", style="#5b9bff")
    body.append("\u00b7", style=C_MUTED)
    body.append("KCP", style="#a78bfa")
    body.append("\u00b7", style=C_MUTED)
    body.append("QUIC", style="#56d4dd")
    body.append("\u00b7", style=C_MUTED)
    body.append("WebSocket", style="#7ec699")
    body.append("  \u00b7  ", style=C_MUTED)
    body.append("HAProxy Aggregation", style=C_MUTED)
    body.append("\n", style="")

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
