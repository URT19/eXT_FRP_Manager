"""FRP Manager v3 — Main CLI with Node/Route/Channel architecture."""
from __future__ import annotations

import re
import secrets
import string
import subprocess
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from . import state
from . import __version__ as APP_VERSION
from .config import Defaults, load_defaults, save_defaults
from .constants import (
    FRP_VERSION, HAPROXY_CFG, PROTOCOLS, PROTO_DISPLAY,
)
from .frp import installer, server as frp_server, client as frp_client, compact
from .haproxy import config as hap_cfg, service as hap_svc
from .i18n import t
from .models import Node, Channel, Route, Hub, ROLE_META
from .system import net, systemd, optimize
from .ui import logo, prompts, tables, shortcuts, help as help_ui
from .ui.header import render_top_header
from .ui import help as help_ui

console = Console()

# ═══════════════════════════════════════════════════════════════════════════
#  Colors — Apple Pro Palette (dark mode)
# ═══════════════════════════════════════════════════════════════════════════

# Side identity
C_IRAN = "#f5d76e"          # warm yellow — Hub (Iran)
C_KHAREJ = "#56d4dd"        # soft cyan — Node (Kharej)

# Roles
C_NEUTRAL = "#d4d4d4"       # text primary
C_MUTED = "#8e8e93"         # secondary text
C_DIM = "#5a5a5e"           # very dim

# Semantic
C_SUCCESS = "#7ec699"       # success green
C_INFO = "#5b9bff"          # info blue
C_WARNING = "#ffb86c"       # warning orange
C_DANGER = "#ff6b6b"        # destructive red
C_ACCENT = "#a78bfa"
C_CYAN = "#56d4dd"           # soft cyan (aliases)        # purple accent

# Fixed UI width (prevents panels stretching to terminal width)
MIN_WIDTH = 95
C_HIGHLIGHT = "#f5d76e"     # highlights

# Titles
C_TITLE = "#ffffff"         # section titles
C_BRAND = "#5b9bff"         # app brand


# ═══════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _random_token(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def get_installed_frp_version(binary: str = "frps") -> Optional[str]:
    import shutil
    from .constants import FRPS_BIN, FRPC_BIN

    if binary == "frps" and FRPS_BIN.exists():
        path = str(FRPS_BIN)
    elif binary == "frpc" and FRPC_BIN.exists():
        path = str(FRPC_BIN)
    else:
        path = shutil.which(binary)

    if not path:
        return None
    try:
        r = subprocess.run([path, "--version"],
                           capture_output=True, text=True, timeout=5)
    except Exception:
        return None
    out = (r.stdout or "") + (r.stderr or "")
    m = re.search(r"(\d+\.\d+\.\d+)", out)
    return m.group(1) if m else None


def frp_installed() -> bool:
    return get_installed_frp_version("frps") is not None


def detect_location_cached(st: dict) -> str:
    meta = st.setdefault("meta", {})
    cached = meta.get("location")
    if cached in ("IRAN", "KHAREJ"):
        return cached
    cc = net.detect_country_code(timeout=4)
    loc = "IRAN" if cc == "IR" else "KHAREJ"
    meta["location"] = loc
    state.save(st)
    return loc


def location_badge(loc: str) -> str:
    if loc == "IRAN":
        return f"[bold {C_IRAN}]● IRAN[/] [dim](inbound / frps)[/dim]"
    return f"[bold {C_KHAREJ}]● KHAREJ[/] [dim](outbound / frpc)[/dim]"


def get_cached_public_ip(st: dict, force_refresh: bool = False) -> str:
    """Return public IPv4, cached in state.meta.public_ip."""
    meta = st.setdefault("meta", {})
    if force_refresh or "public_ip" not in meta:
        ip = net.detect_public_ip(timeout=4) or "unknown"
        meta["public_ip"] = ip
        state.save(st)
        return ip
    return meta.get("public_ip", "unknown")


# ═══════════════════════════════════════════════════════════════════════════
#  Smart Advisor
# ═══════════════════════════════════════════════════════════════════════════



def _resolve_node_name(st: dict, ch) -> str:
    """Resolve the Hub name for a channel by matching serverAddr to node.host.

    Priority:
      1. Match frpc config serverAddr IP to a node.host
      2. Fallback to ch.node (may be stale)
    """
    from .constants import CONFIG_DIR

    # Try to read the frpc config
    try:
        cfg_path = CONFIG_DIR / f"frpc_{ch.name}.toml"
        if cfg_path.exists():
            content = cfg_path.read_text()
            m = re.search(r'serverAddr\s*=\s*"([^"]+)"', content)
            if m:
                hub_ip = m.group(1)
                # Find node with this host
                for node in state.list_nodes(st):
                    if node.host == hub_ip:
                        return node.name
                # No matching node — return IP
                return hub_ip
    except Exception:
        pass

    # Fallback to stored node name
    return ch.node


def _count_channels_for_node(st: dict, node_name: str, node_host: str) -> int:
    """Count channels that belong to this node (by name OR by host IP)."""
    from .constants import CONFIG_DIR

    count = 0
    for ch in state.list_channels(st):
        # Match by name
        if ch.node == node_name:
            count += 1
            continue

        # Match by host IP
        try:
            cfg_path = CONFIG_DIR / f"frpc_{ch.name}.toml"
            if cfg_path.exists():
                content = cfg_path.read_text()
                m = re.search(r'serverAddr\s*=\s*"([^"]+)"', content)
                if m and m.group(1) == node_host:
                    count += 1
        except Exception:
            pass

    return count


def build_kharej_health_summary(st: dict, d: Defaults) -> Optional[Panel]:
    """Compact per-hub status panel for KHAREJ (single-line rows)."""
    channels = state.list_channels(st)
    if not channels:
        return None

    groups = {}
    for ch in channels:
        groups.setdefault(ch.hub, []).append(ch)

    body = Text()
    total = len(channels)
    total_online = 0
    total_offline = 0

    for hub_name in sorted(groups.keys()):
        hub_channels = groups[hub_name]
        online = 0
        offline = 0
        by_proto = {"tcp": 0, "kcp": 0, "quic": 0, "ws": 0}
        routes = set()

        for ch in hub_channels:
            active = (
                systemd.is_active(ch.frps_service)
                or systemd.is_active(ch.frpc_service)
            )
            if active:
                online += 1
                total_online += 1
            else:
                offline += 1
                total_offline += 1
            if ch.proto in by_proto:
                by_proto[ch.proto] += 1
            routes.add(ch.target_port)

        if offline == 0:
            icon = "\u25cf"
            row_color = C_SUCCESS
        elif online == 0:
            icon = "\u25cb"
            row_color = C_DANGER
        else:
            icon = "\u25d0"
            row_color = C_WARNING

        # Compact row
        body.append("  ", style="")
        body.append(icon + " ", style=f"bold {row_color}")
        body.append(f"{hub_name}", style=f"bold {C_IRAN}")
        body.append(" \u2502 ", style=C_DIM)
        body.append(f"{len(hub_channels)}", style=f"bold {C_KHAREJ}")
        body.append(" tun", style=C_MUTED)

        proto_colors = {
            "tcp": C_INFO,
            "kcp": C_ACCENT,
            "quic": C_IRAN,
            "ws": C_SUCCESS,
        }
        proto_parts = []
        for proto in ("tcp", "kcp", "quic", "ws"):
            count = by_proto[proto]
            if count > 0:
                pc = proto_colors.get(proto, C_NEUTRAL)
                proto_parts.append((proto.upper(), count, pc))

        if proto_parts:
            body.append(" \u2502 ", style=C_DIM)
            for i, (pname, pcount, pc) in enumerate(proto_parts):
                if i > 0:
                    body.append(" ", style="")
                body.append(f"{pname}:", style=C_MUTED)
                body.append(f"{pcount}", style=f"bold {pc}")

        body.append(" \u2502 ", style=C_DIM)
        body.append("\u25cf", style=f"bold {C_SUCCESS}")
        body.append(f"{online}", style=f"bold {C_SUCCESS}")
        if offline > 0:
            body.append(" ", style="")
            body.append("\u25cb", style=f"bold {C_DANGER}")
            body.append(f"{offline}", style=f"bold {C_DANGER}")

        if routes:
            routes_str = ",".join(str(r) for r in sorted(routes))
            body.append(" \u2502 ", style=C_DIM)
            body.append(f"\u2192{routes_str}", style=f"bold {C_IRAN}")

        body.append("\n", style="")

    # Total
    body.append("  ", style="")
    body.append("\u2500" * 50, style=C_DIM)
    body.append("\n  ", style="")
    body.append("Total: ", style=C_MUTED)
    body.append(f"{total}", style=f"bold {C_KHAREJ}")
    body.append(" channels", style=C_MUTED)
    body.append("  \u2502  ", style=C_DIM)
    body.append("\u25cf", style=f"bold {C_SUCCESS}")
    body.append(f"{total_online}", style=f"bold {C_SUCCESS}")
    if total_offline > 0:
        body.append(" ", style="")
        body.append("\u25cb", style=f"bold {C_DANGER}")
        body.append(f"{total_offline}", style=f"bold {C_DANGER}")

    if total_offline == 0:
        border = C_SUCCESS
    elif total_online == 0:
        border = C_DANGER
    else:
        border = C_WARNING

    title = (
        f"[{C_KHAREJ}] \U0001f4e1 Channel Status [/] "
        f"[{C_MUTED}]({len(groups)} hub(s) \u2014 {total_online}/{total} online)[/] "
    )

    return Panel(
        body,
        title=title,
        border_style=border,
        box=box.ROUNDED,
        padding=(0, 1),
    )



def build_advisor(st: dict, loc: str, frp_ok: bool, d: Defaults) -> Panel:
    """Return a Rich Panel with contextual advice."""
    nodes = state.list_nodes(st)
    routes = state.list_routes(st)
    channels = state.list_channels(st)

    n_nodes = len(nodes)
    n_routes = len(routes)
    n_channels = len(channels)

    online = 0
    offline = 0
    for ch in channels:
        svc = ch.frps_service if loc == "IRAN" else ch.frpc_service
        if systemd.is_active(svc):
            online += 1
        else:
            offline += 1

    haproxy_ok = hap_svc.is_active() if HAPROXY_CFG.exists() else False
    balanced_routes = [r for r in routes if r.mode == "balanced"]

    # Priority 1: FRP missing
    if not frp_ok:
        body = Text()
        body.append("⚠  ", style=f"bold {C_DANGER}")
        body.append("FRP binary nasb nashode.", style=f"bold {C_DANGER}")
        body.append("\n\n", style=C_MUTED)
        body.append("  Ghadam 1 → az menu ", style=C_MUTED)
        body.append("[1]", style=f"bold {C_SUCCESS}")
        body.append(f" FRP v{FRP_VERSION} ro nasb kon.\n", style=C_MUTED)
        body.append("  Hame chiz be in ghadam vabaste ast.", style=C_MUTED)
        # (Shortcuts moved to separate panel)
        return Panel(
            body,
            title=f"[bold {C_WARNING}] ⚡ {t('adv_action_required', d)} [/]",
            border_style=C_WARNING,
            box=box.ROUNDED,
            padding=(0, 1),
        )

    # Priority 2: IRAN side
    if loc == "IRAN":
        lines: list[tuple[str, str]] = []
        tip = ""

        if n_nodes == 0:
            lines.append(("•", "Hanooz node tanzim nakardi, server-e kharej [node] ra add kon"))
            lines.append(("→", "Az [2] Wizard (pishnahadi) ya [3] Manage Nodes"))
            tip = (
                "Node = server-e kharej ke traffic behesh mire.\n"
                "  Mesal: Hetzner, Walter, Azure.\n"
                "  Wizard saree-tar-ein rah baraye setup-e aval."
            )
        elif n_routes == 0:
            lines.append(("•", f"{n_nodes} node dari, vali hanooz route nasakhti"))
            lines.append(("→", "Az [2] Wizard ya [4] Simple / [5] Balanced"))
            tip = (
                "Route = (port-e public) → (service rooye node).\n"
                "  Simple = 1 channel, Balanced = N channel + HAProxy."
            )
        else:
            state_txt = f"{online} online"
            if offline:
                state_txt += f" / {offline} offline"
            lines.append(("✓", f"{n_channels} channel — {state_txt}"))
            lines.append(("✓", f"{n_routes} route tarif shode"))

            if balanced_routes:
                if haproxy_ok:
                    lines.append(("✓", "HAProxy service ONLINE"))
                else:
                    lines.append(("!", "HAProxy config hast vali service OFF"))
                    lines.append(("→", "Restart az [6] Manage Routes → Rebuild"))
                    tip = "HAProxy baraye balanced route-ha zaroori-ye."

            if not tip:
                if offline > 0:
                    tip = (
                        "Chand channel offline — [9] Health check kon.\n"
                        "  [6] Manage Routes → Logs baraye debug."
                    )
                else:
                    tip = "Hame chi OK. Baraye route jadid: [2] Wizard ya [4]/[5]."

        body = Text()
        for icon, txt in lines:
            color = {
                "•": C_MUTED,
                "→": C_INFO,
                "✓": C_SUCCESS,
                "!": C_DANGER,
            }.get(icon, C_MUTED)
            body.append(f"  {icon}  ", style=f"bold {color}")
            body.append(txt + "\n", style=color)

        if tip and d.help_mode:
            body.append("\n  💡 ", style=f"bold {C_WARNING}")
            body.append(tip, style=f"italic {C_MUTED}")

        # (Shortcuts moved to separate panel)
        return Panel(
            body,
            title=f"[{C_IRAN}] ● IRAN [/] [{C_MUTED}]— Inbound Server (frps)[/] ",
            border_style=C_IRAN,
            box=box.ROUNDED,
            padding=(0, 1),
        )

    # Priority 3: KHAREJ side
    lines = []
    tip = ""

    if n_channels == 0:
        lines.append(("•", "Hanooz tunnel (channel) nadari"))
        lines.append(("→", "Rooye server IRAN (Hub) yek node tarif kon"))
        lines.append((" ", "  az tariq-e menu [2] Wizard ya menu [3] Node-ha"))
        lines.append(("→", "Bad link-haye compact ro biar rooye in server"))
        lines.append((" ", "  az tarigh-e menu [8] Import rooye Node"))
        tip = (
            "Agar roo server IRAN (Hub) ghablan node roo hamin server-e Public IP sakhti,\n"
            "  rooye hamoon server IRAN az tariq-e menu [7] Export baraye Node ro bezanid,\n"
            "  in server ro entekhab konid, link-e compact ro behetoon mideh, copy konid,\n"
            "  va rooye in server az tariq-e menu [8] Import rooye Node vared konid."
        )
    else:
        state_txt = f"{online} online"
        if offline:
            state_txt += f" / {offline} offline"
        lines.append(("✓", f"{n_channels} channel — {state_txt}"))

        listening = 0
        target_ports: set[int] = set()
        for ch in channels:
            target_ports.add(ch.target_port)
        for port in target_ports:
            if not net.is_port_free(port):
                listening += 1

        if listening == 0:
            lines.append(("!", "Hich service-i rooye target port-ha peyda nashod"))
            lines.append(("→", "Xray/service rooye port-ha start kon"))
            tip = (
                f"Service-haye mored-e entezar: "
                f"{', '.join(str(p) for p in sorted(target_ports))}\n"
                f"  Mesal: xray run -c /etc/xray/config.json"
            )
        elif listening < len(target_ports):
            lines.append(("ℹ", f"{listening}/{len(target_ports)} local port listen mikone"))
            tip = "Baraye har target port, yek service bayad listen kone."
        else:
            lines.append(("✓", "Service rooye hame target port-ha listen mikone"))
            tip = "Hame chi OK. Backend service rooye Xray kar mikone."

    body = Text()
    for icon, txt in lines:
        color = {
            "•": C_MUTED,
            "→": C_INFO,
            "ℹ": C_INFO,
            "✓": C_SUCCESS,
            "!": C_DANGER,
        }.get(icon, C_MUTED)
        body.append(f"  {icon}  ", style=f"bold {color}")
        body.append(txt + "\n", style=color)

    if tip and d.help_mode:
        body.append("\n  💡 ", style=f"bold {C_WARNING}")
        body.append(tip, style=f"italic {C_MUTED}")

    # ─── Shortcut hints ───
    # (Shortcuts moved)
    return Panel(
        body,
        title=f"[{C_KHAREJ}] ● KHAREJ [/] [{C_MUTED}]— Outbound Server (frpc)[/] ",
        border_style=C_KHAREJ,
        box=box.ROUNDED,
        padding=(0, 1),
    )


# Compact role banners for IRAN / KHAREJ
BANNER_IRAN = [
    "██╗  ██╗██╗  ██╗██╗   ██╗",
    "██║  ██║██║  ██║███╗  ██║",
    "███████║███████║██╔██╗ ██║",
    "██╔══██║██╔══██║██║╚██╗██║",
    "██║  ██║██║  ██║██║ ╚████║",
    "╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝",
]
BANNER_KHAREJ = [
    "██╗  ██╗██╗  ██╗ █████╗ ██████╗ ███████╗",
    "██║ ██╔╝██║  ██║██╔══██╗██╔══██╗██╔════╝",
    "█████╔╝ ███████║███████║██████╔╝█████╗  ",
    "██╔═██╗ ██╔══██║██╔══██║██╔══██╗██╔══╝  ",
    "██║  ██╗██║  ██║██║  ██║██║  ██║███████╗",
    "╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝",
]


def _build_role_banner(loc: str) -> Panel:
    """Build a role banner matching the info box height."""
    if loc == "IRAN":
        title = "HUB"
        subtitle = "Iran / Inbound / frps"
        color = C_IRAN
    else:
        title = "NODE"
        subtitle = "Kharej / Outbound / frpc"
        color = C_KHAREJ

    body = Text()
    body.append("\n", style="")
    body.append(f"  {title}\n", style=f"bold {color}")
    body.append("\n", style="")
    body.append(f"  {subtitle}", style=f"italic {C_MUTED}")

    return Panel(
        body,
        border_style=color,
        box=box.ROUNDED,
        padding=(0, 1),
        height=6,
    )



def render_header(st: dict, loc: str, d: Defaults) -> None:
    """Print header: logo + info (3 rows) + counters (3 rows)."""
    render_top_header(version=APP_VERSION, width=MIN_WIDTH)
    loc_color = C_IRAN if loc == "IRAN" else C_KHAREJ
    loc_role = "(inbound / frps)" if loc == "IRAN" else "(outbound / frpc)"

    installed = get_installed_frp_version("frps")
    if installed:
        ver_str = (
            f"v{installed} (up to date)"
            if installed == FRP_VERSION
            else f"v{installed} (expected v{FRP_VERSION})"
        )
        ver_color = C_SUCCESS if installed == FRP_VERSION else C_WARNING
    else:
        ver_str = "not installed"
        ver_color = C_DANGER

    # ─── Left panel: 3 rows ───
    info_txt = Text()
    info_txt.append(" Server location ", style=C_MUTED)
    info_txt.append(": ", style=C_DIM)
    info_txt.append("\u25cf ", style=f"bold {loc_color}")
    info_txt.append(loc, style=f"bold {loc_color}")
    info_txt.append(f"  {loc_role}\n", style=C_MUTED)

    info_txt.append(" FRP version     ", style=C_MUTED)
    info_txt.append(": ", style=C_DIM)
    info_txt.append(f"{ver_str}\n", style=f"bold {ver_color}")

    if d.show_ip:
        ip = get_cached_public_ip(st)
    else:
        ip = "hidden"
    info_txt.append(" Public IP       ", style=C_MUTED)
    info_txt.append(": ", style=C_DIM)
    info_txt.append(f"{ip}", style=f"bold {C_INFO}")

    info_panel = Panel(
        info_txt,
        border_style=C_MUTED,
        box=box.ROUNDED,
        padding=(0, 0),
        width=48,
        height=5,
    )

    # ─── Right panel: 3 rows (counters only) ───
    n_nodes = len(state.list_nodes(st))
    n_routes = len(state.list_routes(st))
    n_channels = len(state.list_channels(st))

    cnt_txt = Text()
    cnt_txt.append(" Hubs     ", style=C_MUTED)
    cnt_txt.append(": ", style=C_DIM)
    cnt_txt.append(f"{n_nodes}\n", style=f"bold {C_KHAREJ}")

    if loc == "IRAN":
        cnt_txt.append(" Routes   ", style=C_MUTED)
        cnt_txt.append(": ", style=C_DIM)
        cnt_txt.append(f"{n_routes}\n", style=f"bold {C_IRAN}")

    cnt_txt.append(" Channels ", style=C_MUTED)
    cnt_txt.append(": ", style=C_DIM)
    cnt_txt.append(f"{n_channels}", style=f"bold {C_SUCCESS}")

    cnt_panel = Panel(
        cnt_txt,
        border_style=loc_color,
        box=box.ROUNDED,
        padding=(0, 1),
        width=47,
        height=5,
    )

    from rich.columns import Columns
    console.print(Columns([info_panel, cnt_panel],
                          expand=False, padding=(0, 0)))



def build_shortcut_text(st: dict, loc: str, d: Defaults) -> Panel:
    """Build a single-line Panel with F-key shortcuts (descriptive labels)."""
    next_loc = "KHAREJ" if loc == "IRAN" else "IRAN"
    adv = getattr(d, "advanced_mode", True)

    bar = Text()
    bar.append("  ", style="")

    def cell(k: str, label: str, kind: str = "n") -> None:
        if kind == "d":
            style = "bold white on #c62828"
        else:
            style = "bold white on #1565c0"
        bar.append(f" {k} ", style=style)
        bar.append(f" {label}   ", style=C_MUTED)

    cell("F1", "Help")
    cell("F2", "Dastyar")
    cell("F3", "Language")
    cell("F5", "Location")
    cell("F7", "Advanced")
    cell("F10", "Exit", "d")

    return Panel(
        bar,
        border_style=C_INFO,
        box=box.ROUNDED,
        padding=(0, 0),
        width=MIN_WIDTH,
    )



def render_menu(st: dict, loc: str, d: Defaults) -> None:
    """Print main menu using Rich Table for perfect alignment."""
    side = C_IRAN if loc == "IRAN" else C_KHAREJ
    side = C_IRAN if loc == "IRAN" else C_KHAREJ
    help_on = d.help_mode
    is_iran = loc == "IRAN"
    is_kharej = loc == "KHAREJ"
    adv = getattr(d, "advanced_mode", True)

    items = []

    def add(num, label, color=C_NEUTRAL, hint="", disabled=False, reason=""):
        items.append((num, label, color, hint, disabled, reason))

    # ─── Build items ───
    frp_ok = frp_installed()
    v = get_installed_frp_version("frps") or ""
    ih = f"[{C_SUCCESS}]v{v}[/]" if frp_ok else f"[{C_DANGER}]![/]"
    add("1", "Nasb / Update FRP + HAProxy", C_INFO, ih)

    if is_iran:
        add("2", "Wizard", C_SUCCESS, f"[{C_SUCCESS}](quick)[/]")
    else:
        add("2", "Wizard", C_MUTED, disabled=True, reason="IRAN only")

    n_nodes = len(state.list_nodes(st))
    add("3", "Modiriyat Hub-ha", side, f"[{C_MUTED}]({n_nodes})[/]")

    if adv:
        if is_iran:
            add("4", "Sakht Simple Route", side, f"[{C_MUTED}](1 ch)[/]")
        else:
            add("4", "Sakht Simple Route", C_MUTED, disabled=True, reason="IRAN only")

        if is_iran:
            add("5", "Sakht Balanced Route", side, f"[{C_MUTED}](N ch)[/]")
        else:
            add("5", "Sakht Balanced Route", C_MUTED, disabled=True, reason="IRAN only")

        n_routes = len(state.list_routes(st))
        if is_iran:
            add("6", "Modiriyat Route-ha", side, f"[{C_MUTED}]({n_routes})[/]")
        else:
            add("6", "Modiriyat Route-ha", C_MUTED, disabled=True, reason="IRAN only")

        if is_iran:
            add("7", "Export baraye Node", C_IRAN)
        else:
            add("7", "Export baraye Node", C_MUTED, disabled=True, reason="IRAN only")

        if is_kharej:
            add("8", "Import rooye Node", C_KHAREJ)
        else:
            add("8", "Import rooye Node", C_MUTED, disabled=True, reason="KHAREJ only")

    n_ch = len(state.list_channels(st))
    add("9", "Modiriyat Channel-ha", C_INFO, f"[{C_MUTED}]({n_ch})[/]")

    if adv:
        add("10", "Speedtest", C_NEUTRAL)
        add("11", "Optimize System", C_NEUTRAL)
        add("12", "Backup / Restore", C_NEUTRAL)
        add("13", "Reset", C_DANGER, f"[{C_DANGER}](!)[/]")
        add("14", "Zaban", C_MUTED, f"[{C_MUTED}]({d.ui_lang[:3]})[/]")
        add("15", "Dastyar", C_INFO)
        hm = "ON" if help_on else "OFF"
        add("16", "Help Mode", C_MUTED, f"[{C_MUTED}][{hm}][/]")
        ip_ = "ON" if d.show_ip else "OFF"
        add("17", "Show IP", C_MUTED, f"[{C_MUTED}][{ip_}][/]")
        add("18", "Uninstall", C_DANGER)
        next_loc = "KHAREJ" if is_iran else "IRAN"
        add("19", "Switch Location", C_ACCENT, f"[{C_MUTED}]\u2192{next_loc}[/]")

    add("0", "Khoroj", C_MUTED)

    # ─── Split ───
    half = (len(items) + 1) // 2
    left = items[:half]
    right = items[half:]

    def cell_text(item) -> Text:
        num, label, color, hint, disabled, reason = item
        cell = Text()
        if disabled:
            cell.append(f"[{num:>2}]  ", style=f"dim {C_MUTED}")
            cell.append("\U0001f512 ", style="dim #ffb86c")
            cell.append(label, style=f"dim {C_MUTED}")
            if reason:
                cell.append("  ")
                cell.append(f"({reason})", style=f"dim italic {C_DANGER}")
        else:
            cell.append(f"[{num:>2}]  ", style=f"bold {color}")
            cell.append(label, style=color)
            if hint:
                cell.append("  ")
                cell.append_text(Text.from_markup(hint))
        return cell

    # ─── Rich Table for auto-alignment ───
    tbl = Table(
        show_header=False,
        box=None,
        padding=(0, 2),
        expand=False,
    )
    tbl.add_column("left", no_wrap=True, min_width=44)
    tbl.add_column("right", no_wrap=True)

    for i in range(max(len(left), len(right))):
        lc = cell_text(left[i]) if i < len(left) else Text("")
        rc = cell_text(right[i]) if i < len(right) else Text("")
        tbl.add_row(lc, rc)

    # ─── Menu Panel ───
    console.print(Panel(
        tbl,
        title=f"[bold {C_INFO}] \U0001f4cb Menu [/][{C_MUTED}]| {len(items)} items[/]",
        border_style=C_INFO,
        box=box.ROUNDED,
        padding=(0, 1),
        width=MIN_WIDTH,
    ))

    # ─── Help Hints Panel (separate box) ───
    if help_on:
        hint_map = {
            "1": "hint_menu_install",
            "2": "hint_menu_wizard",
            "3": "hint_menu_nodes",
            "4": "hint_menu_simple_route",
            "5": "hint_menu_balanced_route",
            "6": "hint_menu_manage_routes",
            "7": "hint_menu_export",
            "8": "hint_menu_import",
            "9": "hint_menu_health",
            "10": "hint_menu_speedtest",
            "11": "hint_menu_optimize",
            "12": "hint_menu_backup",
            "13": "hint_menu_reset",
            "14": "hint_menu_lang",
            "15": "hint_menu_help",
            "16": "hint_menu_help_toggle",
        }

        hints_text = Text()
        for num, label, color, hint, disabled, reason in items:
            if disabled:
                continue
            key = hint_map.get(num)
            if key:
                hints_text.append(f" [{num:>2}] ", style=f"bold {color}")
                hints_text.append("\u2192 ", style=f"dim {C_MUTED}")
                hints_text.append(t(key, d) + "\n", style=f"dim italic {C_MUTED}")

        if hints_text.plain.endswith("\n"):
            hints_text.right_crop(1)

        console.print(Panel(
            hints_text,
            title=f"[bold {C_WARNING}] \U0001f4a1 Dastyar (Help Hints) [/]",
            border_style=C_WARNING,
            box=box.ROUNDED,
            padding=(0, 1),
            width=MIN_WIDTH,
        ))

def render_hubs_table(hubs: list, st: dict) -> None:
    """Render hubs table with type, routes (from channels), and channel counts."""
    if not hubs:
        console.print(f"[yellow]Hich Hub-i tarif nashode.[/]")
        console.print()
        console.print(f"[{C_MUTED}]Baraye add kardan: menu [1][/]")
        return

    tbl = Table(title="Hubs", show_lines=False, box=box.ROUNDED)
    tbl.add_column("#", style="dim", width=3)
    tbl.add_column("Name", style="cyan bold")
    tbl.add_column("Host", style="yellow")
    tbl.add_column("Location", style="green")
    tbl.add_column("Type", style="magenta")
    tbl.add_column("Routes", style="bright_yellow")
    tbl.add_column("Channels", justify="right")
    tbl.add_column("Note", style="dim")

    for i, h in enumerate(hubs, 1):
        # ─── Count channels + collect routes ───
        channels = _channels_for_hub(st, h.name, h.host)
        ch_count = len(channels)
        ch_routes = sorted({c.target_port for c in channels})

        # ─── Determine type from channels (dynamic) ───
        if ch_count == 0:
            hub_type = "empty"
        elif ch_count == 1:
            hub_type = "simple"
        else:
            hub_type = "balanced"

        type_colors = {
            "simple": C_INFO,
            "balanced": C_SUCCESS,
            "empty": C_MUTED,
            "manual": C_WARNING,
        }
        type_color = type_colors.get(hub_type, C_MUTED)
        type_txt = f"[{type_color}]{hub_type}[/]"

        # ─── Routes display ───
        if ch_routes:
            routes_txt = ", ".join(str(p) for p in ch_routes[:4])
            if len(ch_routes) > 4:
                routes_txt += f" +{len(ch_routes) - 4}"
        else:
            routes_txt = "\u2014"

        tbl.add_row(
            str(i),
            h.name,
            h.host,
            h.location or "\u2014",
            type_txt,
            routes_txt,
            str(ch_count),
            h.note or "\u2014",
        )

    console.print(tbl)


def _channels_for_hub(st: dict, hub_name: str, hub_host: str) -> list:
    """Get channels for a hub (by name OR by host IP from frpc config)."""
    from .constants import CONFIG_DIR
    import re as _re

    matched = []

    for ch in state.list_channels(st):
        # Match by hub name
        if ch.hub == hub_name:
            matched.append(ch)
            continue

        # Match by host IP (from frpc config)
        try:
            cfg_path = CONFIG_DIR / f"frpc_{ch.name}.toml"
            if cfg_path.exists():
                content = cfg_path.read_text()
                m = _re.search(r'serverAddr\s*=\s*"([^"]+)"', content)
                if m and m.group(1) == hub_host:
                    matched.append(ch)
        except Exception:
            pass

    return matched


def _count_channels_for_hub(st: dict, hub_name: str, hub_host: str) -> int:
    """Backward-compat: just channel count."""
    return len(_channels_for_hub(st, hub_name, hub_host))


def _hub_channels_and_routes(st: dict, hub_name: str, hub_host: str):
    """Return (channel_count, sorted_routes)."""
    channels = _channels_for_hub(st, hub_name, hub_host)
    routes = sorted({c.target_port for c in channels})
    return len(channels), routes



def _hub_channels_and_routes(st: dict, hub_name: str, hub_host: str):
    """Return (channel_count, sorted_routes) for this hub.

    Matches by hub name OR by host IP (from frpc config serverAddr).
    """
    from .constants import CONFIG_DIR
    import re as _re

    channels = []
    routes = set()

    for ch in state.list_channels(st):
        matched = False

        # Match by hub name
        if ch.hub == hub_name:
            matched = True

        # Match by host IP (frpc config)
        if not matched:
            try:
                cfg_path = CONFIG_DIR / f"frpc_{ch.name}.toml"
                if cfg_path.exists():
                    content = cfg_path.read_text()
                    m = _re.search(r'serverAddr\s*=\s*"([^"]+)"', content)
                    if m and m.group(1) == hub_host:
                        matched = True
            except Exception:
                pass

        if matched:
            channels.append(ch)
            routes.add(ch.target_port)

    return len(channels), sorted(routes)


def _count_channels_for_hub(st: dict, hub_name: str, hub_host: str) -> int:
    """Backward-compat: just channel count."""
    count, _ = _hub_channels_and_routes(st, hub_name, hub_host)
    return count




def render_nodes_table_kharej(nodes: list[Node], st: dict) -> None:
    """Render a read-only nodes table for Kharej side.

    On Kharej, nodes are just pointers to HUB servers.
    Channel counts live on the Hub, not here.
    """
    if not nodes:
        console.print(f"[{C_MUTED}]Hich Hub-i tarif nashode.[/]")
        return

    tbl = Table(title="Nodes (read-only)", show_lines=False, box=box.ROUNDED)
    tbl.add_column("#", style="dim", width=3)
    tbl.add_column("Name", style="cyan bold")
    tbl.add_column("Host", style="yellow")
    tbl.add_column("Role", style="magenta")
    tbl.add_column("Note", style="dim")

    for i, n in enumerate(nodes, 1):
        # On Kharej, every node is a HUB (Iran) endpoint
        role = "HUB"
        tbl.add_row(
            str(i), n.name, n.host,
            f"[{C_IRAN}]{role}[/]",
            n.note or "\u2014",
        )
    console.print(tbl)


def manage_hubs(st: dict, d: Defaults, loc: str = "IRAN") -> None:
    """Manage hubs with role-aware UI.

    On KHAREJ:  Hub = Server-e IRAN  (role=iran_server)
    On IRAN:    Hub = Server-e KHAREJ (role=kharej_server)
    """
    # Determine which role we are managing from this side
    local_role = "iran_server" if loc == "KHAREJ" else "kharej_server"
    meta = ROLE_META[local_role]

    while True:
        console.clear()

        all_hubs = state.list_hubs(st)
        # Show all hubs (role filter removed for backward-compat)
        hubs = all_hubs

        # ─── Info panel ───
        info_body = Text()
        info_body.append("\n  ", style="")
        info_body.append("Current server:     ", style=C_MUTED)
        info_body.append_text(Text.from_markup(
            f"[bold {C_IRAN if loc == 'IRAN' else C_KHAREJ}]● {loc}[/]"
        ))
        info_body.append("\n  ", style="")
        info_body.append("Managing:           ", style=C_MUTED)
        info_body.append_text(Text.from_markup(
            f"[bold {meta['color']}]{meta['badge']}[/]"
        ))
        info_body.append("\n\n")
        info_body.append(f"  {meta['what']}\n", style=C_TITLE)
        info_body.append(f"  Mesal: {meta['example']}\n", style=C_MUTED)
        info_body.append("\n")
        info_body.append("  \U0001f4cb Workflow:\n", style=C_TITLE)
        for line in meta["workflow"]:
            info_body.append(f"  {line}\n", style=C_MUTED)
        info_body.append("\n")

        console.print(Panel(
            info_body,
            title=f"[bold {meta['color']}] \U0001f5a5  {meta['menu_title']} [/]",
            border_style=meta["color"],
            box=box.ROUNDED,
            padding=(0, 1),
            width=MIN_WIDTH,
        ))
        console.print()

        # ─── Table ───
        render_hubs_table(hubs, st)
        console.print()

        # ─── Menu ───
        console.print(f"[{C_INFO}]1[/] Add {meta['badge']}")
        if hubs:
            console.print(f"[{C_INFO}]2[/] Edit Hub")
            console.print(f"[{C_INFO}]3[/] Manage Channels")
            console.print(f"[{C_DANGER}]4[/] Remove Hub")
        console.print(f"[{C_MUTED}]h[/] Rahnama")
        console.print(f"[{C_MUTED}]0[/] Bargasht")

        choice = prompts.ask(t("choose", d), "").lower()

        if choice == "0":
            return
        if choice == "h":
            _show_hub_help(loc, local_role)
            continue

        if choice == "1":
            _hub_add(st, d, loc, local_role)
        elif choice == "2" and hubs:
            _hub_edit(st, d, hubs, loc)
        elif choice == "3" and hubs:
            _hub_channels_menu(st, d, hubs, loc)
        elif choice == "4" and hubs:
            _hub_delete(st, d, hubs, loc)
        else:
            console.print(f"[{C_DANGER}]Invalid[/]")
            prompts.pause()


def _show_hub_help(loc: str, local_role: str = "iran_server") -> None:
    """Detailed help for hub management (role-aware, plain text)."""
    console.clear()
    console.print()

    meta = ROLE_META[local_role]

    console.print(Panel(
        Text.from_markup(
            f"[bold {C_TITLE}]\U0001f4da  RAHNAMA — {meta['menu_title']}[/]\n"
            f"[{C_MUTED}]Tozihat-e kamel[/]\n"
        ),
        border_style=meta["color"],
        box=box.ROUNDED,
        padding=(0, 1),
        width=MIN_WIDTH,
    ))
    console.print()

    # ─── Use plain strings (not f-strings) to avoid markup issues ───
    if local_role == "iran_server":
        body1 = """[bold #5b9bff]\U0001f5fa  To rooye KHAREJ hasti[/]

  [bold #ffffff]Naqsh-e to:[/] [#8e8e93]Node server — frpc rooye hamin server ejra mishe[/]
  [bold #ffffff]Naqsh-e Hub:[/] [#8e8e93]Server-e IRAN (frps) — behesh vasl mishim[/]

  [bold #ffffff]Hub dar inja chie?[/]
  [#8e8e93]Har Hub = yek server-e IRAN ke frpc-e in server behesh vasl mishe.[/]
  [#8e8e93]Mesal: server-e IRAN-e asli, server-e backup[/]"""

        body2 = """[bold #7ec699]\U0001f504  Jaryan-e kar (Workflow)[/]

  [bold #ffffff]Ravesh 1 — Automatic (pishnahadi):[/]
  [#8e8e93]1. Rooye server-e IRAN, az menu [7] compact besaz[/]
  [#8e8e93]2. Inja az menu [8] Import kon[/]
  [#8e8e93]3. Hub + channel-ha khodkar sakhte mishan[/]

  [bold #ffffff]Ravesh 2 — Manual:[/]
  [#8e8e93]1. Inja yek Hub add kon (esm + IP server-e IRAN)[/]
  [#8e8e93]2. Channel-ha ro be in Hub vasl kon (menu [3])[/]
  [#8e8e93]3. Port + token ro ba IRAN sync kon[/]"""

        body3 = """[bold #ffb86c]\U0001f4a1 Chand nokte mohem[/]

  [bold #ffffff]•[/] [#8e8e93]Esm-e Hub bayad ba esm-e compact yeksan bashe[/]
  [bold #ffffff]•[/] [#8e8e93]Chand Hub mitoonan hamzaman bashe (HA)[/]
  [bold #ffffff]•[/] [#8e8e93]Age yek IRAN down beshe, baghi kar mikonan[/]
  [bold #ffffff]•[/] [#8e8e93]frpc rooye in server be IRAN vasl mishe[/]
  [bold #ffffff]•[/] [#8e8e93]Age Hub ro pak koni, hame channel-hash pak mishan[/]"""
    else:
        body1 = """[bold #5b9bff]\U0001f5fa  To rooye IRAN hasti[/]

  [bold #ffffff]Naqsh-e to:[/] [#8e8e93]Hub server — frps rooye hamin server ejra mishe[/]
  [bold #ffffff]Naqsh-e Hub:[/] [#8e8e93]Server-e KHAREJ (frpc) — inja behesh service midim[/]

  [bold #ffffff]Hub dar inja chie?[/]
  [#8e8e93]Har Hub = yek server-e kharej ke traffic behesh ferestade mishe.[/]
  [#8e8e93]Mesal: server-e Hetzner, Vultr, DO[/]"""

        body2 = """[bold #7ec699]\U0001f504  Jaryan-e kar (Workflow)[/]

  [bold #ffffff]Gadam 1:[/] [#8e8e93]Add Hub (esm + IP server-e kharej)[/]
  [bold #ffffff]Gadam 2:[/] [#8e8e93]Route besaz (menu [4] ya [5])[/]
  [bold #ffffff]Gadam 3:[/] [#8e8e93]Export (menu [7])[/]
  [bold #ffffff]Gadam 4:[/] [#8e8e93]Import rooye kharej[/]"""

        body3 = """[bold #ffb86c]\U0001f4a1 Chand nokte mohem[/]

  [bold #ffffff]•[/] [#8e8e93]Har Hub = yek server-e kharej (yek IP)[/]
  [bold #ffffff]•[/] [#8e8e93]Chand Route be hamoon Hub (chand port)[/]
  [bold #ffffff]•[/] [#8e8e93]Chand Hub hamzaman (chand server)[/]
  [bold #ffffff]•[/] [#8e8e93]HAProxy rooye IRAN traffic rooye channel-ha pakhsh mikone[/]"""

    console.print(Panel(
        Text.from_markup(body1),
        border_style=C_INFO,
        box=box.ROUNDED,
        padding=(0, 1),
        width=MIN_WIDTH,
    ))
    console.print()
    console.print(Panel(
        Text.from_markup(body2),
        border_style=C_SUCCESS,
        box=box.ROUNDED,
        padding=(0, 1),
        width=MIN_WIDTH,
    ))
    console.print()
    console.print(Panel(
        Text.from_markup(body3),
        border_style=C_WARNING,
        box=box.ROUNDED,
        padding=(0, 1),
        width=MIN_WIDTH,
    ))

    console.print()
    console.input(f"[{C_MUTED}]Enter bezan baraye bargasht...[/]")




def _hub_add(st: dict, d: Defaults, loc: str = "IRAN",
             local_role: str = "kharej_server") -> None:
    """Add a new hub with the correct role."""
    import re as _re

    meta = ROLE_META[local_role]

    console.print()
    console.print(Panel(
        Text.from_markup(
            f"[bold {meta['color']}]Adding: {meta['badge']}[/]\n"
            f"[{C_MUTED}]{meta['what']}[/]"
        ),
        border_style=meta["color"],
        box=box.ROUNDED,
        padding=(0, 1),
        width=MIN_WIDTH,
    ))
    console.print()

    # ─── Name ───
    if local_role == "iran_server":
        name_hint = "Esm-e server-e IRAN (mesal: iran-1, iran-hub-216)"
    else:
        name_hint = "Esm-e server-e KHAREJ (mesal: germany-1, hetzner-2)"

    name = prompts.ask(name_hint)
    if not _re.match(r"^[a-zA-Z0-9\-]{2,32}$", name):
        console.print(f"[{C_DANGER}]Esm na-motabar (faghat a-z, 0-9, dash)[/]")
        prompts.pause()
        return
    if state.get_hub(st, name):
        console.print(f"[{C_DANGER}]Hub '{name}' ghablan vojud dare[/]")
        prompts.pause()
        return

    # ─── Host ───
    if local_role == "iran_server":
        host_hint = "IP ya domain-e server-e IRAN"
    else:
        host_hint = "IP ya domain-e server-e KHAREJ"

    host = prompts.ask(host_hint)

    # ─── Location ───
    loc_val = prompts.ask("Location (ekhtiari, mesal: Germany, IRAN)", "", allow_empty=True)

    # ─── Note ───
    note = prompts.ask("Note (ekhtiari)", "", allow_empty=True)

    # ─── Create ───
    hub = Hub(
        name=name,
        host=host,
        role=local_role,
        location=loc_val,
        note=note,
        type="simple",
    )
    state.add_hub(st, hub)
    state.save(st)

    console.print()
    console.print(f"[{C_SUCCESS}]\u2713 {meta['badge']} '{name}' added[/]")
    console.print(f"  Host: {host}")

    # ─── Next steps ───
    console.print()
    console.print(f"[{C_INFO}]Next steps:[/]")
    for line in meta["workflow"]:
        console.print(f"  [{C_MUTED}]{line}[/]")

    prompts.pause()




def _hub_channels_menu(st: dict, d: Defaults, hubs: list, loc: str = "IRAN") -> None:
    """Manage channels for a specific hub."""
    sel = prompts.choose("Select hub", [h.name for h in hubs])
    if not sel:
        return

    hub = state.get_hub(st, sel)
    if not hub:
        return

    while True:
        console.clear()
        console.clear()

        # Channels of this hub
        channels = state.list_channels(st, hub=sel)

        # Location badge
        if loc == "IRAN":
            role_badge = f"[{C_IRAN}]IRAN[/] → Hub = [{C_KHAREJ}]{sel}[/]"
        else:
            role_badge = f"[{C_KHAREJ}]KHAREJ[/] → Hub = [{C_IRAN}]{sel}[/]"

        # Info panel
        console.print(Panel(
            Text.from_markup(
                f"[bold {C_INFO}]\U0001f4e1 Channels of Hub: {sel}[/]\n\n"
                f"  [{C_MUTED}]Role:  {role_badge}[/]\n"
                f"  [{C_MUTED}]Host:  {hub.host}[/]\n"
                f"  [{C_MUTED}]Type:  {hub.type}[/]\n"
                f"  [{C_MUTED}]Routes: {hub.routes or 'none'}[/]"
            ),
            border_style=C_INFO,
            box=box.ROUNDED,
            padding=(0, 1),
            width=MIN_WIDTH,
        ))
        console.print()

        # Table
        if channels:
            tbl = Table(show_lines=False, box=box.ROUNDED)
            tbl.add_column("#", style="dim", width=3)
            tbl.add_column("Channel", style="cyan bold")
            tbl.add_column("Proto", style="magenta")
            tbl.add_column("Bind", justify="right")
            tbl.add_column("Remote", justify="right")
            tbl.add_column("Target", justify="right")
            tbl.add_column("Status")

            for i, ch in enumerate(channels, 1):
                active = (systemd.is_active(ch.frps_service) or
                          systemd.is_active(ch.frpc_service))
                st_txt = f"[{C_SUCCESS}]ON[/]" if active else f"[{C_DANGER}]OFF[/]"

                tbl.add_row(
                    str(i),
                    ch.name,
                    ch.proto.upper(),
                    str(ch.bind_port),
                    str(ch.remote_port),
                    str(ch.target_port),
                    st_txt,
                )
            console.print(tbl)
        else:
            console.print(f"[{C_MUTED}]Hich channel-i baraye in Hub nist.[/]")
            if loc == "KHAREJ":
                console.print()
                console.print(f"[{C_INFO}]Chegune channel ezafe konam?[/]")
                console.print(f"  [{C_MUTED}]1. Rooye server-e IRAN (Hub), yek route besaz[/]")
                console.print(f"  [{C_MUTED}]2. Az menu [7] Export, compact ra begir[/]")
                console.print(f"  [{C_MUTED}]3. Az menu [8] Import, inja paste kon[/]")

        console.print()
        console.print(f"[{C_INFO}]1[/] Add channel (manual)")
        if channels:
            console.print(f"[{C_INFO}]2[/] Edit channel")
            console.print(f"[{C_INFO}]3[/] Restart channel")
            console.print(f"[{C_INFO}]4[/] View logs")
            console.print(f"[{C_DANGER}]5[/] Delete channel")
        console.print(f"[{C_MUTED}]0[/] Back")

        choice = prompts.ask(t("choose", d), "")

        if choice == "0":
            return
        if choice == "1":
            _channel_add(st, d, hub, loc)
        elif choice == "2" and channels:
            _channel_edit(st, d, hub, channels)
        elif choice == "3" and channels:
            _channel_restart(st, d, channels)
        elif choice == "4" and channels:
            _channel_view_logs(st, d, channels)
        elif choice == "5" and channels:
            _channel_delete(st, d, hub, channels)
        else:
            console.print(f"[{C_DANGER}]Invalid[/]")
            prompts.pause()


def _channel_add(st: dict, d: Defaults, hub, loc: str = "IRAN") -> None:
    """Add a channel to a hub manually."""
    console.print()
    console.print(f"[{C_INFO}]Adding channel to hub: {hub.name}[/]")
    console.print()

    if loc == "IRAN":
        console.print(f"[{C_MUTED}]In side: server-e IRAN (frps)[/]")
        console.print(f"[{C_MUTED}]In channel az IRAN be {hub.name} ({hub.host}) mire[/]")
    else:
        console.print(f"[{C_MUTED}]In side: server-e KHAREJ (frpc)[/]")
        console.print(f"[{C_MUTED}]In channel az inja be IRAN ({hub.host}) mire[/]")
    console.print()

    route_port = prompts.ask_int("Route port (public on Hub, mesal 443)", 443, 1, 65535)
    target_port = prompts.ask_int("Target port (Xray/service)", 443, 1, 65535)
    proto_choice = prompts.choose("Protocol", ["tcp", "kcp", "quic", "ws"])
    if not proto_choice:
        return
    proto = proto_choice

    route_id = f"rt-{route_port}"
    index = state.next_channel_index(st, route_id, hub.name)

    bind_port = net.random_free_port(d.port_range_start, d.port_range_end)
    token = _random_token(d.token_length)
    remote_port = 20000 + (route_port % 10000) + index
    iperf_port = 55000 + (route_port % 10000) + index

    ch = Channel(
        route_id=route_id,
        hub=hub.name,
        index=index,
        proto=proto,
        bind_port=bind_port,
        token=token,
        remote_port=remote_port,
        target_port=target_port,
        iperf_port=iperf_port,
    )

    # Save channel
    state.add_channel(st, ch)

    # Ensure route exists
    route = state.get_route(st, route_id)
    if not route:
        route = Route(
            id=route_id,
            entry_port=route_port,
            mode="balanced" if index > 1 else "simple",
            channels=[],
        )
    if ch.name not in route.channels:
        route.channels.append(ch.name)
    state.add_route(st, route)

    # Update hub routes
    if route_port not in hub.routes:
        hub.routes.append(route_port)
        state.add_hub(st, hub)

    # Write config
    if loc == "IRAN":
        _write_server_channel(ch, d)
    else:
        _write_client_channel(ch, hub, d)

    state.save(st)

    console.print()
    console.print(f"[{C_SUCCESS}]\u2713 Channel added: {ch.name}[/]")
    console.print(f"  bind={ch.bind_port}  remote={ch.remote_port}  target={ch.target_port}")
    console.print()
    console.print(f"[{C_WARNING}]\u26a0 Note: rooye taraf-e dige ham bayad channel add beshe.[/]")
    prompts.pause()


def _channel_edit(st: dict, d: Defaults, hub, channels: list) -> None:
    sel = prompts.choose("Select channel", [c.name for c in channels])
    if not sel:
        return
    ch = state.get_channel(st, sel)
    if not ch:
        return

    ch.target_port = prompts.ask_int(
        f"Target port (current: {ch.target_port})",
        ch.target_port, 1, 65535,
    )
    state.add_channel(st, ch)
    state.save(st)

    if prompts.confirm("Restart service now?", default=True):
        systemd.service_action(ch.frpc_service, "restart")
        systemd.service_action(ch.frps_service, "restart")
        console.print(f"[{C_SUCCESS}]\u2713 Channel updated + restarted[/]")

    prompts.pause()


def _channel_restart(st: dict, d: Defaults, channels: list) -> None:
    sel = prompts.choose("Select channel to restart", [c.name for c in channels])
    if not sel:
        return
    ch = state.get_channel(st, sel)
    if not ch:
        return
    systemd.service_action(ch.frpc_service, "restart")
    systemd.service_action(ch.frps_service, "restart")
    console.print(f"[{C_SUCCESS}]\u2713 {ch.name} restarted[/]")
    prompts.pause()


def _channel_view_logs(st: dict, d: Defaults, channels: list) -> None:
    sel = prompts.choose("Select channel", [c.name for c in channels])
    if not sel:
        return
    ch = state.get_channel(st, sel)
    if not ch:
        return
    console.print()
    console.print(f"[{C_INFO}]--- {ch.name} logs ---[/]")
    logs = systemd.logs(ch.frpc_service, 30)
    if not logs.strip():
        logs = systemd.logs(ch.frps_service, 30)
    console.print(logs)
    prompts.pause()


def _channel_delete(st: dict, d: Defaults, hub, channels: list) -> None:
    sel = prompts.choose("Select channel to delete", [c.name for c in channels])
    if not sel:
        return
    ch = state.get_channel(st, sel)
    if not ch:
        return

    if not prompts.confirm(f"Delete channel '{sel}'?", default=False):
        return

    _stop_channel_services(ch.name)
    frp_server.delete_frps_config(ch)
    frp_client.delete_frpc_config(ch)

    # Remove from route
    route = state.get_route(st, ch.route_id)
    if route:
        route.channels = [c for c in route.channels if c != ch.name]
        if not route.channels:
            state.remove_route(st, ch.route_id)
        else:
            state.add_route(st, route)

    st.get("channels", {}).pop(ch.name, None)
    state.save(st)

    console.print(f"[{C_DANGER}]\u2713 Channel '{sel}' deleted[/]")
    prompts.pause()





def _hub_edit(st: dict, d: Defaults, hubs: list, loc: str = "IRAN", host_hint: str = "") -> None:
    """Edit an existing hub."""
    sel = prompts.choose(t("nodes_select", d), [h.name for h in hubs])
    if not sel:
        return
    hub = state.get_hub(st, sel)
    if not hub:
        return

    hub.host = prompts.ask(t("nodes_host", d), hub.host)
    hub.location = prompts.ask(t("nodes_location", d), hub.location, allow_empty=True)
    hub.note = prompts.ask(t("nodes_note", d), hub.note, allow_empty=True)
    state.add_hub(st, hub)
    state.save(st)
    console.print(f"[{C_SUCCESS}]{t('nodes_updated', d, n=sel)}[/]")
    prompts.pause()


def _hub_delete(st: dict, d: Defaults, hubs: list, loc: str = "IRAN") -> None:
    """Delete a hub with all its channels."""
    sel = prompts.choose(t("nodes_select_del", d), [h.name for h in hubs])
    if not sel:
        return

    # Show impact
    channels = state.list_channels(st, hub=sel)
    if not channels:
        # Fallback: match by host IP
        from .constants import CONFIG_DIR
        import re as _re
        hub = state.get_hub(st, sel)
        if hub:
            for c in state.list_channels(st):
                cfg_path = CONFIG_DIR / f"frpc_{c.name}.toml"
                if cfg_path.exists():
                    content = cfg_path.read_text()
                    m = _re.search(r'serverAddr\s*=\s*"([^"]+)"', content)
                    if m and m.group(1) == hub.host:
                        channels.append(c)

    console.print()
    console.print(f"[bold {C_WARNING}]\u26a0 This will delete the hub and all its channels:[/]")
    console.print(f"  [{C_MUTED}]Hub: {sel}[/]")
    console.print(f"  [{C_MUTED}]Channels: {len(channels)}[/]")
    console.print()

    if not prompts.confirm(f"Remove '{sel}'?", default=False):
        return

    removed = state.remove_hub(st, sel)
    for cname in removed:
        _stop_channel_services(cname)
    state.save(st)

    console.print(f"[{C_DANGER}]{t('nodes_removed', d, n=sel, c=len(removed))}[/]")
    prompts.pause()


def _channel_add(st: dict, d: Defaults, hub) -> None:
    """Add a channel to a hub manually."""
    console.print()
    console.print(f"[{C_MUTED}]Manual channel add for hub: {hub.name}[/]")
    console.print()

    route_port = prompts.ask_int("Route port (public on hub, e.g. 443)", 443, 1, 65535)
    target_port = prompts.ask_int("Target port (on this server)", 443, 1, 65535)
    proto_choice = prompts.choose("Protocol", ["tcp", "kcp", "quic", "ws"])
    if not proto_choice:
        return
    proto = proto_choice

    route_id = f"rt-{route_port}"
    existing = state.list_channels(st, hub=hub.name)
    index = state.next_channel_index(st, route_id, hub.name)

    bind_port = net.random_free_port(d.port_range_start, d.port_range_end)
    token = _random_token(d.token_length)
    remote_port = 20000 + (route_port % 10000) + index
    iperf_port = 55000 + (route_port % 10000) + index

    ch = Channel(
        route_id=route_id,
        hub=hub.name,
        index=index,
        proto=proto,
        bind_port=bind_port,
        token=token,
        remote_port=remote_port,
        target_port=target_port,
        iperf_port=iperf_port,
    )

    # Save channel
    state.add_channel(st, ch)

    # Ensure route exists
    route = state.get_route(st, route_id)
    if not route:
        route = Route(
            id=route_id,
            entry_port=route_port,
            mode="balanced" if index > 1 else "simple",
            channels=[],
        )
    if ch.name not in route.channels:
        route.channels.append(ch.name)
    state.add_route(st, route)

    # Update hub routes list
    if route_port not in hub.routes:
        hub.routes.append(route_port)
        state.add_hub(st, hub)

    # Write frpc config for Kharej (this side)
    _write_client_channel(ch, hub, d)

    state.save(st)

    console.print()
    console.print(f"[{C_SUCCESS}]✅ Channel added:[/] {ch.name}")
    console.print(f"   bind={ch.bind_port}  remote={ch.remote_port}  target={ch.target_port}")
    console.print()
    console.print(f"[{C_MUTED}]Note: rooye server-e IRAN (Hub) ham bayad compact-e marboote add beshe.[/]")
    prompts.pause()


def _channel_edit(st: dict, d: Defaults, hub, channels: list) -> None:
    """Edit channel config manually."""
    sel = prompts.choose("Select channel", [c.name for c in channels])
    if not sel:
        return

    ch = state.get_channel(st, sel)
    if not ch:
        return

    console.print()
    console.print(f"[{C_INFO}]Editing: {ch.name}[/]")
    console.print()

    # Editable fields
    ch.target_port = prompts.ask_int(
        f"Target port (current: {ch.target_port})",
        ch.target_port, 1, 65535,
    )
    # Note: proto, bind_port, remote_port, token typically shouldn't change

    state.add_channel(st, ch)
    state.save(st)

    # Rewrite config
    _write_client_channel(ch, hub, d)

    if prompts.confirm("Restart service now?", default=True):
        systemd.service_action(ch.frpc_service, "restart")
        console.print(f"[{C_SUCCESS}]✅ Channel updated + restarted[/]")

    prompts.pause()


def _channel_restart(st: dict, d: Defaults, channels: list) -> None:
    sel = prompts.choose("Select channel to restart", [c.name for c in channels])
    if not sel:
        return
    ch = state.get_channel(st, sel)
    if not ch:
        return
    systemd.service_action(ch.frpc_service, "restart")
    systemd.service_action(ch.frps_service, "restart")
    console.print(f"[{C_SUCCESS}]✅ {ch.name} restarted[/]")
    prompts.pause()


def _channel_view_logs(st: dict, d: Defaults, channels: list) -> None:
    sel = prompts.choose("Select channel", [c.name for c in channels])
    if not sel:
        return
    ch = state.get_channel(st, sel)
    if not ch:
        return
    console.print()
    console.print(f"[{C_INFO}]--- {ch.name} logs ---[/]")
    # Try frpc first, then frps
    logs = systemd.logs(ch.frpc_service, 30)
    if not logs.strip():
        logs = systemd.logs(ch.frps_service, 30)
    console.print(logs)
    prompts.pause()


def _channel_delete(st: dict, d: Defaults, hub, channels: list) -> None:
    sel = prompts.choose("Select channel to delete", [c.name for c in channels])
    if not sel:
        return
    ch = state.get_channel(st, sel)
    if not ch:
        return

    if not prompts.confirm(f"Delete channel '{sel}'?", default=False):
        return

    _stop_channel_services(ch.name)
    frp_server.delete_frps_config(ch)
    frp_client.delete_frpc_config(ch)

    # Remove from route
    route = state.get_route(st, ch.route_id)
    if route:
        route.channels = [c for c in route.channels if c != ch.name]
        if not route.channels:
            state.remove_route(st, ch.route_id)
        else:
            state.add_route(st, route)

    # Remove from state
    st.get("channels", {}).pop(ch.name, None)
    state.save(st)

    console.print(f"[{C_DANGER}]✅ Channel '{sel}' deleted[/]")
    prompts.pause()




def _node_add(st: dict, d: Defaults) -> None:
    """Add a new node."""
    import re as _re

    name = prompts.ask(t("nodes_name", d))
    if not _re.match(r"^[a-zA-Z0-9\-]{2,32}$", name):
        console.print(f"[{C_DANGER}]{t('nodes_name_invalid', d)}[/]")
        prompts.pause()
        return
    if state.get_node(st, name):
        console.print(f"[{C_DANGER}]{t('nodes_exists', d, n=name)}[/]")
        prompts.pause()
        return
    host = prompts.ask(t("nodes_host", d))
    loc_val = prompts.ask(t("nodes_location", d), "", allow_empty=True)
    note = prompts.ask(t("nodes_note", d), "", allow_empty=True)
    state.add_node(st, Node(name=name, host=host, location=loc_val, note=note))
    state.save(st)
    console.print(f"[{C_SUCCESS}]{t('nodes_added', d, n=name)}[/]")
    prompts.pause()


def _node_edit(st: dict, d: Defaults, nodes: list) -> None:
    sel = prompts.choose(t("nodes_select", d), [n.name for n in nodes])
    if not sel:
        return
    node = state.get_node(st, sel)
    if not node:
        return
    node.host = prompts.ask(t("nodes_host", d), node.host)
    node.location = prompts.ask(t("nodes_location", d), node.location, allow_empty=True)
    node.note = prompts.ask(t("nodes_note", d), node.note, allow_empty=True)
    state.add_node(st, node)
    state.save(st)
    console.print(f"[{C_SUCCESS}]{t('nodes_updated', d, n=sel)}[/]")
    prompts.pause()


def _node_delete(st: dict, d: Defaults, nodes: list, loc: str = "IRAN") -> None:
    """Delete a node with all its channels."""
    sel = prompts.choose(t("nodes_select_del", d), [n.name for n in nodes])
    if not sel:
        return

    # ─── Show impact ───
    ch_count = len(state.list_channels(st, node=sel))
    affected_routes = []
    for r in state.list_routes(st):
        chs = [state.get_channel(st, cn) for cn in r.channels]
        chs = [c for c in chs if c and c.node == sel]
        if chs:
            affected_routes.append(r.id)

    console.print()
    console.print(f"[bold {C_WARNING}]\u26a0 In node hame channel-hash ra az dast mide:[/]")
    console.print(f"  [{C_MUTED}]Node: {sel}[/]")
    console.print(f"  [{C_MUTED}]Channels: {ch_count}[/]")
    if affected_routes:
        console.print(f"  [{C_MUTED}]Routes-e moteaser: {', '.join(affected_routes)}[/]")
    console.print()

    if not prompts.confirm(f"Remove '{sel}' and ALL its channels?", default=False):
        return

    # ─── Remove ───
    removed = state.remove_node(st, sel)
    for cname in removed:
        _stop_channel_services(cname)
    state.save(st)

    # Rebuild HAProxy if any balanced routes were affected (only on IRAN)
    if affected_routes and loc == "IRAN":
        try:
            _rebuild_haproxy(st, d)
        except Exception:
            pass

    console.print(f"[{C_DANGER}]{t('nodes_removed', d, n=sel, c=len(removed))}[/]")
    prompts.pause()



def _node_add(st: dict, d: Defaults) -> None:
    """Add a new node."""
    name = prompts.ask(t("nodes_name", d))
    if not re.match(r"^[a-zA-Z0-9\-]{2,32}$", name):
        console.print(f"[{C_DANGER}]{t('nodes_name_invalid', d)}[/]")
        prompts.pause()
        return
    if state.get_node(st, name):
        console.print(f"[{C_DANGER}]{t('nodes_exists', d, n=name)}[/]")
        prompts.pause()
        return
    host = prompts.ask(t("nodes_host", d))
    loc = prompts.ask(t("nodes_location", d), "", allow_empty=True)
    note = prompts.ask(t("nodes_note", d), "", allow_empty=True)
    state.add_node(st, Node(name=name, host=host,
                            location=loc, note=note))
    state.save(st)
    console.print(f"[{C_SUCCESS}]{t('nodes_added', d, n=name)}[/]")
    prompts.pause()


def _node_edit(st: dict, d: Defaults, nodes: list[Node]) -> None:
    """Edit an existing node."""
    sel = prompts.choose(t("nodes_select", d), [n.name for n in nodes])
    if not sel:
        return
    node = state.get_node(st, sel)
    if not node:
        return
    node.host = prompts.ask(t("nodes_host", d), node.host)
    node.location = prompts.ask(t("nodes_location", d),
                                node.location, allow_empty=True)
    node.note = prompts.ask(t("nodes_note", d),
                            node.note, allow_empty=True)
    state.add_node(st, node)
    state.save(st)
    console.print(f"[{C_SUCCESS}]{t('nodes_updated', d, n=sel)}[/]")
    prompts.pause()


def _node_delete(st: dict, d: Defaults, nodes: list[Node]) -> None:
    """Delete a node with all its channels."""
    sel = prompts.choose(t("nodes_select_del", d), [n.name for n in nodes])
    if not sel:
        return

    # Show impact
    ch_count = len(state.list_channels(st, node=sel))
    affected_routes = []
    for r in state.list_routes(st):
        chs = [state.get_channel(st, cn) for cn in r.channels]
        chs = [c for c in chs if c and c.node == sel]
        if chs:
            affected_routes.append(r.id)

    console.print()
    console.print(f"[bold {C_WARNING}]\u26a0 In node hame channel-hash ra az dast mide:[/]")
    console.print(f"  [{C_MUTED}]Node: {sel}[/]")
    console.print(f"  [{C_MUTED}]Channels: {ch_count}[/]")
    if affected_routes:
        console.print(f"  [{C_MUTED}]Routes-e moteaser: {', '.join(affected_routes)}[/]")
    console.print()

    if not prompts.confirm(f"Remove '{sel}' and ALL its channels?",
                            default=False):
        return

    removed = state.remove_node(st, sel)
    for cname in removed:
        _stop_channel_services(cname)
    state.save(st)

    # Rebuild HAProxy if any balanced routes were affected
    if affected_routes:
        try:
            _rebuild_haproxy(st, d)
        except Exception:
            pass

    console.print(f"[{C_DANGER}]{t('nodes_removed', d, n=sel, c=len(removed))}[/]")
    prompts.pause()



def create_simple_route(st: dict, d: Defaults, loc: str) -> None:
    render_top_header(version=APP_VERSION, width=MIN_WIDTH)
    if loc != "IRAN":
        console.print(f"[{C_KHAREJ}]Simple Route faghat rooye IRAN sakhte mishe.[/]")
        prompts.pause(); return

    nodes = state.list_nodes(st)
    if not nodes:
        console.print(f"[{C_DANGER}]{t('sr_no_nodes', d)}[/]")
        prompts.pause(); return

    console.print(f"[bold {C_IRAN}]{t('sr_title', d)}[/]\n")

    node_name = prompts.choose(t("sr_select_node", d), [n.name for n in nodes])
    if not node_name:
        return
    node = state.get_node(st, node_name)
    assert node

    entry_port = prompts.ask_int(t("sr_entry_port", d), 8443, 1, 65535)
    if state.get_route_by_port(st, entry_port):
        console.print(f"[{C_DANGER}]Port {entry_port} ghablan estefade shode.[/]")
        prompts.pause(); return

    target_port = prompts.ask_int(t("sr_target_port", d), entry_port, 1, 65535)

    proto_choice = prompts.choose(t("sr_protocol", d),
                                   ["tcp", "kcp", "quic", "ws"])
    if not proto_choice:
        return
    proto = proto_choice

    console.print(f"\n[{C_INFO}]{t('sr_will_create', d, entry=entry_port, node=node_name, target=target_port, proto=proto)}[/]")
    if not prompts.confirm(t("continue_q", d), default=True):
        return

    route_id = f"rt-{entry_port}"
    bind_port = net.random_free_port(d.port_range_start, d.port_range_end)
    token = _random_token(d.token_length)
    # simple route: direct port forward — remote_port == entry_port
    remote_port = entry_port
    iperf_port = 55000 + (entry_port % 10000)

    ch = Channel(
        route_id=route_id, node=node_name, index=1, proto=proto,
        bind_port=bind_port, token=token,
        remote_port=remote_port, target_port=target_port,
        iperf_port=iperf_port,
    )
    route = Route(
        id=route_id, entry_port=entry_port, mode="simple",
        channels=[ch.name],
    )

    # Write configs
    _write_server_channel(ch, d)
    state.add_channel(st, ch)
    state.add_route(st, route)
    state.save(st)

    net.ufw_allow(bind_port, "udp" if proto in ("kcp", "quic") else "tcp")
    net.ufw_allow(bind_port, "tcp")

    console.print(f"\n[{C_SUCCESS}]{t('sr_created', d)}[/]")
    console.print(f"  [{C_KHAREJ}]{t('sr_created_channel', d, name=ch.name)}[/]")
    console.print(f"  bind={ch.bind_port}  remote={ch.remote_port}  target={ch.target_port}")
    prompts.pause()


# ═══════════════════════════════════════════════════════════════════════════
#  Balanced Route
# ═══════════════════════════════════════════════════════════════════════════

def create_balanced_route(st: dict, d: Defaults, loc: str) -> None:
    render_top_header(version=APP_VERSION, width=MIN_WIDTH)
    if loc != "IRAN":
        console.print(f"[{C_KHAREJ}]Balanced Route faghat rooye IRAN sakhte mishe.[/]")
        prompts.pause(); return

    nodes = state.list_nodes(st)
    if not nodes:
        console.print(f"[{C_DANGER}]{t('br_no_nodes', d)}[/]")
        prompts.pause(); return

    console.print(f"[bold {C_IRAN}]{t('br_title', d)}[/]\n")

    entry_port = prompts.ask_int(t("br_entry_port", d), 443, 1, 65535)
    if state.get_route_by_port(st, entry_port):
        console.print(f"[{C_DANGER}]Port {entry_port} ghablan estefade shode.[/]")
        prompts.pause(); return

    selected = prompts.choose_multi(t("br_select_nodes", d),
                                     [n.name for n in nodes])
    if not selected:
        console.print(f"[yellow]Hich node-i entekhab nashod.[/]")
        prompts.pause(); return

    per_node = prompts.ask_int(t("br_channels_per_node", d), 3, 1, 8)
    total = per_node * len(selected)

    protos_input = prompts.ask(t("br_channel_protos", d),
                                "tcp,tcp,ws")
    protos = [p.strip().lower() for p in protos_input.split(",") if p.strip()]
    protos = [p for p in protos if p in PROTOCOLS]
    if not protos:
        console.print(f"[{C_DANGER}]Hich protocol-e motabar-i nadadi.[/]")
        prompts.pause(); return

    console.print(f"\n[{C_INFO}]{t('br_will_create', d, n=total, c=len(selected))}[/]")
    if not prompts.confirm(t("continue_q", d), default=True):
        return

    route_id = f"rt-{entry_port}"
    route = Route(id=route_id, entry_port=entry_port, mode="balanced")
    channels: list[Channel] = []

    for node_name in selected:
        for i in range(per_node):
            idx = state.next_channel_index(st, route_id, node_name) + i
            proto = protos[(i) % len(protos)]
            bind_port = net.random_free_port(d.port_range_start, d.port_range_end)
            token = _random_token(d.token_length)
            remote_port = 20000 + (entry_port % 10000) + idx
            iperf_port = 55000 + (entry_port % 10000) + idx

            ch = Channel(
                route_id=route_id, node=node_name, index=idx, proto=proto,
                bind_port=bind_port, token=token,
                remote_port=remote_port, target_port=entry_port,
                iperf_port=iperf_port,
            )
            _write_server_channel(ch, d)
            state.add_channel(st, ch)
            channels.append(ch)
            route.channels.append(ch.name)
            net.ufw_allow(bind_port, "udp" if proto in ("kcp", "quic") else "tcp")
            net.ufw_allow(bind_port, "tcp")

    state.add_route(st, route)
    state.save(st)

    _rebuild_haproxy(st, d)

    console.print(f"\n[{C_SUCCESS}]{t('br_created', d)}[/]")
    for ch in channels:
        console.print(f"  [{C_KHAREJ}]{ch.name}[/]  bind={ch.bind_port}")
    console.print(f"[{C_INFO}]{t('br_haproxy_rebuilt', d, n=len(channels))}[/]")
    prompts.pause()


# ═══════════════════════════════════════════════════════════════════════════
#  Manage Routes & Channels
# ═══════════════════════════════════════════════════════════════════════════

def render_routes_table(routes: list[Route], st: dict) -> None:
    if not routes:
        console.print("[yellow]Hich route-i vojood nadare.\n[/]")
        return
    tbl = Table(title="Routes", show_lines=True, box=box.ROUNDED)
    tbl.add_column("ID", style="cyan bold")
    tbl.add_column("Port", justify="right", style="yellow")
    tbl.add_column("Mode", style="magenta")
    tbl.add_column("Nodes", style="green")
    tbl.add_column("Channels", justify="right")
    tbl.add_column("Online", justify="right", style="bright_green")
    for r in routes:
        chs = [state.get_channel(st, cn) for cn in r.channels]
        chs = [c for c in chs if c]
        nodes = sorted({c.node for c in chs})
        online = sum(1 for c in chs if systemd.is_active(c.frps_service))
        tbl.add_row(
            r.id, str(r.entry_port), r.mode,
            ",".join(nodes) if nodes else "\u2014",
            str(len(chs)), f"{online}/{len(chs)}",
        )
    console.print(tbl)



def manage_channels(st: dict, d: Defaults, loc: str) -> None:
    """Manage individual channels.

    On IRAN: full control (list/restart/stop/logs/edit/delete/test).
    On KHAREJ: local control (no delete — that's from Iran).
    """
    is_iran = loc == "IRAN"

    while True:
        render_top_header(version=APP_VERSION, width=MIN_WIDTH)
        channels = state.list_channels(st)

        if not channels:
            console.print(
                f"[{C_WARNING}]Hich channel-i vojood nadare.[/]"
            )
            console.print(
                f"[{C_MUTED}]Baraye sakht: Menu [2] Wizard ya [4]/[5] Route[/]"
                if is_iran else
                f"[{C_MUTED}]Baraye sakht: rooye IRAN compact besaz, "
                f"bad rooye inja [8] Import kon.[/]"
            )
            prompts.pause()
            return

        # ─── Header panel ───
        online = 0
        for ch in channels:
            svc = ch.frps_service if is_iran else ch.frpc_service
            if systemd.is_active(svc):
                online += 1

        console.print(
            Panel(
                Text.from_markup(
                    f"[bold {C_INFO}]\U0001f4e1 Channel Management "
                    f"[{C_MUTED}]({online}/{len(channels)} online)[/][/]\n\n"
                    f"  [{C_MUTED}]Server role: "
                    f"[bold {C_IRAN if is_iran else C_KHAREJ}]"
                    f"{'IRAN (frps)' if is_iran else 'KHAREJ (frpc)'}[/][/]\n"
                    f"  [{C_MUTED}]Hame operations baraye channel-haye "
                    f"{'frps' if is_iran else 'frpc'} rooye hamin server ast.[/]"
                ),
                border_style=C_IRAN if is_iran else C_KHAREJ,
                box=box.ROUNDED,
                padding=(0, 1),
            )
        )
        console.print()

        # ─── Channel table ───
        tbl = Table(show_lines=False, box=box.ROUNDED)
        tbl.add_column("#", style="dim", width=3)
        tbl.add_column("Channel", style="cyan bold")
        tbl.add_column("Proto", style="magenta")
        tbl.add_column("Node" if is_iran else "HUB", style="yellow")
        tbl.add_column("Port", justify="right")
        tbl.add_column("Status", justify="center")

        for i, ch in enumerate(channels, 1):
            svc = ch.frps_service if is_iran else ch.frpc_service
            active = systemd.is_active(svc)

            # Port to display depends on role:
            #   IRAN  → bind_port (frps listens here)
            #   KHAREJ → target_port (frpc forwards to here)
            port_to_show = ch.bind_port if is_iran else ch.target_port
            peer_label = ch.node if is_iran else ch.node  # both show same

            if active:
                status = f"[{C_SUCCESS}]\u25cf ON[/]"
            else:
                status = f"[{C_DANGER}]\u25cb OFF[/]"

            tbl.add_row(
                str(i),
                ch.name,
                ch.proto.upper(),
                peer_label,
                str(port_to_show),
                status,
            )
        console.print(tbl)
        console.print()

        # ─── Menu ───
        console.print(f"[{C_INFO}]1[/] View full details of a channel")
        console.print(f"[{C_INFO}]2[/] Restart a channel")
        console.print(f"[{C_INFO}]3[/] Stop / Start a channel")
        console.print(f"[{C_INFO}]4[/] View live logs (tail -f)")
        console.print(f"[{C_INFO}]5[/] Edit config manually")
        console.print(f"[{C_INFO}]6[/] Test throughput (iperf3)")
        console.print(f"[{C_INFO}]7[/] Check health of one channel")
        console.print(f"[{C_DANGER}]8[/] Delete a channel")
        if is_iran:
            console.print(f"[{C_INFO}]9[/] Rebuild HAProxy")
        console.print(f"[{C_MUTED}]0[/] {t('back', d)}")
        console.print()

        choice = prompts.ask(t("choose", d), "").lower()

        if choice == "0":
            return
        if choice == "1":
            _channel_view(st, d, channels, is_iran)
        elif choice == "2":
            _channel_restart(st, d, channels, is_iran)
        elif choice == "3":
            _channel_toggle(st, d, channels, is_iran)
        elif choice == "4":
            _channel_logs(st, d, channels, is_iran)
        elif choice == "5":
            _channel_edit(st, d, channels, is_iran)
        elif choice == "6":
            _channel_iperf(st, d, channels, is_iran)
        elif choice == "7":
            _channel_health(st, d, channels, is_iran)
        elif choice == "8":
            _channel_delete(st, d, channels, is_iran)
        elif choice == "9" and is_iran:
            _rebuild_haproxy(st, d)
            prompts.pause()
        else:
            console.print(f"[{C_DANGER}]{t('invalid', d)}[/]")
            prompts.pause()


# ─── Helper functions ───

def _pick_channel(channels: list[Channel]) -> "Channel | None":
    """Prompt user to choose one channel."""
    names = [ch.name for ch in channels]
    sel = prompts.choose("Channel ra entekhab kon", names)
    if not sel:
        return None
    for ch in channels:
        if ch.name == sel:
            return ch
    return None


def _channel_view(st: dict, d: Defaults,
                  channels: list[Channel], is_iran: bool) -> None:
    ch = _pick_channel(channels)
    if not ch:
        return

    svc = ch.frps_service if is_iran else ch.frpc_service
    active = systemd.is_active(svc)

    console.print()
    console.print(f"[bold {C_INFO}]Channel details:[/]")
    console.print(f"  [{C_MUTED}]Name[/]      : [{C_KHAREJ}]{ch.name}[/]")
    console.print(f"  [{C_MUTED}]Route[/]     : [{C_INFO}]{ch.route_id}[/]")
    console.print(f"  [{C_MUTED}]Node[/]      : {ch.node}")
    console.print(f"  [{C_MUTED}]Protocol[/]  : [{C_ACCENT}]{ch.proto.upper()}[/]")
    console.print(f"  [{C_MUTED}]Index[/]     : {ch.index}")
    console.print()
    console.print(f"  [{C_MUTED}]Bind port[/]    (rooye Iran)  : {ch.bind_port}")
    console.print(f"  [{C_MUTED}]Remote port[/]  (rooye Kharej): {ch.remote_port}")
    console.print(f"  [{C_MUTED}]Target port[/]  (Xray rooye kharej): {ch.target_port}")
    console.print(f"  [{C_MUTED}]iPerf port[/]  : {ch.iperf_port}")
    console.print()
    console.print(f"  [{C_MUTED}]Service[/]   : {svc}")
    console.print(f"  [{C_MUTED}]Status[/]    : "
                  f"[{C_SUCCESS}]ACTIVE[/]" if active
                  else f"[{C_DANGER}]INACTIVE[/]")
    console.print()
    prompts.pause()


def _channel_restart(st: dict, d: Defaults,
                     channels: list[Channel], is_iran: bool) -> None:
    ch = _pick_channel(channels)
    if not ch:
        return
    svc = ch.frps_service if is_iran else ch.frpc_service
    systemd.service_action(svc, "restart")
    console.print(f"[{C_SUCCESS}]\u2713 {ch.name} restarted[/]")
    prompts.pause()


def _channel_toggle(st: dict, d: Defaults,
                    channels: list[Channel], is_iran: bool) -> None:
    ch = _pick_channel(channels)
    if not ch:
        return
    svc = ch.frps_service if is_iran else ch.frpc_service
    active = systemd.is_active(svc)
    if active:
        systemd.service_action(svc, "stop")
        console.print(f"[{C_WARNING}]\u25cb {ch.name} stopped[/]")
    else:
        systemd.service_action(svc, "start")
        console.print(f"[{C_SUCCESS}]\u25cf {ch.name} started[/]")
    prompts.pause()


def _channel_logs(st: dict, d: Defaults,
                  channels: list[Channel], is_iran: bool) -> None:
    ch = _pick_channel(channels)
    if not ch:
        return
    svc = ch.frps_service if is_iran else ch.frpc_service
    console.print(
        f"[{C_MUTED}]Showing last 50 lines of {svc}...[/]\n"
    )
    console.print(systemd.logs(svc, 50))
    console.print()
    if prompts.confirm("Live tail (follow) konam?", default=False):
        console.print(f"[{C_MUTED}](Ctrl+C baraye khoroj)[/]")
        import subprocess as _sp
        try:
            _sp.run(["journalctl", "-u", svc, "-f"])
        except KeyboardInterrupt:
            pass
    prompts.pause()


def _channel_edit(st: dict, d: Defaults,
                  channels: list[Channel], is_iran: bool) -> None:
    ch = _pick_channel(channels)
    if not ch:
        return
    from .constants import CONFIG_DIR
    binary = "frps" if is_iran else "frpc"
    config = CONFIG_DIR / f"{binary}_{ch.name}.toml"
    if not config.exists():
        console.print(f"[{C_DANGER}]Config file peyda nashod: {config}[/]")
        prompts.pause()
        return

    editor = get_editor()
    console.print(f"[{C_INFO}]Opening {config} with {editor}...[/]")
    import subprocess as _sp
    _sp.run([editor, str(config)])

    if prompts.confirm("Service ro restart konam?", default=True):
        svc = ch.frps_service if is_iran else ch.frpc_service
        systemd.service_action(svc, "restart")
        console.print(f"[{C_SUCCESS}]\u2713 Config saved + service restarted[/]")
    prompts.pause()


def _channel_iperf(st: dict, d: Defaults,
                   channels: list[Channel], is_iran: bool) -> None:
    """Test throughput over a channel.

    Auto-detect mode:
      1. If remote side is listening on iperf_port → run CLIENT
      2. If nothing is listening → run SERVER (and wait for remote client)
      3. If local side is already listening → warn

    The user can also force server or client mode.
    """
    import subprocess as _sp
    import json as _json
    import time as _time

    ch = _pick_channel(channels)
    if not ch:
        return

    if not ch.iperf_port:
        console.print(f"[{C_WARNING}]iPerf port baraye in channel tanzim nashode.[/]")
        prompts.pause()
        return

    # ─── What's on our side? ───
    local_listening = not net.is_port_free(ch.iperf_port)

    console.print()
    console.print(f"[bold {C_INFO}]iPerf3 Test: {ch.name}[/]")
    console.print(f"  [{C_MUTED}]iPerf port: {ch.iperf_port}[/]")
    console.print(f"  [{C_MUTED}]Server role: "
                  f"[bold {C_IRAN if is_iran else C_KHAREJ}]"
                  f"{'IRAN' if is_iran else 'KHAREJ'}[/][/]")
    console.print()

    # ─── Detect remote side ───
    console.print(f"[{C_MUTED}]Dar hale check-e ettesal-e remote...[/]")
    remote_reachable = _probe_iperf_remote(ch)

    console.print()

    # ─── Auto-decide ───
    if local_listening:
        console.print(
            f"[{C_WARNING}]\u26a0 iperf3 ham aknun rooye port {ch.iperf_port} "
            f"dar hamin server aktiv ast.[/]"
        )
        console.print(
            f"[{C_MUTED}]  Ehtemalan ye process dige az ghabl run shode.[/]"
        )
        console.print()
        console.print(f"  [{C_INFO}]1[/] Kill kon va dobare run kon")
        console.print(f"  [{C_INFO}]2[/] Client test kon (be hamun port wasl sho)")
        console.print(f"  [{C_MUTED}]0[/] Bargasht")
        ans = prompts.ask("Entekhab", "0")
        if ans == "0":
            return
        if ans == "1":
            _sp.run(["fuser", "-k", f"{ch.iperf_port}/tcp"],
                    capture_output=True)
            _time.sleep(1)
            local_listening = False
        # ans == "2" falls through to client test

    if not local_listening and remote_reachable == "yes":
        # Remote is listening → run CLIENT
        console.print(
            f"[{C_SUCCESS}]\u2713 Remote dar hale listen ast \u2014 "
            f"run CLIENT test[/]"
        )
        _run_iperf_client(ch)
    elif not local_listening and remote_reachable == "no":
        # Nobody listening → run SERVER
        console.print(
            f"[{C_INFO}]Hich kasi listen nemikone \u2014 run SERVER mode[/]"
        )
        console.print(
            f"[{C_MUTED}]  Rooye server-e dige, in channel ra baz kon va "
            f"Menu [9] \u2192 6 ro bezan (khodash client mishe).[/]"
        )
        console.print()
        if prompts.confirm("Server mode rooye hamin server start beshe?",
                            default=True):
            _run_iperf_server(ch)
    else:
        # local_listening True and we chose to run client
        console.print(
            f"[{C_INFO}]Client test be {ch.iperf_port}...[/]"
        )
        _run_iperf_client(ch)

    prompts.pause()


def _probe_iperf_remote(ch: Channel) -> str:
    """Probe whether the remote side has iperf listening.

    Returns:
        "yes"  - remote reachable
        "no"   - remote not reachable
        "unknown" - couldn't determine
    """
    import socket
    # The iperf port is forwarded over the tunnel.
    # On the local machine we can't directly know remote state.
    # Strategy: try to connect to localhost:iperf_port.
    #   - If it succeeds, someone on the other side is likely serving.
    #   - If it fails, nobody is serving locally.
    # (This works because frpc/frps forwards the port locally once the
    #  remote side starts iperf server.)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            result = s.connect_ex(("127.0.0.1", ch.iperf_port))
            return "yes" if result == 0 else "no"
    except Exception:
        return "unknown"


def _run_iperf_server(ch: Channel) -> None:
    """Run iperf3 in server mode with live hints."""
    import subprocess as _sp

    net.ufw_allow(ch.iperf_port)
    console.print()
    console.print(
        f"[{C_SUCCESS}]\u25b6 iperf3 server rooye :{ch.iperf_port} "
        f"(Ctrl+C baraye stop)[/]"
    )
    console.print(
        f"[{C_MUTED}]  Montazer-e client az taraf-e dige hastim...[/]"
    )
    console.print()
    try:
        _sp.run(["iperf3", "-s", "-p", str(ch.iperf_port)])
    except KeyboardInterrupt:
        console.print()
        console.print(f"[{C_MUTED}]Server stopped.[/]")


def _run_iperf_client(ch: Channel) -> None:
    """Run iperf3 client test and pretty-print results."""
    import subprocess as _sp
    import json as _json

    dur = prompts.ask_int("Moddat (sec)", 10, 1, 120)
    streams = prompts.ask_int("Tedad-e stream (parallel)", 4, 1, 32)

    console.print()
    console.print(
        f"[{C_INFO}]Dar hale test... ({dur}s, {streams} stream)[/]"
    )

    cmd = [
        "iperf3",
        "-c", "127.0.0.1",
        "-p", str(ch.iperf_port),
        "-P", str(streams),
        "-t", str(dur),
        "--json",
    ]

    # Run with both stdout and stderr captured
    try:
        r = _sp.run(
            cmd,
            capture_output=True, text=True, timeout=dur + 30,
        )
    except _sp.TimeoutExpired:
        console.print(f"[{C_DANGER}]Timeout \u2014 test cancel shod.[/]")
        return
    except FileNotFoundError:
        console.print(f"[{C_DANGER}]iperf3 nasb nist![/]")
        console.print(f"[{C_MUTED}]  Nasb: apt-get install iperf3[/]")
        return

    # ─── Show command + exit code for debug ───
    console.print(f"[{C_MUTED}]  Command: {' '.join(cmd)}[/]")
    console.print(f"[{C_MUTED}]  Exit code: {r.returncode}[/]")
    console.print()

    # ─── Failure path: show raw output ───
    if r.returncode != 0:
        console.print(f"[{C_DANGER}]\u2717 iPerf fail shod[/]")
        console.print()

        # Try to parse error from stdout (json) or stderr
        err_text = ""
        try:
            data = _json.loads(r.stdout)
            err_text = data.get("error", "") or ""
            if not err_text and "start" in data:
                err_text = data["start"].get("connected", [{}])[0].get("error", "")
        except Exception:
            pass

        if not err_text:
            err_text = r.stderr.strip() or r.stdout.strip()

        if err_text:
            console.print(f"[{C_MUTED}]  Error:[/]")
            for line in err_text.splitlines()[:10]:
                console.print(f"  [{C_DANGER}]{line}[/]")
        else:
            console.print(f"[{C_MUTED}]  (no output from iperf3)[/]")

        console.print()
        console.print(f"[bold {C_INFO}]Diagnosis:[/]")

        # Common causes
        causes = []

        # Check if port is listening locally
        from .system import net as _net
        if _net.is_port_free(ch.iperf_port):
            causes.append(
                f"  [{C_WARNING}]\u2022[/] Port {ch.iperf_port} rooye hamin server "
                f"listen nemikone"
            )
            causes.append(
                f"    [{C_MUTED}]frps iperf port ra baaz nakarde. "
                f"Check kon frpc taraf-e dige iperf ro run karde.[/]"
            )
        else:
            causes.append(
                f"  [{C_SUCCESS}]\u2022[/] Port {ch.iperf_port} listen mikone "
                f"(frps response mide)"
            )
            causes.append(
                f"    [{C_MUTED}]Vali iperf3 server taraf-e dige javab nemide.[/]"
            )
            causes.append(
                f"    [{C_MUTED}]Check kon: rooye taraf-e dige iperf3 -s -p {ch.iperf_port} "
                f"run shode[/]"
            )

        # Check iperf3 binary
        which = _sp.run(["which", "iperf3"], capture_output=True, text=True)
        if which.returncode != 0:
            causes.append(f"  [{C_DANGER}]\u2022[/] iperf3 nasb nist!")
        else:
            causes.append(f"  [{C_SUCCESS}]\u2022[/] iperf3 nasb ast: {which.stdout.strip()}")

        for c in causes:
            console.print(c)

        console.print()
        console.print(f"[bold {C_INFO}]Rahnama:[/]")
        console.print(f"  [{C_MUTED}]1.[/] Rooye taraf-e dige: [bold]Menu [9] \u2192 6[/]"
                      f" \u2192 hamin channel \u2192 [bold]Server mode[/]")
        console.print(f"  [{C_MUTED}]2.[/] Rooye hamin server: [bold]Menu [9] \u2192 6[/]"
                      f" \u2192 hamin channel \u2192 [bold]Client mode[/]")
        console.print()
        return

    # ─── Success path ───
    try:
        data = _json.loads(r.stdout)
    except Exception as e:
        console.print(f"[{C_DANGER}]Natije parse nashod: {e}[/]")
        console.print(f"[{C_MUTED}]stdout: {r.stdout[:300]}[/]")
        return

    try:
        sent = data["end"]["sum_sent"]
        recv = data["end"]["sum_received"]
    except KeyError as e:
        console.print(f"[{C_DANGER}]KeyError: {e}[/]")
        console.print(f"[{C_MUTED}]data: {str(data)[:300]}[/]")
        return

    mbps_sent = sent["bits_per_second"] / 1e6
    mbps_recv = recv["bits_per_second"] / 1e6
    gb_sent = sent["bytes"] / 1e9
    gb_recv = recv["bytes"] / 1e9

    console.print()
    console.print(f"[bold {C_SUCCESS}]\u2501\u2501\u2501 Natije \u2501\u2501\u2501[/]")
    console.print()
    console.print(
        f"  [{C_MUTED}]Channel[/]      : [{C_KHAREJ}]{ch.name}[/]"
    )
    console.print(
        f"  [{C_MUTED}]Protocol[/]     : [{C_ACCENT}]{ch.proto.upper()}[/]"
    )
    console.print(
        f"  [{C_MUTED}]Duration[/]     : {dur}s, {streams} streams"
    )
    console.print()
    console.print(
        f"  [{C_MUTED}]Upload[/]  (^)  : "
        f"[{C_SUCCESS}]{mbps_sent:>8.2f}[/] Mbps  "
        f"[{C_MUTED}]({gb_sent:.2f} GB)[/]"
    )
    console.print(
        f"  [{C_MUTED}]Download[/](v)  : "
        f"[{C_SUCCESS}]{mbps_recv:>8.2f}[/] Mbps  "
        f"[{C_MUTED}]({gb_recv:.2f} GB)[/]"
    )
    console.print()

    if mbps_recv >= 800:
        verdict = f"[{C_SUCCESS}]\u2605 Excellent[/]"
    elif mbps_recv >= 400:
        verdict = f"[{C_SUCCESS}]\u2713 Good[/]"
    elif mbps_recv >= 150:
        verdict = f"[{C_WARNING}]\u26a0 Acceptable[/]"
    elif mbps_recv >= 50:
        verdict = f"[{C_WARNING}]\u26a0 Slow[/]"
    else:
        verdict = f"[{C_DANGER}]\u2717 Very slow[/]"

    console.print(f"  [{C_MUTED}]Verdict[/]      : {verdict}")
    console.print()



def _channel_health(st: dict, d: Defaults,
                    channels: list[Channel], is_iran: bool) -> None:
    ch = _pick_channel(channels)
    if not ch:
        return
    svc = ch.frps_service if is_iran else ch.frpc_service
    active = systemd.is_active(svc)

    console.print()
    console.print(f"[bold {C_INFO}]Health check: {ch.name}[/]")
    console.print()
    console.print(f"  [{C_MUTED}]Service[/]     : {svc}")
    if active:
        console.print(f"  [{C_SUCCESS}]\u2713 ACTIVE[/]")
    else:
        console.print(f"  [{C_DANGER}]\u2717 INACTIVE[/]")
        console.print(f"  [{C_MUTED}]  Check logs: Menu [9] \u2192 4[/]")

    # Check listening port
    port_to_check = ch.bind_port if is_iran else ch.target_port
    listening = not net.is_port_free(port_to_check)
    if listening:
        console.print(f"  [{C_SUCCESS}]\u2713 Port {port_to_check} dar hale listen[/]")
    else:
        console.print(f"  [{C_WARNING}]\u26a0 Port {port_to_check} azad (listen nemikone)[/]")
        if not is_iran:
            console.print(f"  [{C_MUTED}]  Service rooye {ch.target_port} "
                          f"start nashode[/]")

    prompts.pause()


def _channel_delete(st: dict, d: Defaults,
                    channels: list[Channel], is_iran: bool) -> None:
    """Delete a channel.

    On IRAN: remove channel from state + stop frps + delete configs (both).
    On KHAREJ: remove channel from local state + stop frpc + delete frpc config.
                (Iran side is untouched — use Iran to fully remove.)
    """
    from .frp import server as frp_server, client as frp_client

    ch = _pick_channel(channels)
    if not ch:
        return

    console.print()
    console.print(f"[bold {C_DANGER}]\u26a0 Delete channel: {ch.name}[/]")
    console.print(f"  [{C_MUTED}]Route  : {ch.route_id}[/]")
    console.print(f"  [{C_MUTED}]Node   : {ch.node}[/]")
    console.print()

    # ─── Role-specific warning ───
    if is_iran:
        console.print(
            f"  [{C_WARNING}]In action rooye IRAN:[/]"
        )
        console.print(
            f"  [{C_MUTED}]\u2022 frps@ service متوقف و حذف می‌شه[/]"
        )
        console.print(
            f"  [{C_MUTED}]\u2022 frps config پاک می‌شه[/]"
        )
        console.print(
            f"  [{C_MUTED}]\u2022 frpc config (baraye taraf-e kharej) ham pak "
            f"mishe \u2014 vali rooye Kharej ettesal ghate mishe[/]"
        )
        console.print(
            f"  [{C_MUTED}]\u2022 Age route-e balanced bashe, HAProxy rebuild mishe[/]"
        )
    else:
        console.print(
            f"  [{C_WARNING}]In action rooye KHAREJ:[/]"
        )
        console.print(
            f"  [{C_MUTED}]\u2022 frpc@ service متوقف و حذف می‌شه[/]"
        )
        console.print(
            f"  [{C_MUTED}]\u2022 frpc config pak می‌شه[/]"
        )
        console.print(
            f"  [{C_MUTED}]\u2022 Channel faghat az state-e HAMIN server hazf mishe[/]"
        )
        console.print()
        console.print(
            f"  [{C_DANGER}]\u26a0 توجه:[/] [{C_MUTED}]rooye server-e IRAN, "
            f"in channel hanuz vojood dare va frps-e marboote aktiv ast.[/]"
        )
        console.print(
            f"  [{C_MUTED}]  Baraye hazf-e kamel, in channel ra az rooye IRAN ham pak kon.[/]"
        )

    console.print()

    if not prompts.confirm(f"'{ch.name}' pak beshe?", default=False):
        console.print(f"[{C_MUTED}]Cancel shod.[/]")
        return

    # ─── Stop and remove services ───
    if is_iran:
        _stop_channel_services(ch.name)
        frp_server.delete_frps_config(ch)
        frp_client.delete_frpc_config(ch)
    else:
        # Only the local frpc service
        svc = ch.frpc_service
        systemd.remove_unit(svc)
        systemd.daemon_reload()
        frp_client.delete_frpc_config(ch)

    # ─── Remove from state ───
    state.remove_tunnel(st, ch.name) if hasattr(state, "remove_tunnel") \
        else st.get("channels", {}).pop(ch.name, None)

    # ─── Remove from route (on Iran, we own the route) ───
    if is_iran:
        r = state.get_route(st, ch.route_id)
        if r:
            r.channels = [c for c in r.channels if c != ch.name]
            state.add_route(st, r)

            # If route is now empty, remove it too
            if not r.channels:
                console.print(
                    f"[{C_WARNING}]Route '{r.id}' khali shod \u2014 pak mishe[/]"
                )
                state.remove_route(st, r.id)
            elif r.mode == "balanced":
                # Rebuild HAProxy since channel list changed
                _rebuild_haproxy(st, d)

    state.save(st)

    console.print()
    console.print(f"[{C_DANGER}]\u2713 {ch.name} deleted[/]")

    if not is_iran:
        console.print(
            f"[{C_MUTED}]  Yadet bashe ke rooye IRAN ham hazfesh koni "
            f"age nemikhay aktiv bashe.[/]"
        )

    prompts.pause()



def manage_routes(st: dict, d: Defaults) -> None:
    while True:
        render_top_header(version=APP_VERSION, width=MIN_WIDTH)
        routes = state.list_routes(st)
        render_routes_table(routes, st)

        if not routes:
            prompts.pause(); return

        console.print(f"\n[{C_INFO}]1[/] Restart Route")
        console.print(f"[{C_INFO}]2[/] Stop Route")
        console.print(f"[{C_INFO}]3[/] Logs (all channels)")
        console.print(f"[{C_INFO}]4[/] Show channels detail")
        console.print(f"[{C_DANGER}]5[/] Delete Route")
        console.print(f"[{C_MUTED}]h[/] Help")
        console.print(f"[{C_MUTED}]0[/] {t('back', d)}")
        choice = prompts.ask(t("choose", d), "").lower()

        if choice == "0":
            return
        if choice == "h":
            help_ui.show_menu_help("5")
            continue
        if choice not in ("1", "2", "3", "4", "5"):
            console.print(f"[{C_DANGER}]{t('invalid', d)}[/]")
            prompts.pause(); continue

        sel = prompts.choose(t("mr_select", d), [r.id for r in routes])
        if not sel:
            continue
        route = state.get_route(st, sel)
        assert route
        chs = [state.get_channel(st, cn) for cn in route.channels]
        chs = [c for c in chs if c]

        if choice in ("1", "2"):
            action = "restart" if choice == "1" else "stop"
            for c in chs:
                systemd.service_action(c.frps_service, action)
            console.print(f"[{C_SUCCESS}]Route {sel} {action}ed ({len(chs)} channels).[/]")
            prompts.pause()
        elif choice == "3":
            for c in chs:
                console.print(f"\n[{C_INFO}]───── {c.name} ─────[/]")
                console.print(systemd.logs(c.frps_service, 20))
            prompts.pause()
        elif choice == "4":
            tbl = Table(show_lines=False, box=box.SIMPLE)
            tbl.add_column("Channel", style="cyan")
            tbl.add_column("Node", style="yellow")
            tbl.add_column("Proto", style="magenta")
            tbl.add_column("Bind", justify="right")
            tbl.add_column("Remote", justify="right")
            tbl.add_column("Target", justify="right")
            tbl.add_column("Status")
            for c in chs:
                st_txt = (
                    f"[{C_SUCCESS}]ONLINE[/]" if systemd.is_active(c.frps_service)
                    else f"[{C_DANGER}]OFFLINE[/]"
                )
                tbl.add_row(c.name, c.node, c.proto, str(c.bind_port),
                            str(c.remote_port), str(c.target_port), st_txt)
            console.print(tbl)
            prompts.pause()
        elif choice == "5":
            if not prompts.confirm(f"Delete route '{sel}' ({len(chs)} channels)?",
                                   default=False):
                continue
            for c in chs:
                _stop_channel_services(c.name)
                frp_server.delete_frps_config(c)
                frp_client.delete_frpc_config(c)
            state.remove_route(st, sel)
            state.save(st)
            if route.mode == "balanced":
                _rebuild_haproxy(st, d)
            console.print(f"[{C_DANGER}]{t('mr_deleted', d, r=sel, n=len(chs))}[/]")
            prompts.pause()


# ═══════════════════════════════════════════════════════════════════════════
#  Export / Import
# ═══════════════════════════════════════════════════════════════════════════

def export_for_node(st: dict, d: Defaults, loc: str) -> None:
    """Export compact for a specific hub (or all hubs)."""
    logo.show(t("logo_sub", d))

    if loc != "IRAN":
        console.print(f"[{C_KHAREJ}]Export faghat rooye IRAN anjam mishe.[/]")
        prompts.pause()
        return

    hubs = state.list_hubs(st)
    if not hubs:
        console.print(f"[{C_DANGER}]Hich Hub-i nadari. Aval menu [3] yek Hub add kon.[/]")
        prompts.pause()
        return

    # ─── Select hub ───
    hub_names = [h.name for h in hubs]
    sel = prompts.choose("Kodoom Hub?", hub_names)
    if not sel:
        return

    hub = state.get_hub(st, sel)
    if not hub:
        return

    channels = state.list_channels(st, hub=sel)
    if not channels:
        console.print(f"[{C_DANGER}]Hich channel-i baraye in Hub nist.[/]")
        prompts.pause()
        return

    # ─── Hub IP from our own public IP ───
    hub_ip = net.detect_public_ip() or ""

    # ─── Export ───
    from .frp import compact as _compact
    path = _compact.export_channels(channels, hub_name=hub.name, hub_ip=hub_ip)

    console.clear()
    console.print()
    console.print(Panel(
        Text.from_markup(
            f"[bold {C_SUCCESS}]\u2705 Export kamel shod[/]\n\n"
            f"  [{C_MUTED}]Hub:      [/][bold {C_IRAN}]{hub.name}[/]\n"
            f"  [{C_MUTED}]Hub IP:   [/][bold {C_CYAN}]{hub_ip}[/]\n"
            f"  [{C_MUTED}]Channels: [/][bold {C_INFO}]{len(channels)}[/]\n"
            f"  [{C_MUTED}]Type:     [/][bold {C_WARNING}]{hub.type}[/]\n"
            f"  [{C_MUTED}]File:     [/][{C_CYAN}]{path}[/]"
        ),
        border_style=C_SUCCESS,
        box=box.ROUNDED,
        padding=(0, 1),
        width=MIN_WIDTH,
    ))
    console.print()

    # ─── Show content ───
    console.print(f"[bold {C_INFO}]Compact {hub.name}:[/]")
    console.print(f"[{C_MUTED}]" + "\u2500" * (MIN_WIDTH - 4) + "[/]")
    console.print()
    console.print(path.read_text())
    console.print(f"[{C_MUTED}]" + "\u2500" * (MIN_WIDTH - 4) + "[/]")
    console.print()

    # ─── Next steps ───
    console.print(f"[bold {C_WARNING}]Ghadam-haye badi:[/]")
    console.print(f"  [{C_INFO}]1.[/] In line-ha ro copy kon")
    console.print(f"  [{C_INFO}]2.[/] Vared-e server-e kharej ([bold]{hub.name}[/]) sho")
    console.print(f"  [{C_INFO}]3.[/] Menu [8] → Import az Hub")
    console.print(f"  [{C_INFO}]4.[/] Line-ha ro paste kon, Enter-e khali bezan")

    prompts.pause()



def import_on_node(st: dict, d: Defaults, loc: str) -> None:
    """Import compact from Hub.

    Smart detection:
      - 1 channel -> Simple Hub
      - N channels -> Balanced Hub
      - Existing Hub name -> auto-append number (iran-1 -> iran-1-2)
    """
    logo.show(t("logo_sub", d))

    if loc != "KHAREJ":
        console.print(f"[{C_IRAN}]Import faghat rooye KHAREJ anjam mishe.[/]")
        prompts.pause()
        return

    # ─── Info ───
    console.print(Panel(
        Text.from_markup(
            f"[bold {C_INFO}]\U0001f4e5  Import az Hub[/]\n\n"
            f"  [{C_MUTED}]Compact-e sakhte shode rooye server-e IRAN ra paste kon.[/]\n"
            f"  [{C_MUTED}]Ba'd az paste, Enter-e khali bezan ta payan.[/]"
        ),
        border_style=C_INFO,
        box=box.ROUNDED,
        padding=(0, 1),
        width=MIN_WIDTH,
    ))
    console.print()

    # ─── Paste lines ───
    lines: list[str] = []
    while True:
        line = prompts.ask("", allow_empty=True)
        if not line:
            break
        lines.append(line)

    if not lines:
        console.print(f"[{C_DANGER}]Hich line-i paste nakardi.[/]")
        prompts.pause()
        return

    full_text = "\n".join(lines)

    # ─── Parse compact ───
    from .frp import compact as _compact
    result = _compact.parse_compact(full_text)

    if not result["lines"]:
        console.print(f"[{C_DANGER}]Hich channel-e motabar-i peyda nashod.[/]")
        if result["errors"]:
            console.print()
            console.print(f"[{C_WARNING}]Errors:[/]")
            for e in result["errors"][:5]:
                console.print(f"  [{C_MUTED}]{e}[/]")
        prompts.pause()
        return

    meta = result["meta"]
    parsed_lines = result["lines"]

    # ─── Show preview ───
    console.print()
    console.print(Panel(
        Text.from_markup(
            f"[bold {C_SUCCESS}]\U0001f50d  Detected:[/]\n\n"
            f"  [{C_MUTED}]Hub Name:     [/][bold {C_IRAN}]{meta['hub_name']}[/]\n"
            f"  [{C_MUTED}]Hub IP:       [/][bold {C_IRAN}]{meta['hub_ip'] or 'unknown'}[/]\n"
            f"  [{C_MUTED}]Type:         [/][bold {C_WARNING}]{meta['type'].upper()}[/]\n"
            f"  [{C_MUTED}]Channels:     [/][bold {C_INFO}]{meta['channels_count']}[/]\n"
            f"  [{C_MUTED}]Routes:       [/][bold {C_INFO}]{sorted({item['channel'].target_port for item in parsed_lines})}[/]"
        ),
        border_style=C_SUCCESS,
        box=box.ROUNDED,
        padding=(0, 1),
        width=MIN_WIDTH,
    ))
    console.print()

    # ─── Handle existing hub name ───
    hub_name = meta["hub_name"]
    hub_ip = meta["hub_ip"]

    existing_hub = state.get_hub(st, hub_name)
    if existing_hub:
        # Ask user: append number or reuse?
        console.print(f"[{C_WARNING}]Hub '{hub_name}' ghablan vojud dare (IP: {existing_hub.host})[/]")
        console.print()
        console.print(f"  [{C_INFO}]1[/] Reuse (channel-ha ro be in hub-e mojood add kon)")
        console.print(f"  [{C_INFO}]2[/] Rename (esm-e jadid besaz)")
        console.print(f"  [{C_MUTED}]0[/] Cancel")

        choice = prompts.ask("Entekhab", "1")

        if choice == "0":
            return
        elif choice == "2":
            new_name = prompts.ask(
                f"Esm-e jadid baraye Hub",
                default=f"{hub_name}-2",
            )
            hub_name = new_name
            # Update channel.hub for all
            for item in parsed_lines:
                item["channel"].hub = hub_name
            meta["hub_name"] = hub_name

    # ─── Ask for IP if missing ───
    if not hub_ip:
        hub_ip = prompts.ask(
            f"[{C_INFO}]IP server-e IRAN (Hub)[/]"
        )

    # ─── Create or get hub ───
    if not state.get_hub(st, hub_name):
        hub = Hub(
            name=hub_name,
            host=hub_ip,
            location="IRAN",
            note="",
            type=meta["type"],
            routes=sorted({item["channel"].target_port for item in parsed_lines}),
        )
        state.add_hub(st, hub)
        console.print(f"[{C_SUCCESS}]\u2713 Hub '{hub_name}' created[/]")
    else:
        hub = state.get_hub(st, hub_name)
        console.print(f"[{C_SUCCESS}]\u2713 Using existing Hub '{hub_name}'[/]")

    # ─── Add channels ───
    added = []
    skipped = []

    for item in parsed_lines:
        ch = item["channel"]
        # Ensure hub name is correct
        ch.hub = hub_name

        # Check if channel already exists
        if state.get_channel(st, ch.name):
            skipped.append(ch.name)
            continue

        # Write frpc config (Kharej side)
        _write_client_channel(ch, hub, d)
        state.add_channel(st, ch)
        added.append(ch.name)

        # Add route if not exists
        route = state.get_route(st, ch.route_id)
        if not route:
            route = Route(
                id=ch.route_id,
                entry_port=ch.target_port,
                mode=meta["type"],
                channels=[],
            )
        if ch.name not in route.channels:
            route.channels.append(ch.name)
        state.add_route(st, route)

    state.save(st)

    # ─── Summary ───
    console.print()
    console.print(f"[{C_SUCCESS}]\u2713 Import kamel shod[/]")
    console.print(f"  [{C_MUTED}]Added channels:   [/][{C_SUCCESS}]{len(added)}[/]")
    if skipped:
        console.print(f"  [{C_MUTED}]Skipped (exists): [/][{C_WARNING}]{len(skipped)}[/]")
    console.print()

    for cname in added:
        console.print(f"  [{C_KHAREJ}]{cname}[/]")

    prompts.pause()



def health_check(st: dict, d: Defaults, loc: str) -> None:
    render_top_header(version=APP_VERSION, width=MIN_WIDTH)
    channels = state.list_channels(st)
    if not channels:
        console.print(f"[yellow]{t('health_no_tunnels', d)}[/]")
        prompts.pause(); return

    tbl = Table(title="Health", show_lines=False, box=box.ROUNDED)
    tbl.add_column("Channel", style="cyan")
    tbl.add_column("Node", style="yellow")
    tbl.add_column("Role")
    tbl.add_column("Service")
    tbl.add_column("Bind Port")
    tbl.add_column("Target Port")
    for ch in channels:
        role = "server" if loc == "IRAN" else "client"
        svc = ch.frps_service if loc == "IRAN" else ch.frpc_service
        svc_st = (
            f"[{C_SUCCESS}]● active[/]" if systemd.is_active(svc)
            else f"[{C_DANGER}]○ down[/]"
        )
        listen_st = (
            f"[{C_SUCCESS}]● listening[/]" if not net.is_port_free(ch.bind_port)
            else f"[{C_MUTED}]○ free[/]"
        )
        tbl.add_row(ch.name, ch.node, role, svc_st, listen_st,
                    str(ch.target_port))
    console.print(tbl)
    prompts.pause()


def speedtest(st: dict, d: Defaults, loc: str) -> None:
    """Run iperf3 speedtest. Loops until user chooses Back."""
    import json
    import subprocess as _sp

    # Loop تا کاربر Back بزنه
    while True:
        logo.show(t("logo_sub", d))

        channels = state.list_channels(st)
        if not channels:
            console.print(f"[yellow]{t('speed_no_tunnels', d)}[/]")
            prompts.pause()
            return

        # ─── Channel selection with Back option ───
        console.print()
        console.print(f"[bold {C_INFO}]Speedtest — Channel ra entekhab kon:[/]")
        console.print(f"[{C_MUTED}]Baraye bargasht, 0 bezan.[/]")
        console.print()

        channel_choices = [
            f"{c.name}  [{c.proto.upper()}]"
            for c in channels
        ]
        channel_choices.append("0  ← Back")

        sel_display = prompts.choose(t("speed_select", d), channel_choices)
        if not sel_display or sel_display.startswith("0"):
            return

        # Extract channel name
        sel = sel_display.split("  [")[0].strip()
        ch = state.get_channel(st, sel)
        if not ch:
            console.print(f"[{C_DANGER}]Channel '{sel}' not found[/]")
            prompts.pause()
            continue

        # ─── Mode selection ───
        console.print()
        console.print(f"[bold {C_INFO}]Channel:[/] [{C_KHAREJ}]{ch.name}[/]  "
                      f"[{C_MUTED}]Protocol:[/] [{C_ACCENT}]{ch.proto.upper()}[/]  "
                      f"[{C_MUTED}]iPerf port:[/] {ch.iperf_port}")
        console.print()

        # Default mode depends on location
        if loc == "IRAN":
            default_mode = "2"
            mode_hint = "pishnahad: 2 (Client test rooye IRAN)"
        else:
            default_mode = "1"
            mode_hint = "pishnahad: 1 (Server mode rooye KHAREJ)"

        console.print(f"  [{C_INFO}]1[/] {t('speed_mode_srv', d)}")
        console.print(f"  [{C_INFO}]2[/] {t('speed_mode_cli', d)}")
        console.print(f"  [{C_MUTED}]0[/] Back")
        console.print()
        console.print(f"  [{C_MUTED}]{mode_hint}[/]")
        console.print()

        mode = prompts.ask(t("speed_mode", d), default_mode)

        if mode == "0":
            continue

        if mode == "1":
            # ─── Server mode ───
            net.ufw_allow(ch.iperf_port)
            console.print()
            console.print(
                f"[{C_SUCCESS}]{t('speed_starting_srv', d, p=ch.iperf_port)}[/]"
            )
            console.print(f"[{C_MUTED}]CTRL+C = stop[/]")
            console.print()
            try:
                _sp.run(["iperf3", "-s", "-p", str(ch.iperf_port)])
            except KeyboardInterrupt:
                console.print(f"\n[{C_MUTED}]Server stopped.[/]")
            prompts.pause()

        else:
            # ─── Client test ───
            dur = prompts.ask_int(t("speed_duration", d), 10, 1, 120)
            console.print()
            console.print(f"[{C_INFO}]{t('speed_testing', d, name=ch.name)}[/]")

            r = _sp.run(
                ["iperf3", "-c", "127.0.0.1", "-p", str(ch.iperf_port),
                 "-P", "8", "-t", str(dur), "--json"],
                capture_output=True, text=True,
            )
            try:
                data = json.loads(r.stdout)
                mbps = data["end"]["sum_received"]["bits_per_second"] / 1e6

                console.print()
                console.print(f"[bold {C_SUCCESS}]━━━ Natije ━━━[/]")
                console.print()
                console.print(f"  [{C_MUTED}]Channel[/]     : [{C_KHAREJ}]{ch.name}[/]")
                console.print(f"  [{C_MUTED}]Protocol[/]    : [{C_ACCENT}]{ch.proto.upper()}[/]")
                console.print(f"  [{C_MUTED}]Duration[/]    : {dur}s, 8 streams")
                console.print()
                console.print(f"  [{C_MUTED}]Throughput[/]  : "
                              f"[{C_SUCCESS}]{mbps:.2f} Mbps[/]")
                console.print()

                # Verdict
                if mbps >= 800:
                    verdict = f"[{C_SUCCESS}]★ Excellent[/]"
                elif mbps >= 400:
                    verdict = f"[{C_SUCCESS}]✓ Good[/]"
                elif mbps >= 150:
                    verdict = f"[{C_WARNING}]⚠ Acceptable[/]"
                elif mbps >= 50:
                    verdict = f"[{C_WARNING}]⚠ Slow[/]"
                else:
                    verdict = f"[{C_DANGER}]✗ Very slow[/]"
                console.print(f"  [{C_MUTED}]Verdict[/]     : {verdict}")
                console.print()
            except Exception:
                console.print(f"[{C_DANGER}]{t('speed_failed', d, e=r.stderr[:200])}[/]")

            prompts.pause()
        # Loop continues → back to channel selection


def optimize_menu(st: dict, d: Defaults, loc: str) -> None:
    render_top_header(version=APP_VERSION, width=MIN_WIDTH)
    console.print(f"[{C_INFO}]1[/] {t('opt_tcp', d)}")
    console.print(f"[{C_INFO}]2[/] {t('opt_udp', d)}")
    console.print(f"[{C_INFO}]3[/] {t('opt_all', d)}")
    console.print(f"[{C_MUTED}]0[/] {t('back', d)}")
    c = prompts.ask(t("choose", d), "")
    if c == "1":
        optimize.optimize_tcp()
        console.print(f"[{C_SUCCESS}]{t('opt_tcp_done', d)}[/]")
    elif c == "2":
        optimize.optimize_udp()
        console.print(f"[{C_SUCCESS}]{t('opt_udp_done', d)}[/]")
    elif c == "3":
        optimize.optimize_all()
        console.print(f"[{C_SUCCESS}]{t('opt_all_done', d)}[/]")
    else:
        return
    prompts.pause()


def backup_restore(st: dict, d: Defaults, loc: str) -> None:
    import shutil
    from datetime import datetime
    from .constants import BACKUP_DIR, STATE_FILE, CONFIG_DIR

    render_top_header(version=APP_VERSION, width=MIN_WIDTH)
    console.print(f"[{C_INFO}]1[/] {t('bak_create', d)}")
    console.print(f"[{C_INFO}]2[/] {t('bak_restore', d)}")
    console.print(f"[{C_INFO}]3[/] {t('bak_list', d)}")
    console.print(f"[{C_MUTED}]0[/] {t('back', d)}")
    c = prompts.ask(t("choose", d), "")

    if c == "1":
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = BACKUP_DIR / f"backup_{stamp}"
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy(STATE_FILE, dest / "state.json")
        shutil.copytree(CONFIG_DIR, dest / "configs", dirs_exist_ok=True)
        if HAPROXY_CFG.exists():
            shutil.copy(HAPROXY_CFG, dest / "haproxy-agg.cfg")
        console.print(f"[{C_SUCCESS}]{t('bak_saved', d, p=dest)}[/]")
    elif c == "2":
        baks = sorted(BACKUP_DIR.glob("backup_*"))
        if not baks:
            console.print(f"[{C_DANGER}]{t('bak_none', d)}[/]")
        else:
            console.print(f"Latest: {baks[-1]}")
            if prompts.confirm(t("bak_restore_q", d), default=False):
                shutil.copy(baks[-1] / "state.json", STATE_FILE)
                if (baks[-1] / "configs").exists():
                    shutil.copytree(baks[-1] / "configs", CONFIG_DIR,
                                    dirs_exist_ok=True)
                new_st = state.load()
                st.clear(); st.update(new_st)
                console.print(f"[{C_SUCCESS}]{t('bak_restored', d)}[/]")
    elif c == "3":
        for b in sorted(BACKUP_DIR.glob("backup_*")):
            console.print(f"  [{C_KHAREJ}]{b.name}[/]")
    else:
        return
    prompts.pause()


def reset_menu(st: dict, d: Defaults, loc: str) -> None:
    render_top_header(version=APP_VERSION, width=MIN_WIDTH)
    console.print(f"[{C_DANGER}]╔══════════════════════════════════════════════════╗[/]")
    console.print(f"[{C_DANGER}]║   ⚠  {t('reset_warning', d):<43}║[/]")
    console.print(f"[{C_DANGER}]╚══════════════════════════════════════════════════╝[/]\n")
    console.print(f"[{C_DANGER}]1[/] {t('reset_all_tunnels', d)}")
    console.print(f"[{C_DANGER}]2[/] {t('reset_haproxy_only', d)}")
    console.print(f"[{C_DANGER}]3[/] {t('reset_full', d)}")
    console.print(f"[{C_MUTED}]0[/] {t('back', d)}")
    c = prompts.ask(t("choose", d), "")

    if c == "1":
        if not prompts.confirm(t("reset_all_tunnels_q", d), default=False):
            return
        for ch in state.list_channels(st):
            _stop_channel_services(ch.name)
            frp_server.delete_frps_config(ch)
            frp_client.delete_frpc_config(ch)
        st["channels"] = {}
        st["routes"] = {}
        state.save(st)
        console.print(f"[{C_DANGER}]{t('reset_all_done', d)}[/]")
    elif c == "2":
        hap_svc.disable()
        if HAPROXY_CFG.exists():
            HAPROXY_CFG.unlink()
        console.print(f"[{C_DANGER}]{t('reset_haproxy_done', d)}[/]")
    elif c == "3":
        if not prompts.confirm(t("reset_full_q", d), default=False):
            return
        for ch in state.list_channels(st):
            _stop_channel_services(ch.name)
        hap_svc.disable()
        from .constants import CONFIG_DIR
        for f in CONFIG_DIR.glob("*.toml"):
            f.unlink()
        if HAPROXY_CFG.exists():
            HAPROXY_CFG.unlink()
        state.remove_all(st)
        state.save(st)
        console.print(f"[{C_DANGER}]{t('reset_full_done', d)}[/]")
    else:
        return
    prompts.pause()


def lang_menu(st: dict, d: Defaults, loc: str) -> None:
    render_top_header(version=APP_VERSION, width=MIN_WIDTH)
    console.print(f"{t('lang_current', d)}: [bright_yellow]{d.ui_lang}[/]\n")
    console.print(f"[{C_INFO}]1[/] Finglish")
    console.print(f"[{C_INFO}]2[/] English")
    console.print(f"[{C_MUTED}]0[/] {t('back', d)}")
    c = prompts.ask(t("choose", d), "")
    if c == "1":
        d.ui_lang = "finglish"; save_defaults(d)
        console.print(f"[{C_SUCCESS}]{t('lang_set', d, lang='Finglish')}[/]")
    elif c == "2":
        d.ui_lang = "english"; save_defaults(d)
        console.print(f"[{C_SUCCESS}]{t('lang_set', d, lang='English')}[/]")
    else:
        return
    prompts.pause()


def install_frp(d: Defaults) -> None:
    render_top_header(version=APP_VERSION, width=MIN_WIDTH)
    if not installer.is_installed() or prompts.confirm(
            t("install_already_q", d), default=False):
        installer.install_dependencies()
        installer.download_frp()
    frp_server.write_frps_unit()
    frp_client.write_frpc_unit()
    systemd.daemon_reload()

    installed = get_installed_frp_version("frps")
    if installed:
        console.print(f"[{C_SUCCESS}]{t('install_ready', d, v=installed)}[/]")
    else:
        console.print(f"[{C_DANGER}]{t('install_failed', d)}[/]")
    prompts.pause()


# ═══════════════════════════════════════════════════════════════════════════
#  Internal helpers
# ═══════════════════════════════════════════════════════════════════════════

def _write_server_channel(ch: Channel, d: Defaults) -> None:
    frp_server.write_frps_unit()
    frp_server.write_frps_config(
        ch, max_pool=d.max_pool_count,
        tcpmux=d.tcpmux, heartbeat_timeout=d.heartbeat_timeout,
    )
    systemd.daemon_reload()
    systemd.service_action(ch.frps_service, "enable")
    systemd.service_action(ch.frps_service, "restart")


def _write_client_channel(ch: Channel, node: Node, d: Defaults) -> None:
    frp_client.write_frpc_unit()
    frp_client.write_frpc_config(
        ch, node, pool_count=d.pool_count,
        tcpmux=d.tcpmux,
        heartbeat_interval=d.heartbeat_interval,
        heartbeat_timeout=d.heartbeat_timeout,
    )
    systemd.daemon_reload()
    systemd.service_action(ch.frpc_service, "enable")
    systemd.service_action(ch.frpc_service, "restart")


def _stop_channel_services(name: str) -> None:
    """Force-stop and remove both frps and frpc for a channel.

    Steps:
      1. systemctl stop + disable (works even if unit file exists)
      2. kill orphan processes (matches config file path)
      3. remove unit file
      4. remove config file
      5. daemon-reload + reset-failed
    """
    import subprocess as _sp
    from .constants import CONFIG_DIR, SYSTEMD_DIR

    for binary in ("frps", "frpc"):
        unit = f"{binary}@{name}.service"
        config = CONFIG_DIR / f"{binary}_{name}.toml"
        unit_file = SYSTEMD_DIR / unit

        # 1) Stop + disable
        _sp.run(["systemctl", "stop", unit],
                capture_output=True, timeout=15)
        _sp.run(["systemctl", "disable", unit],
                capture_output=True, timeout=15)

        # 2) Kill orphan processes by config file path
        _sp.run(["pkill", "-9", "-f", str(config)],
                capture_output=True)

        # 3) Remove unit file
        if unit_file.exists():
            try:
                unit_file.unlink()
            except Exception:
                pass

        # 4) Remove config file
        if config.exists():
            try:
                config.unlink()
            except Exception:
                pass

    # 5) Reload systemd
    _sp.run(["systemctl", "daemon-reload"], capture_output=True)
    _sp.run(["systemctl", "reset-failed"], capture_output=True)



def _rebuild_haproxy(st: dict, d: Defaults) -> None:
    routes = state.list_routes(st)
    channels = {ch.name: ch for ch in state.list_channels(st)}
    hap_cfg.write(routes, channels, HAPROXY_CFG)

    ok, out = hap_svc.validate()
    if not ok:
        console.print(f"[{C_DANGER}]{t('hap_invalid', d)}\n{out}[/]")
        return

    hap_svc.write_unit()
    systemd.daemon_reload()
    hap_svc.enable()
    hap_svc.reload_or_restart()
    console.print(f"[{C_SUCCESS}]HAProxy rebuilt ({sum(1 for r in routes if r.mode == 'balanced')} balanced routes)[/]")


# ═══════════════════════════════════════════════════════════════════════════
#  Main menu
# ═══════════════════════════════════════════════════════════════════════════

def _handle_fkey(key: str, st: dict, d: Defaults, loc: str) -> None:
    """Handle a function key (F1..F12) from the main menu.

    All actions return to the menu afterward (except F10 which exits).
    For F7 (mode toggle), we use save_defaults + implicit reload by caller.
    """
    import sys as _sys
    from .ui import help as help_ui

    if key == "F1":
        help_ui.show_full_help()

    elif key == "F2":
        d.help_mode = not d.help_mode
        save_defaults(d)
        console.print(
            f"[{C_SUCCESS}]"
            f"{t('help_toggle_on' if d.help_mode else 'help_toggle_off', d)}"
            f"[/]"
        )
        prompts.pause()

    elif key == "F3":
        lang_menu(st, d, loc)

    elif key == "F5":
        new_loc = "KHAREJ" if loc == "IRAN" else "IRAN"
        st.setdefault("meta", {})["location"] = new_loc
        state.save(st)
        console.clear()
        console.print()
        console.print(
            f"[bold {C_SUCCESS}]\u2713 Location avaz shod be: "
            f"[{C_IRAN if new_loc == 'IRAN' else C_KHAREJ}]{new_loc}[/][/]"
        )
        console.print()
        prompts.pause()

    elif key == "F7":
        # Toggle advanced/simple mode
        new_value = not getattr(d, "advanced_mode", True)
        d.advanced_mode = new_value
        save_defaults(d)
        mode_txt = "ADVANCED" if new_value else "SIMPLE"
        console.print(f"[{C_SUCCESS}]\u2713 Menu mode: {mode_txt}[/]")
        # Show what will change
        if new_value:
            console.print(
                f"[{C_MUTED}]  Hame option-ha neshoon dade mishan "
                f"(19 items)[/]"
            )
        else:
            console.print(
                f"[{C_MUTED}]  Faghat option-haye asli neshoon dade mishan "
                f"(5 items)[/]"
            )
            console.print(
                f"[{C_MUTED}]  Baghie az tarigh-e F-keys dastresi daran[/]"
            )
        prompts.pause()

    elif key == "F8":
        backup_restore(st, d, loc)

    elif key == "F10":
        console.print(f"[{C_MUTED}]Khoroj...[/]")
        _sys.exit(0)

    elif key == "F12":
        from .ui import uninstall as uninstall_ui
        uninstall_ui.show_menu()

    else:
        console.print(f"[{C_WARNING}]F-key: {key} (hanooz tarif nashode)[/]")
        prompts.pause()





def main_menu() -> None:
    """Main menu loop with F-key shortcuts."""
    d = load_defaults()
    loc = "IRAN"
    st = {}

    while True:
        # ─── Reload state ───
        st = state.load()
        loc = detect_location_cached(st)
        d = load_defaults()

        # ─── Render ───
        render_header(st, loc, d)

        if loc == "KHAREJ":
            health = build_kharej_health_summary(st, d)
            if health is not None:
                console.print(health, width=MIN_WIDTH)
                console.print()

        frp_ok = frp_installed()
        advisor = build_advisor(st, loc, frp_ok, d)

        # ─── Main menu ───
        render_menu(st, loc, d)

        # ─── F-key shortcuts panel ───
        console.print(build_shortcut_text(st, loc, d))

        # ─── Advisor ───
        console.print(advisor, width=MIN_WIDTH)
        console.print(f"[{C_MUTED}]  Dastyar: shomare ya F-key ro bezan, bad Enter[/]")

        # ─── Read input ───
        try:
            if shortcuts.supports_raw_mode():
                choice = _read_menu_input(d)
            else:
                choice = prompts.ask(t("choose", d), "").lower()
        except KeyboardInterrupt:
            console.print(f"\n[{C_MUTED}]bye[/]")
            return

        # ─── Dispatch ───
        try:
            if choice == "0":
                console.print(f"[{C_MUTED}]{t('menu_exit', d)}[/]")
                return
            elif choice == "1":
                install_frp(d)
            elif choice == "2":
                from .ui import wizard as wizard_ui
                wizard_ui.run_wizard()
            elif choice == "3":
                manage_hubs(st, d, loc)
            elif choice == "4":
                create_simple_route(st, d, loc)
            elif choice == "5":
                create_balanced_route(st, d, loc)
            elif choice == "6":
                manage_routes(st, d)
            elif choice == "7":
                export_for_node(st, d, loc)
            elif choice == "8":
                import_on_node(st, d, loc)
            elif choice == "9":
                manage_channels(st, d, loc)
            elif choice == "10":
                speedtest(st, d, loc)
            elif choice == "11":
                optimize_menu(st, d, loc)
            elif choice == "12":
                backup_restore(st, d, loc)
            elif choice == "13":
                reset_menu(st, d, loc)
            elif choice == "14":
                lang_menu(st, d, loc)
            elif choice == "15":
                help_ui.show_full_help()
            elif choice == "16":
                d.help_mode = not d.help_mode
                save_defaults(d)
                console.print(
                    f"[{C_SUCCESS}]"
                    f"{t('help_toggle_on' if d.help_mode else 'help_toggle_off', d)}"
                    f"[/]"
                )
                prompts.pause()
            elif choice == "17":
                d.show_ip = not d.show_ip
                save_defaults(d)
                if d.show_ip:
                    get_cached_public_ip(st, force_refresh=True)
                status = "ON" if d.show_ip else "OFF"
                console.print(f"[{C_SUCCESS}]Show IP: {status}[/]")
                prompts.pause()
            elif choice == "18":
                from .ui import uninstall as uninstall_ui
                uninstall_ui.show_menu()
            elif choice == "19":
                new_loc = "KHAREJ" if loc == "IRAN" else "IRAN"
                st.setdefault("meta", {})["location"] = new_loc
                state.save(st)
                console.clear()
                console.print()
                console.print(
                    f"[bold {C_SUCCESS}]\u2713 Location avaz shod be: "
                    f"[{C_IRAN if new_loc == 'IRAN' else C_KHAREJ}]{new_loc}[/][/]"
                )
                console.print()
                prompts.pause()
            elif choice == "h":
                help_ui.show_menu_help("main")
            elif choice.startswith("F") and choice[1:].isdigit():
                _handle_fkey(choice, st, d, loc)
            else:
                console.print(f"[{C_DANGER}]{t('invalid', d)}[/]")
                prompts.pause()
        except KeyboardInterrupt:
            console.print(f"\n[bright_yellow]Interrupted.[/]")
            continue


def _read_menu_input(d) -> str:
    """Read menu input: F-keys act immediately, digits accumulate until Enter.

    Returns:
        - "F1".."F12" for function keys
        - "0".."99" for numeric input
        - single letters like "h" for help
    """
    import sys as _sys

    # Show prompt
    _sys.stdout.write(f"? {t('choose', d)}: ")
    _sys.stdout.flush()

    buffer = ""

    while True:
        key = shortcuts.read_key_blocking()

        # F-key
        if key and key.startswith("F") and key[1:].isdigit():
            _sys.stdout.write(f" [{key}]\n")
            _sys.stdout.flush()
            return key

        if key == "ENTER":
            _sys.stdout.write("\n")
            _sys.stdout.flush()
            return buffer.lower()

        if key == "BACKSPACE":
            if buffer:
                buffer = buffer[:-1]
                _sys.stdout.write("\b \b")
                _sys.stdout.flush()
            continue

        if key == "ESC":
            _sys.stdout.write("\n")
            _sys.stdout.flush()
            return ""

        # Digit
        if key and len(key) == 1 and key.isdigit():
            buffer += key
            _sys.stdout.write(key)
            _sys.stdout.flush()
            continue

        # Letter (single command like 'h')
        if key and len(key) == 1 and key.isalpha():
            _sys.stdout.write(key + "\n")
            _sys.stdout.flush()
            return key.lower()

        # Ignore other keys
        continue



def run() -> None:
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print(f"\n[{C_DANGER}]Bye.[/]")


if __name__ == "__main__":
    run()
