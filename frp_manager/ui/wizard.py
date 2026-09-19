"""Combined Node + Route creation wizard — Finglish edition."""
from __future__ import annotations

import secrets
import string
import re as _re
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich import box

from .. import state
from ..config import load_defaults
from ..constants import PROTOCOLS
from ..frp import server as frp_server, client as frp_client
from ..models import Node, Channel, Route
from ..system import net, systemd
from . import prompts

console = Console()

# Colors
C_SUCCESS = "#7ec699"
C_INFO = "#5b9bff"
C_WARNING = "#ffb86c"
C_DANGER = "#ff6b6b"
C_MUTED = "#8e8e93"
C_TITLE = "#ffffff"
C_IRAN = "#f5d76e"
C_KHAREJ = "#56d4dd"
C_ACCENT = "#a78bfa"

# Fixed UI width (must match cli.py)
MIN_WIDTH = 95
C_DIM = "#5a5a5e"


def _random_token(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _step(n: int, total: int, title: str) -> None:
    console.clear()
    console.print()
    console.print(f"[bold {C_INFO}]\u2501\u2501\u2501 Step {n}/{total} \u2501\u2501\u2501[/]  [bold {C_TITLE}]{title}[/]")
    console.print()


def _info(label: str, value: str, color: str = C_INFO) -> None:
    console.print(f"  [{C_MUTED}]{label:<22}[/] [{color}]{value}[/]")


def _validate_node_name(name: str) -> bool:
    return bool(_re.match(r"^[a-zA-Z0-9\-]{2,32}$", name))

def _ensure_haproxy_ready() -> bool:
    """Verify HAProxy is installed and can be used.

    Returns True if ready, False if user wants to abort.
    Auto-installs HAProxy if missing (with user confirmation).
    """
    import subprocess
    from rich.prompt import Prompt

    # ─── Check binary ───
    binary_ok = subprocess.run(
        ["which", "haproxy"],
        capture_output=True, text=True,
    ).returncode == 0

    if not binary_ok:
        console.print()
        console.print(f"[bold {C_WARNING}]\u26a0 HAProxy nasb nist[/]")
        console.print()
        console.print(f"  [{C_MUTED}]Balanced mode be HAProxy niyaz dare.[/]")
        console.print(f"  [{C_MUTED}]Bedoon HAProxy, traffic rooye chand channel pakhsh nemishe.[/]")
        console.print()
        console.print(f"  [{C_INFO}]1.[/] Nasb-e HAProxy (apt install haproxy)")
        console.print(f"  [{C_INFO}]2.[/] Bargasht be Simple mode")
        console.print(f"  [{C_INFO}]0.[/] Cancel")
        console.print()

        ans = Prompt.ask(
            f"[{C_INFO}]Entekhab[/]",
            choices=["0", "1", "2"],
            default="1",
        )

        if ans == "0":
            return False
        if ans == "2":
            console.print(f"[{C_MUTED}]Lotfan Simple mode ro entekhab kon.[/]")
            try:
                prompts.pause()
            except Exception:
                pass
            return False

        # Install HAProxy
        console.print()
        console.print(f"[{C_INFO}]Dar hale nasb-e HAProxy...[/]")
        try:
            result = subprocess.run(
                ["apt-get", "install", "-y", "haproxy"],
                capture_output=True, text=True, timeout=180,
            )
            if result.returncode == 0:
                console.print(f"[{C_SUCCESS}]\u2713 HAProxy nasb shod[/]")
            else:
                console.print(f"[{C_DANGER}]\u2717 Nasb-e HAProxy fail shod[/]")
                console.print(f"[{C_MUTED}]{result.stderr[-300:]}[/]")
                return False
        except Exception as e:
            console.print(f"[{C_DANGER}]\u2717 {e}[/]")
            return False

    # ─── All good ───
    console.print()
    console.print(f"  [{C_SUCCESS}]\u2713[/] HAProxy amade baraye Balanced mode")
    return True




def _show_channel_explanation(entry_port: int) -> None:
    """Show a visual explanation of what channels are in balanced mode."""
    console.print()
    console.print(f"[bold {C_INFO}]\U0001f4a1 Channel chie? (dar Balanced Route)[/]")
    console.print()

    diagram = (
        f"  [{C_TITLE}]Yek channel = yek tunnel-e mostaghel-e FRP[/]\n\n"
        f"  [{C_IRAN}]Client[/]\n"
        f"     [{C_MUTED}]|[/]\n"
        f"     [{C_MUTED}]v[/]\n"
        f"  [{C_IRAN}]IRAN:{entry_port}[/]  [{C_MUTED}](HAProxy frontend)[/]\n"
        f"     [{C_MUTED}]|[/]\n"
        f"     [{C_MUTED}]+---------+---------+---------+[/]\n"
        f"     [{C_MUTED}]|         |         |         |[/]\n"
        f"     [{C_MUTED}]v         v         v         v[/]\n"
        f"  [{C_KHAREJ}]ch-1[/]      [{C_KHAREJ}]ch-2[/]      [{C_KHAREJ}]ch-3[/]      [{C_KHAREJ}]ch-4[/]\n"
        f"     [{C_MUTED}]|         |         |         |[/]\n"
        f"     [{C_MUTED}]+---------+---------+---------+[/]\n"
        f"     [{C_MUTED}]|[/]\n"
        f"     [{C_MUTED}]v[/]\n"
        f"  [{C_KHAREJ}]Xray :{entry_port} (rooye server-e kharej)[/]"
    )

    console.print(Panel(
        Text.from_markup(diagram),
        border_style=C_INFO,
        box=box.ROUNDED,
        padding=(0, 1),
    ))
    console.print()

    console.print(f"  [bold {C_SUCCESS}]\u2713 Chera chand channel?[/]")
    console.print(f"  [{C_MUTED}]  \u2022 Har channel yek tunnel-e joda = parallel[/]")
    console.print(f"  [{C_MUTED}]  \u2022 Bandwidth-e kol = (bandwidth-e yek channel) x (tedad)[/]")
    console.print(f"  [{C_MUTED}]  \u2022 Age yek channel down beshe, baghie kar mikonan[/]")
    console.print()

    console.print(f"  [bold {C_WARNING}]\u26a0 Mesal:[/]")
    console.print(f"  [{C_MUTED}]  Agar hame channel-ha rooye yek server-e kharej bashan:[/]")
    console.print(f"  [{C_MUTED}]    entry :{entry_port} \u2192 4 channel \u2192 hamun Xray[/]")
    console.print(f"  [{C_MUTED}]  Bandwidth-e kol \u2248 4 x sari'at-e yek tunnel[/]")
    console.print()

    console.print(f"  [bold {C_INFO}]\U0001f4a1 Chand bezanam?[/]")
    console.print(f"  [{C_MUTED}]  \u2022 2-3 channel: traffic-e motevasset[/]")
    console.print(f"  [{C_MUTED}]  \u2022 4-6 channel: bandwidth-e bala (pishnahad)[/]")
    console.print(f"  [{C_MUTED}]  \u2022 7-8 channel: server-e ghavi + network-e khoob[/]")
    console.print()


def _ask_port(prompt: str, default: int = 443,
              exclude_route_port: int | None = None) -> int:
    while True:
        raw = Prompt.ask(f"[{C_INFO}]{prompt}[/]", default=str(default)).strip()
        if not raw.isdigit():
            console.print(f"[{C_DANGER}]  \u2717 Bayad adad bashe.[/]")
            continue
        port = int(raw)
        if not (1 <= port <= 65535):
            console.print(f"[{C_DANGER}]  \u2717 Port bayad 1 ta 65535 bashe.[/]")
            continue
        if exclude_route_port and port == exclude_route_port:
            console.print(f"[{C_WARNING}]  \u26a0 In port ghablan estefade shode.[/]")
            continue
        return port


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#  STEP 1 — Mode
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

def _choose_mode() -> Optional[str]:
    console.print(f"[bold {C_TITLE}]Wizard mode:[/]\n")
    console.print(f"  [{C_INFO}]1[/]  [bold]Quick[/]  [{C_MUTED}]\u2014 3 so'al, baghie auto[/]")
    console.print(f"       [{C_MUTED}](Pishnahad baraye user-e jadid)[/]")
    console.print()
    console.print(f"  [{C_INFO}]2[/]  [bold]Custom[/] [{C_MUTED}]\u2014 kontrol-e kamel rooye hame chiz[/]")
    console.print(f"       [{C_MUTED}](Baraye setup-e pishrafte)[/]")
    console.print()
    console.print(f"  [{C_MUTED}]0[/]  Cancel")
    console.print()

    choice = Prompt.ask(
        f"[bold {C_INFO}]Entekhab[/]",
        choices=["0", "1", "2"],
        default="1",
        show_choices=False,
    )
    if choice == "0":
        return None
    if choice == "1":
        return "quick"
    return "custom"


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#  STEP 2 — Node
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

def _collect_node(st: dict, custom: bool = False) -> Optional[Node]:
    existing = state.list_nodes(st)
    if existing:
        console.print(f"[{C_MUTED}]Node-haye mojood: "
                      f"{', '.join(n.name for n in existing)}[/]\n")

    console.print(f"[{C_MUTED}]Inja yek esm bara server-e kharej (node) tarif konid.[/]")
    console.print(f"[{C_MUTED}]Mesal: Germany-01, Hetzner-02, Frankfurt-A, Helsinki-2.[/]\n")

    # Name
    while True:
        name = Prompt.ask(f"[{C_INFO}]Esm-e node[/]").strip()
        if not name:
            console.print(f"[{C_DANGER}]  \u2717 Esm lazem ast.[/]")
            continue
        if not _validate_node_name(name):
            console.print(f"[{C_DANGER}]  \u2717 Faghat a-z, 0-9, dash (2-32 char).[/]")
            continue
        if state.get_node(st, name):
            console.print(f"[{C_DANGER}]  \u2717 Node '{name}' ghablan vojud dare.[/]")
            continue
        break

    # Host
    while True:
        host = Prompt.ask(f"[{C_INFO}]IP ya domain-e server-e kharej[/]").strip()
        if not host:
            console.print(f"[{C_DANGER}]  \u2717 Host lazem ast.[/]")
            continue
        break

## TWEST

    # Hub Name (this server's name on IRAN side)
    hub_name = "iran-1"
    if _is_iran_side(st):
        console.print()
        console.print(f"[{C_MUTED}]Esm-e in server-e IRAN (Hub):[/]")
        console.print(f"[{C_MUTED}]In esm rooye server-e kharej estefade mishe.[/]")
        hub_name = Prompt.ask(
            f"[{C_INFO}]Esm-e Hub[/]",
            default="iran-1",
        ).strip()
        if not hub_name:
            hub_name = "iran-1"
        # Save to state.meta
        st.setdefault("meta", {})["hub_name"] = hub_name
        state.save(st)

    if not custom:
        return Node(name=name, host=host, location="", note="")

    # Custom: extra fields
    location = Prompt.ask(
        f"[{C_INFO}]Location[/] [{C_MUTED}](ekhtiari, mesal: Germany)[/]",
        default="",
    ).strip()
    note = Prompt.ask(
        f"[{C_INFO}]Note[/] [{C_MUTED}](ekhtiari)[/]",
        default="",
    ).strip()
    return Node(name=name, host=host, location=location, note=note)


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#  STEP 3 — Route
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

def _collect_protocol_mix(total_channels: int) -> Optional[list[str]]:
    """Step-by-step protocol selection.

    Asks how many channels for each protocol in order:
      TCP -> KCP -> QUIC -> WS
    Shows remaining count as user picks.
    Loops back if user cancels at confirmation.

    Returns:
        list[str]: list of protocol names, one per channel
        None:      user cancelled entirely
    """
    while True:  # allow restart if user cancels confirmation
        remaining = total_channels
        chosen: list[str] = []

        console.print()
        console.print(f"[bold {C_INFO}]Protocol mix baraye {total_channels} channel[/]")
        console.print(f"[{C_MUTED}]Dar har marhale, tedad channel-haye har protocol ra vared kon.[/]")
        console.print(f"[{C_MUTED}]Agar nemikhay, 0 bezan.[/]")
        console.print()

        # ─── TCP ───
        tcp_n = _ask_channel_count(
            "TCP", remaining,
            hint="sari-tarin, paydar-tarin",
        )
        if tcp_n is None:
            return None
        chosen += ["tcp"] * tcp_n
        remaining -= tcp_n
        if remaining == 0:
            if _confirm_protocol_mix(chosen):
                return chosen
            else:
                continue

        # ─── KCP ───
        kcp_n = _ask_channel_count(
            "KCP", remaining,
            hint="khob baraye network-e lossy (UDP)",
        )
        if kcp_n is None:
            return None
        chosen += ["kcp"] * kcp_n
        remaining -= kcp_n
        if remaining == 0:
            if _confirm_protocol_mix(chosen):
                return chosen
            else:
                continue

        # ─── QUIC ───
        quic_n = _ask_channel_count(
            "QUIC", remaining,
            hint="modern, bandwidth bala (UDP)",
        )
        if quic_n is None:
            return None
        chosen += ["quic"] * quic_n
        remaining -= quic_n
        if remaining == 0:
            if _confirm_protocol_mix(chosen):
                return chosen
            else:
                continue

        # ─── WS ───
        ws_n = _ask_channel_count(
            "WS", remaining,
            hint="WebSocket, baraye bypass firewall",
        )
        if ws_n is None:
            return None
        chosen += ["ws"] * ws_n
        remaining -= ws_n

        # Should be 0 now (because we forced exact = remaining)
        # But just to be safe, if user entered less than remaining,
        # we add the rest as TCP
        if remaining > 0:
            console.print(f"[{C_WARNING}]  \u26a0 {remaining} channel baghimonde \u2014 be TCP ezafe mishan[/]")
            chosen += ["tcp"] * remaining

        if _confirm_protocol_mix(chosen):
            return chosen
        else:
            continue


def _ask_channel_count(proto_name: str, remaining: int,
                       hint: str = "") -> Optional[int]:
    """Ask how many channels for a given protocol.

    Returns None if user cancels (Ctrl+C).
    Returns integer between 0 and remaining.
    """
    if remaining <= 0:
        return 0

    hint_txt = f"  [{C_MUTED}]({hint})[/]" if hint else ""
    prompt = (
        f"[{C_INFO}]Chand {proto_name}?[/] "
        f"[{C_MUTED}](0-{remaining}, baqi-moonde: {remaining})[/]"
    )

    while True:
        console.print(f"  {prompt}{hint_txt}")
        try:
            raw = Prompt.ask(f"  [{C_MUTED}]>[/]", default="0").strip()
        except (KeyboardInterrupt, EOFError):
            return None

        if not raw.isdigit():
            console.print(f"  [{C_DANGER}]\u2717 Bayad adad bashe.[/]")
            continue

        n = int(raw)
        if n < 0:
            console.print(f"  [{C_DANGER}]\u2717 Adad manfi ghabool nist.[/]")
            continue
        if n > remaining:
            console.print(f"  [{C_DANGER}]\u2717 Bishtar az {remaining} nemishe.[/]")
            continue

        # Visual feedback
        bar = "#" * n + "." * (remaining - n)
        console.print(f"  [{C_SUCCESS}]\u2713 {proto_name}: {n}[/]  [{C_MUTED}][{bar}][/]")
        console.print()
        return n


def _confirm_protocol_mix(chosen: list[str]) -> bool:
    """Show summary of protocol mix and ask for confirmation.

    Returns True if confirmed, False if user wants to redo.
    Raises _WizardCancel if user cancels entirely.
    """
    from collections import Counter
    import questionary as _q

    counts = Counter(chosen)

    console.print()
    console.print(f"[bold {C_INFO}]\u2501\u2501\u2501 Khollase \u2501\u2501\u2501[/]")
    console.print()
    console.print(f"  [{C_SUCCESS}]\u2713[/] In channel-ha sakhte mishan:")

    colors = {
        "tcp":  C_INFO,
        "kcp":  C_ACCENT,
        "quic": C_IRAN,
        "ws":   C_SUCCESS,
    }
    for proto, count in counts.items():
        color = colors.get(proto, C_TITLE)
        console.print(f"    [{color}]\u2022 {proto.upper()}: {count} channel[/]")

    console.print()
    console.print(f"  [{C_MUTED}]Majmooe: {len(chosen)} channel[/]")
    console.print()

    # Use questionary.select for single-key selection without Enter
    answer = _q.select(
        "In channel ha mored-e taeed hast?",
        choices=[
            _q.Choice(title="yes   (taiid)", value="y"),
            _q.Choice(title="redo  (az avval)", value="n"),
            _q.Choice(title="cancel", value="q"),
        ],
    ).ask()

    if answer is None:  # Ctrl+C
        return False
    if answer == "y":
        return True
    if answer == "q":
        raise _WizardCancel()
    return False


class _WizardCancel(Exception):
    """Raised when user wants to cancel the wizard from a nested prompt."""
    pass


def _collect_route(st: dict, node: Node, custom: bool = False) -> Optional[dict]:
    # ─── Entry port explanation ───
    console.print(f"[bold {C_INFO}]\U0001f4a1 Entry port chie?[/]")
    console.print()
    console.print(f"  [{C_TITLE}]Port-e voroodi be server-e IRAN.[/]")
    console.print(f"  [{C_MUTED}]Hamin porti ke user az tariq-e Server-e Iran behesh vasl mishe.[/]")
    console.print()
    console.print(f"  [bold {C_SUCCESS}]\u25b8 Mesal 1 (pishnahad):[/]")
    console.print(f"  [{C_MUTED}]Server-e kharej (node) config keh setup kardim rooye 443 tanzim shode[/]")
    console.print(f"  [{C_MUTED}]va kar mideh. Hala agar bekhaim rooye server-e IRAN ham ba hamin[/]")
    console.print(f"  [{C_MUTED}]port kar konad, bayad hamin 443 ro vared kard.[/]")
    console.print(f"  [{C_IRAN}]  \u2192 Entry port = 443  |  Target port = 443[/]")
    console.print()
    console.print(f"  [bold {C_WARNING}]\u25b8 Mesal 2 (port-e digar rooye IRAN):[/]")
    console.print(f"  [{C_MUTED}]Server-e kharej (node) config rooye 443 tanzim shode va kar mideh,[/]")
    console.print(f"  [{C_MUTED}]vali mikhay rooye IRAN ba port-e digari (mesal 8443) behesh vasl beshi.[/]")
    console.print()
    console.print(f"  [{C_MUTED}]Yani config-e IRAN ba port-e 8443 ferestade mishe be 443-e kharej.[/]")
    console.print(f"  [{C_MUTED}]Config-e IRAN (Hub) mishe ba port-e 8443,[/]")
    console.print(f"  [{C_MUTED}]dar soorati ke port-e kharej rooye 443 ejra shode.[/]")
    console.print(f"  [{C_IRAN}]  \u2192 Entry port = 8443  |  Target port = 443[/]")
    console.print()
    console.print()

    # ─── Entry port ───
    while True:
        entry = Prompt.ask(
            f"[{C_INFO}]Entry port[/] [{C_MUTED}](port-e public rooye IRAN, mesal 443)[/]",
            default="443",
        ).strip()
        if not entry.isdigit():
            console.print(f"[{C_DANGER}]  \u2717 Bayad adad bashe.[/]")
            continue
        entry = int(entry)
        if not (1 <= entry <= 65535):
            console.print(f"[{C_DANGER}]  \u2717 Port bayad 1 ta 65535 bashe.[/]")
            continue
        if state.get_route_by_port(st, entry):
            console.print(f"[{C_DANGER}]  \u2717 Port {entry} ghablan estefade shode.[/]")
            continue
        break

    # ─── Target port explanation ───
    console.print()
    console.print(f"[bold {C_INFO}]\U0001f4a1 Target port chie?[/]")
    console.print()
    console.print(f"  [{C_TITLE}]Port-e daghigh-e service rooye server-e kharej ast.[/]")
    console.print(f"  [{C_MUTED}]Bayad hamoon porti bashe ke Xray/VPN rooye server-e kharej[/]")
    console.print(f"  [{C_MUTED}]rooye un tanzim shode.[/]")
    console.print()
    console.print(f"  [bold {C_SUCCESS}]\u25b8 Mesal:[/]")
    console.print(f"  [{C_MUTED}]Agar Xray rooye kharej 443 bashe \u2192 Target port = 443[/]")
    console.print(f"  [{C_MUTED}]Bayad hamoon port config rooye server-e kharej ro vared koni.[/]")
    console.print()
    console.print()

    target = Prompt.ask(
        f"[{C_INFO}]Target port[/] [{C_MUTED}](port-e config rooye server-e kharej)[/]",
        default=str(entry),
    ).strip()
    if not target.isdigit():
        target = entry
    target = int(target)

    # ═══════════════════════════════════════════════════════════
    #  ROUTE MODE  (moved BEFORE protocol)
    # ═══════════════════════════════════════════════════════════
    console.print()
    console.clear()
    console.print()
    console.print(f"[bold {C_INFO}]\U0001f4a1 Route mode chie?[/]")
    console.print()
    console.print(f"  [bold {C_SUCCESS}]Simple[/]   [{C_MUTED}]\u2014 traffic az yek tunel (canal) rad misheh.[/]")
    console.print(f"  [{C_MUTED}]Ageh server pahnaye band khoobi dareh ya trafik ziadi nadarid.[/]")
    console.print()
    console.print(f"  [bold {C_WARNING}]Balanced[/] [{C_MUTED}]\u2014 taqsim-e traffic rooye chand tunel (canal) + HAProxy.[/]")
    console.print(f"  [{C_MUTED}]Trafik az tariq-e chandin tunel (canal) bein-e server-e IRAN (Hub)[/]")
    console.print(f"  [{C_MUTED}]va server-e kharej (Node) enteghal dadeh misheh.[/]")
    console.print(f"  [{C_MUTED}]Monaseb-e pahnaye band bala, HA, mitooneh chandin barabar sari-tar basheh.[/]")
    console.print(f"  [{C_MUTED}]Be ghodrat-e server (RAM va CPU) ham bastegi dare.[/]")
    console.print(f"  [{C_MUTED}]Dar nahayat in chand tunel (kanal) az tarigh-e HAProxy modiriat misheh.[/]")
    console.print()
    console.print()

    console.print(f"  [{C_INFO}]1[/]  Simple")
    console.print(f"  [{C_INFO}]2[/]  Balanced")
    mode_choice = Prompt.ask(
        f"[{C_INFO}]Route mode[/]",
        choices=["1", "2"],
        default="1",
    )
    route_mode = "simple" if mode_choice == "1" else "balanced"

    # ─── BALANCED: verify HAProxy is available ───
    if route_mode == "balanced":
        _ensure_haproxy_ready()

    # ═══════════════════════════════════════════════════════════
    #  SIMPLE MODE: ask protocol once
    # ═══════════════════════════════════════════════════════════
    if route_mode == "simple":
        console.clear()
        console.print()
        console.print(f"[bold {C_INFO}]Protocol Tunnel (Kanal):[/]")
        console.print(f"[{C_MUTED}]No-e protocol-e tunel (kanal) ra entekhab konid.[/]")
        console.print()
        console.print(f"  [{C_INFO}]1[/]  [bold]TCP[/]      [{C_MUTED}]\u2014 sari-tarin va paydar-tarin (pishnahad)[/]")
        console.print(f"  [{C_INFO}]2[/]  [bold]KCP[/]      [{C_MUTED}]\u2014 khob baraye network-e daraye ekhtelal (UDP)[/]")
        console.print(f"  [{C_INFO}]3[/]  [bold]QUIC[/]     [{C_MUTED}]\u2014 protocol-e jadid, pahnaye band bala (UDP)[/]")
        console.print(f"  [{C_INFO}]4[/]  [bold]WS[/]       [{C_MUTED}]\u2014 WebSocket, baraye obor az sad-e filtering[/]")
        console.print()

        proto_choice = Prompt.ask(
            f"[{C_INFO}]Protocol[/]",
            choices=["1", "2", "3", "4"],
            default="1",
        )
        proto = {"1": "tcp", "2": "kcp", "3": "quic", "4": "ws"}[proto_choice]

        return {
            "entry": entry,
            "target": target,
            "proto": proto,
            "mode": "simple",
            "channels": 1,
        }

    # ═══════════════════════════════════════════════════════════
    #  BALANCED MODE: channel count + protocol mix
    # ═══════════════════════════════════════════════════════════

    # Visual explanation of what channels mean
    _show_channel_explanation(entry)

    # Ask channel count
    console.print()
    while True:
        raw = Prompt.ask(
            f"[{C_INFO}]Chand channel ejra konam?[/] "
            f"[{C_MUTED}](2-8, pishnahad 3-6)[/]",
            default="3",
        ).strip()
        if raw.isdigit() and 2 <= int(raw) <= 8:
            n_channels = int(raw)
            break
        console.print(f"[{C_DANGER}]  \u2717 Adad bayad bein-e 2 ta 8 bashe.[/]")

    # Step-by-step protocol selection
    try:
        protos = _collect_protocol_mix(n_channels)
    except _WizardCancel:
        console.print(f"[{C_MUTED}]Cancel shod.[/]")
        return None

    if protos is None:
        console.print(f"[{C_MUTED}]Cancel shod.[/]")
        return None

    return {
        "entry": entry,
        "target": target,
        "proto": protos[0],
        "protos": protos,
        "mode": "balanced",
        "channels": len(protos),
    }



def _preview(st: dict, node: Node, plan: dict, d) -> bool:
    console.print(f"[bold {C_INFO}]Review \u2014 in chiz-ha sakhte mishan:[/]\n")

    # ─── This server ───
    hub_ip = _get_hub_ip(st)
    console.print(f"  [bold {C_IRAN}]In server (Hub):[/]")
    _info("Role", "Hub / Iran (frps listens)", C_IRAN)
    _info("Public IP", hub_ip, C_IRAN)
    console.print()

    # ─── Node ───
    console.print(f"  [bold {C_KHAREJ}]Node (Kharej):[/]")
    _info("Name", node.name, C_KHAREJ)
    _info("Host", node.host, C_KHAREJ)
    if node.location:
        _info("Location", node.location, C_MUTED)
    console.print()

    # ─── Route ───
    console.print(f"  [bold {C_INFO}]Route:[/]")
    _info("Entry port", f":{plan['entry']} (rooye IRAN)", C_IRAN)
    _info("Target port", f"{plan['target']} (rooye {node.name})", C_KHAREJ)
    _info("Mode", plan["mode"].upper(), C_INFO)
    console.print()

    # ─── Channels ───
    console.print(f"  [bold]Channels ({plan['channels']}):[/]")
    channels = _simulate_channels(st, node, plan, d)
    tbl = Table(show_header=False, box=box.SIMPLE_HEAD, padding=(0, 2))
    tbl.add_column("name", style=f"bold {C_KHAREJ}")
    tbl.add_column("proto", style=C_INFO)
    tbl.add_column("bind", style=C_IRAN, justify="right")
    tbl.add_column("remote", style=C_MUTED, justify="right")

    for ch in channels:
        tbl.add_row(
            ch.name, ch.proto.upper(),
            f":{ch.bind_port}", f":{ch.remote_port}",
        )
    console.print(tbl)
    console.print()

    # ─── Summary ───
    if plan["mode"] == "balanced":
        console.print(f"  [{C_SUCCESS}]\u2713[/] HAProxy frontend rooye :{plan['entry']} sakhte mishe")
        console.print(f"  [{C_SUCCESS}]\u2713[/] Traffic bein {plan['channels']} channel pakhsh mishe")
    else:
        console.print(f"  [{C_MUTED}]Simple route: HAProxy lazem nist[/]")
    console.print()

    return prompts.confirm("In route sakhte beshe?", default=True)

def _is_iran_side(st: dict) -> bool:
    """Check if running on IRAN side."""
    meta = st.get("meta", {})
    loc = meta.get("location", "")
    if loc == "IRAN":
        return True
    if loc == "KHAREJ":
        return False
    from ..system import net
    cc = net.detect_country_code(timeout=3)
    return cc == "IR"




def _get_hub_ip(st: dict) -> str:
    """Get HUB public IP from cache or detect."""
    meta = st.setdefault("meta", {})
    cached = meta.get("public_ip")
    if cached and cached != "unknown":
        return cached
    ip = net.detect_public_ip(timeout=4) or "unknown"
    meta["public_ip"] = ip
    state.save(st)
    return ip


def _simulate_channels(st: dict, node: Node, plan: dict, d) -> list[Channel]:
    route_id = f"rt-{plan['entry']}"
    channels = []
    existing_names = list(st.get("channels", {}).keys())
    next_idx = 1

    if plan["mode"] == "simple":
        protos = [plan["proto"]]
    else:
        protos = plan.get("protos", ["tcp"])

    for proto in protos:
        while f"ch-{plan['entry']}-{node.name}-{next_idx:02d}" in existing_names:
            next_idx += 1
        idx = next_idx
        next_idx += 1

        bind_port = net.random_free_port(d.port_range_start, d.port_range_end)

        # KEY LOGIC:
        # - simple mode: remote_port = entry_port (direct port forward on Hub)
        # - balanced mode: remote_port = auto (HAProxy listens on entry_port, forwards to remote_port)
        if plan["mode"] == "simple":
            remote_port = plan["entry"]
        else:
            remote_port = 20000 + (plan["entry"] % 10000) + idx

        iperf_port = 55000 + (plan["entry"] % 10000) + idx

        ch = Channel(
            route_id=route_id,
            hub=node.name,
            index=idx,
            proto=proto,
            bind_port=bind_port,
            token=_random_token(d.token_length),
            remote_port=remote_port,
            target_port=plan["target"],
            iperf_port=iperf_port,
        )
        channels.append(ch)
    return channels


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#  Creation
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

def _create(st: dict, node: Node, plan: dict, d) -> tuple[Node, Route, list[Channel]]:
    state.add_node(st, node)

    route_id = f"rt-{plan['entry']}"
    route = Route(
        id=route_id,
        entry_port=plan["entry"],
        mode=plan["mode"],
        channels=[],
    )

    channels: list[Channel] = []
    existing_names = list(st.get("channels", {}).keys())
    next_idx = 1

    if plan["mode"] == "simple":
        protos = [plan["proto"]]
    else:
        protos = plan.get("protos", ["tcp"])

    for proto in protos:
        while f"ch-{plan['entry']}-{node.name}-{next_idx:02d}" in existing_names:
            next_idx += 1
        idx = next_idx
        next_idx += 1

        bind_port = net.random_free_port(d.port_range_start, d.port_range_end)

        # simple mode: direct port forward (remote_port = entry_port)
        # balanced mode: HAProxy on entry_port forwards to remote_port
        if plan["mode"] == "simple":
            remote_port = plan["entry"]
        else:
            remote_port = 20000 + (plan["entry"] % 10000) + idx

        iperf_port = 55000 + (plan["entry"] % 10000) + idx

        ch = Channel(
            route_id=route_id,
            hub=node.name,
            index=idx,
            proto=proto,
            bind_port=bind_port,
            token=_random_token(d.token_length),
            remote_port=remote_port,
            target_port=plan["target"],
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

    if plan["mode"] == "balanced":
        _rebuild_haproxy(st, d)

    return node, route, channels


def _write_server_channel(ch: Channel, d) -> None:
    frp_server.write_frps_unit()
    frp_server.write_frps_config(
        ch, max_pool=d.max_pool_count,
        tcpmux=d.tcpmux, heartbeat_timeout=d.heartbeat_timeout,
    )
    systemd.daemon_reload()
    systemd.service_action(ch.frps_service, "enable")
    systemd.service_action(ch.frps_service, "restart")


def _rebuild_haproxy(st: dict, d) -> None:
    from ..constants import HAPROXY_CFG
    from ..haproxy import config as hap_cfg, service as hap_svc
    routes = state.list_routes(st)
    channels = {ch.name: ch for ch in state.list_channels(st)}
    hap_cfg.write(routes, channels, HAPROXY_CFG)
    ok, out = hap_svc.validate()
    if not ok:
        console.print(f"[{C_DANGER}]HAProxy invalid: {out}[/]")
        return
    hap_svc.write_unit()
    systemd.daemon_reload()
    hap_svc.enable()
    hap_svc.reload_or_restart()


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#  Success summary
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

def _success_summary(st: dict, node: Node, route: Route,
                     channels: list[Channel]) -> None:
    """Show success summary with compact link + detailed next steps."""
    console.clear()

    # ─── Header box ───
    console.print(Panel(
        Text.from_markup(f"[bold {C_SUCCESS}]\u2705 Setup kamel shod![/]"),
        border_style=C_SUCCESS,
        box=box.ROUNDED,
        padding=(0, 1),
        width=MIN_WIDTH,
    ))
    console.print()

    # ─── Hub info ───
    hub_ip = _get_hub_ip(st)
    console.print(f"  [bold {C_IRAN}]Server-e IRAN (Hub):[/]")
    _info("Public IP", hub_ip, C_IRAN)
    console.print()

    # ─── Node info ───
    console.print(f"  [bold {C_KHAREJ}]Server-e kharej (Node):[/]")
    _info("Name", node.name, C_KHAREJ)
    _info("Host", node.host, C_KHAREJ)
    console.print()

    # ─── Route info ───
    console.print(f"  [bold {C_INFO}]Route:[/]")
    _info("Route ID", route.id, C_INFO)
    _info("Entry port", f":{route.entry_port} (rooye IRAN)", C_IRAN)
    _info("Mode", route.mode.upper(), C_INFO)
    _info("Channels", str(len(channels)), C_SUCCESS)
    console.print()

    # ─── Online status ───
    online = 0
    for ch in channels:
        if systemd.is_active(ch.frps_service):
            online += 1

    if online == len(channels):
        console.print(f"  [{C_SUCCESS}]\u25cf Hame {online} channel ONLINE[/]")
    else:
        console.print(f"  [{C_WARNING}]\u25cf {online}/{len(channels)} channel online[/]")
    console.print()

    # ─── Compact file info ───
    hub_ip = _get_hub_ip(st)
    try:
        from ..frp import compact as _compact
        path = _compact.export_channels(channels, node.name, hub_ip)
        console.print(f"  [{C_SUCCESS}]\u2713[/] File zakhire shod: [{C_KHAREJ}]{path}[/]")
        console.print()
    except Exception as e:
        console.print(f"[{C_DANGER}]Khata dar export: {e}[/]")
        path = None

    # ─── Compact section ───
    console.print(Panel(
        Text.from_markup(
            f"[bold {C_INFO}]Compact-e in Node[/]"
        ),
        border_style=C_KHAREJ,
        box=box.ROUNDED,
        padding=(0, 1),
        width=MIN_WIDTH,
    ))
    console.print()

    # Print compact content
    if path and path.exists():
        content = path.read_text()
        console.print(f"[{C_MUTED}]" + "─" * (MIN_WIDTH - 4) + "[/]")
        for line in content.splitlines():
            if line.startswith("#"):
                console.print(f"[{C_MUTED}]{line}[/]")
            elif line.strip():
                console.print(f"[bold {C_KHAREJ}]{line}[/]")
            else:
                console.print(line)
        console.print(f"[{C_MUTED}]" + "─" * (MIN_WIDTH - 4) + "[/]")
        console.print()
    else:
        console.print(f"[{C_DANGER}]Compact content available nabood.[/]")
        console.print()

    # ─── Next steps ───
    target_port = channels[0].target_port if channels else "?"
    console.print(f"[bold {C_INFO}]Ghadam-haye badi:[/]")
    console.print()

    console.print(f"  [{C_INFO}]1.[/] Vared-e server-e kharej ([bold]{node.name}[/]) sho:")
    console.print(f"     [{C_MUTED}]ssh root@{node.host}[/]")
    console.print()

    console.print(f"  [{C_INFO}]2.[/] Ejra kon: [{C_KHAREJ}]sudo frp-cli[/] → Menu [{C_INFO}][ 8][/] Import rooye Node")
    console.print(f"     [{C_MUTED}]In line compact-ha-ee keh az ghesmat-e bala copy zadi ro vared mikonid.[/]")
    console.print(f"     [{C_MUTED}]In khat-ha mitoonan yeki be yeki vared besheh, ya hameh ba ham,[/]")
    console.print(f"     [{C_MUTED}]farghi nemikoneh. Dar nahayat baraye etmam-e vared kardan,[/]")
    console.print(f"     [{C_MUTED}]link-haye compact ro Enter bezanid (ye Enter-e khali).[/]")
    console.print()

    console.print(f"  [{C_INFO}]3.[/] Ageh link compact ro faramoosh kardid:")
    console.print(f"     [{C_MUTED}]Rooye server-e IRAN (Hub) az tariq-e menu [{C_INFO}][ 7][/] Export baraye Node[/]")
    console.print(f"     [{C_MUTED}]vared shavid, ba kelid-haye bala va paeen node ro entekhab konid,[/]")
    console.print(f"     [{C_MUTED}]bad link-e compact neshand dadeh shode ro mitoonid bebinid va copy bezanid.[/]")
    console.print()

    console.print(f"  [{C_INFO}]4.[/] Baraye barresi vazeiat-e etesal-e tunel (kanal) ha:")
    console.print(f"     [{C_MUTED}]Az tariq-e server-e kharej (Node) vared Menu [{C_INFO}][ 9][/] Modiriyat Channel-ha[/]")
    console.print(f"     [{C_MUTED}]beshid, bad vared [{C_INFO}]7 Check health of one channel[/] beshid,[/]")
    console.print(f"     [{C_MUTED}]ba entekhab-e channel, vazeiat-e ertebati tunel neshan dadeh mishavad.[/]")
    console.print()

    console.print(f"  [{C_INFO}]5.[/] Hala baraye obor-e traffic az tariq-e server-e Iran, tooye config-e")
    console.print(f"     Xray ya VPN keh be moshtari ersal mikonid, bayad IP va port-e in tanzimat-e")
    console.print(f"     tunel ro mesle-e zir vared konid:")
    console.print(f"     IP ro [{C_INFO}]{hub_ip}[/] va port ro [{C_INFO}]{route.entry_port}[/] bezarid.")
    console.print()
    console.print(f"     [{C_MUTED}]Mesal: {hub_ip}:{route.entry_port}[/]")
    console.print()



def run_wizard() -> None:
    console.clear()
    console.print()

    # Header
    console.print(Panel(
        Text.from_markup(
            f"[bold {C_TITLE}]WIZARD-E TARKIBI[/]  "
            f"[{C_MUTED}]\u2014 Node + Route dar yek jaryan[/]"
        ),
        title=f"[bold {C_INFO}] \U0001f9d9 Wizard [/]",
        border_style=C_INFO,
        box=box.ROUNDED,
        padding=(0, 1),
        width=MIN_WIDTH,
    ))
    console.print()

    # ─── Intro ───
    console.print(f"[{C_WARNING}]\u26a0  In wizard bayad rooye [/][bold {C_IRAN}]SERVER-E IRAN (Hub)[/]"
                  f"[{C_WARNING}] ejra beshe.[/]")
    console.print()
    console.print(f"[{C_MUTED}]In wizard dar yek jaryan misaze:[/]")
    console.print(f"[{C_MUTED}]  1. Node (server-e kharej)[/]")
    console.print(f"[{C_MUTED}]  2. Route (port-e public rooye Iran)[/]")
    console.print(f"[{C_MUTED}]  3. Channel-ha (tunnel-ha bein Iran va Kharej)[/]")
    console.print()
    console.print(f"[{C_MUTED}]Baraye help-e har ghadam, '?' bezan.[/]")
    console.print()

    # Step 1
    _step(1, 4, "Entekhab-e mode")
    mode = _choose_mode()
    if mode is None:
        console.print(f"[{C_MUTED}]Cancel shod.[/]")
        Prompt.ask(f"\n[{C_MUTED}]Enter bezan baraye bargasht[/]", default="")
        return

    st = state.load()
    d = load_defaults()

    # Step 2
    _step(2, 4, "Tanzim-e Node (server-e kharej)")
    node = _collect_node(st, custom=(mode == "custom"))
    if node is None:
        console.print(f"[{C_MUTED}]Cancel shod.[/]")
        Prompt.ask(f"\n[{C_MUTED}]Enter bezan baraye bargasht[/]", default="")
        return

    # Step 3
    _step(3, 4, "Tanzim-e Route (port-e public rooye Iran)")
    plan = _collect_route(st, node, custom=(mode == "custom"))
    if plan is None:
        console.print(f"[{C_MUTED}]Cancel shod.[/]")
        Prompt.ask(f"\n[{C_MUTED}]Enter bezan baraye bargasht[/]", default="")
        return

    # Step 4
    _step(4, 4, "Bazbini va tasdiq")
    if not _preview(st, node, plan, d):
        console.print(f"[{C_MUTED}]Cancel shod. Hich chizi sakhte nashod.[/]")
        Prompt.ask(f"\n[{C_MUTED}]Enter bezan baraye bargasht[/]", default="")
        return

    # Create
    console.print()
    console.print(f"[{C_INFO}]Dar hale sakht...[/]")
    try:
        node, route, channels = _create(st, node, plan, d)
        _success_summary(st, node, route, channels)
    except Exception as e:
        console.print(f"[{C_DANGER}]Kharab shod: {e}[/]")
        import traceback
        traceback.print_exc()

    Prompt.ask(f"[{C_MUTED}]Enter bezan baraye bargasht[/]", default="")
