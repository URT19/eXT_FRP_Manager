"""Help system for FRP Manager v3."""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

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


def help_mode_badge(enabled: bool) -> None:
    if enabled:
        console.print(
            f"[bold {C_SUCCESS}]● Help Mode: ON[/] "
            f"[{C_MUTED}](toggle: menu [16])[/]"
        )
    else:
        console.print(f"[{C_MUTED}]○ Help Mode: OFF (toggle: menu [16])[/]")


def inline_hint(text: str) -> None:
    console.print(f"  [{C_MUTED} italic]└─ {text}[/]")


def edu_tip(title: str, body: str) -> None:
    content = Text()
    content.append(f"💡 {title}\n\n", style=f"bold {C_WARNING}")
    content.append(body, style=C_TITLE)
    console.print(
        Panel(
            content,
            border_style=C_WARNING,
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )


def _section(title: str, items: list[tuple[str, str]]) -> None:
    console.print(f"\n[bold {C_INFO}]{title}[/]")
    console.print(f"[{C_MUTED}]" + "─" * 64 + "[/]")
    for key, val in items:
        console.print(f"  [bold {C_KHAREJ}]▸ {key}[/]")
        for line in val.split("\n"):
            console.print(f"    [{C_TITLE}]{line}[/]")


def show_full_help() -> None:
    """Full help screen — the master guide."""
    console.clear()
    console.print()

    # Header
    console.print(f"[bold {C_INFO}]╔" + "═" * 68 + "╗[/]")
    console.print(
        f"[bold {C_INFO}]║[/] 📚 [bold {C_TITLE}]RAHNAMA (HELP) — FRP Manager v3.0[/]"
        + " " * 15
        + f"[bold {C_INFO}]║[/]"
    )
    console.print(f"[bold {C_INFO}]╚" + "═" * 68 + "╝[/]")

    # ─── Conceptos básicos ───
    _section(
        "MAFAHIM-E ASLI (Core Concepts)",
        [
            (
                "HUB (Iran)",
                "Server-e Irani ke script rooye on ejra mishe.\n"
                "Hamme traffic az inja vared mishe.\n"
                "frps rooye inja listen mikone.",
            ),
            (
                "NODE",
                "Server-e kharej (Kharej).\n"
                "Traffic be inja ferestade mishe.\n"
                "Mesal: Hetzner, Walter, Azure, DigitalOcean.",
            ),
            (
                "ROUTE (Masir)",
                "Yek masir: (port public rooye HUB) → (service rooye NODE).\n"
                "Mesal: :443 (Iran) → hetzner:443 (Xray).\n"
                "Har route yek ID dare mesl 'rt-443'.",
            ),
            (
                "CHANNEL (Kanal)",
                "Yek tunnel FRP bein HUB va yek NODE.\n"
                "Chand channel = chand tunnel parallel.\n"
                "Har channel yek bind-port rooye HUB dare.",
            ),
        ],
    )

    # ─── Two route modes ───
    _section(
        "DO NOE ROUTE",
        [
            (
                "SIMPLE ROUTE",
                "• 1 channel → yek node\n"
                "• Bedoone HAProxy\n"
                "• Baraye traffic-e kam ya test\n"
                "• Mesal: :8443 → hetzner:8443",
            ),
            (
                "BALANCED ROUTE",
                "• N channel (2-8) → yek ya chand node\n"
                "• Ba HAProxy (round-robin load balancing)\n"
                "• Baraye bandwidth-e bala va HA\n"
                "• Mesal: :443 → {hetzner, walter}:443 (6 channels)",
            ),
        ],
    )

    # ─── Wizard (NEW) ───
    _section(
        "WIZARD-E TARKIBI (Menu [2])",
        [
            (
                "In chie?",
                "Yek wizard ke Node + Route ra dar yek jaryan misaze.\n"
                "Baraye user-haye jadid ya setup-e sari'.",
            ),
            (
                "Che mode-ha dare?",
                "1) Quick — faghat 3 so'al, baghie auto\n"
                "2) Custom — kontrol-e kamel rooye hame chiz",
            ),
            (
                "Che misaze?",
                "1. Node (server kharej)\n"
                "2. Route (port public)\n"
                "3. Channel-ha (tunnel-ha)\n"
                "4. Systemd service-ha (auto-start)\n"
                "5. HAProxy config (age balanced bashe)",
            ),
            (
                "Che zaman estefade konam?",
                "• Avalin setup\n"
                "• Add-e node jadid be soorat-e sari'\n"
                "• Test-e configuration",
            ),
        ],
    )

    # ─── Workflow ───
    _section(
        "TARTIB-E KAR (Workflow)",
        [
            ("1. Install", "Menu [1] — FRP binary ra nasb kon."),
            (
                "2. Wizard ya Manual",
                "Menu [2] — Wizard (takhih)\n"
                "Ya: [3] Node + [4]/[5] Route be soorat-e joda.",
            ),
            ("3. Export", "Menu [7] — Config-e channel-ha ra baraye node begir."),
            ("4. Import on Node", "Rooye node: menu [8] — Compact ra paste kon."),
            ("5. Verify", "Menu [9] — Health check."),
        ],
    )

    # ─── Ports ───
    _section(
        "PORT-HA (Port Types)",
        [
            (
                "ENTRY PORT",
                "Port-e public rooye HUB.\n"
                "User be inja vasl mishe.\n"
                "Mesal: 443, 8443, 2083.",
            ),
            (
                "BIND PORT",
                "Port-e dakhli rooye HUB.\n"
                "frps rooye inja listen mikone.\n"
                "Auto-generated: 40000-65000.",
            ),
            (
                "REMOTE PORT",
                "Port-e dakhli rooye NODE.\n"
                "frps rooye inja expose mikone.\n"
                "Auto-generated: 20000-29999.",
            ),
            (
                "TARGET PORT",
                "Port-e service rooye NODE.\n"
                "Xray/service rooye inja listen mikone.\n"
                "User entekhab mikone (mesal: 443).",
            ),
            (
                "IPERF PORT",
                "Port-e test-e sor'at.\n"
                "Auto-generated: 55000-59999.",
            ),
        ],
    )

    # ─── Protocols ───
    _section(
        "PROTOCOL-HA",
        [
            (
                "TCP",
                "Sari-tarin va paydar-tarin.\n"
                "Baraye bishtar traffic.\n"
                "Pishnahad-e avval.",
            ),
            (
                "KCP",
                "UDP-based.\n"
                "Khob baraye network-e lossy.\n"
                "Masraf-e bandwidth-e bishtar.",
            ),
            (
                "QUIC",
                "Modern, UDP-based.\n"
                "Bandwidth-e bala + latency-e kam.\n"
                "Baraye network-e khoob.",
            ),
            (
                "WebSocket (WS)",
                "TCP-based, sazi ba HTTP.\n"
                "Baraye bypass firewall / CDN.\n"
                "Mesal: Cloudflare.",
            ),
        ],
    )

    # ─── FAQ ───
    _section(
        "SO'AL-HAYE MOTAVAJE (FAQ)",
        [
            (
                "Chand channel bezanam?",
                "Simple: 1\n"
                "Balanced: 3-6 (bishtar = bandwidth balatar)\n"
                "Bishtar az 8 = overhead ziyad",
            ),
            (
                "Che protocol estefade konam?",
                "Pishnahad: mix (2 TCP + 1 WS)\n"
                "Agar filter shode: WS ya QUIC\n"
                "Normal: TCP faghat",
            ),
            (
                "Chand node estefade konam?",
                "Multi-node = resistant-tar\n"
                "Agar yek node down shod, baghie kar mikonan\n"
                "Single-node = sade-tar",
            ),
            (
                "Age yek channel down shod?",
                "HAProxy khodesh failover mikone\n"
                "User chizi nemifahme\n"
                "Mitooni az menu [9] check koni",
            ),
            (
                "Cheghadr bandwidth daram?",
                "Be soorat-e theory: N × bandwidth-e har channel\n"
                "Amalan: ~70-90% az in\n"
                "Test kon ba menu [10]",
            ),
            (
                "Chetor tunnel ro delete konam?",
                "Menu [6] Manage Routes → [5] Delete\n"
                "Ya age node kamel mikhay pak she: Menu [3] → [3]",
            ),
        ],
    )

    # ─── Tips ───
    _section(
        "TIPS-E MOFID",
        [
            (
                "Baraye bandwidth-e bishtar",
                "1. Balanced route ba 4-6 channel\n"
                "2. Mix protocol: TCP + WS\n"
                "3. Multi-node (2-3 server)\n"
                "4. Optimize system: Menu [11]",
            ),
            (
                "Baraye bypass-e filter",
                "1. WebSocket ya QUIC\n"
                "2. Port 443 ya 8443\n"
                "3. CDN roosh (Cloudflare)",
            ),
            (
                "Baraye debug",
                "1. Menu [9] Health Check\n"
                "2. Menu [6] → Logs\n"
                "3. journalctl -u frps@ch-*-f",
            ),
        ],
    )

    # ─── Commands ───
    _section(
        "COMMAND-HAYE SARI'",
        [
            ("CLI", "sudo frp-cli — Classic menu"),
            ("TUI", "sudo frp-tui — Textual TUI (experimental)"),
            ("Wizard", "sudo frp-wizard — Direct wizard"),
            ("Uninstall", "sudo frp-uninstall — Uninstall menu"),
            ("Export", "sudo frp-export — Clean project ZIP"),
        ],
    )

    console.print()
    console.input(f"[{C_MUTED}]Enter bezan baraye bargasht...[/]")


def show_menu_help(menu_key: str) -> None:
    """Short help overlay for a specific menu."""
    help_map = {
        "main": (
            "Main Menu",
            [
                (
                    "In menu chie?",
                    "Menu-ye asli ke hame dastresi-ha az inja shoroo mishe.",
                ),
                (
                    "Tartib-e pishnahadi",
                    "1. [1] Install (aval)\n"
                    "2. [2] Wizard (baraye setup sari')\n"
                    "3. Ya manual: [3] Node + [4]/[5] Route\n"
                    "4. [7] Export + [8] Import\n"
                    "5. [9] Health check",
                ),
            ],
        ),
        "3": (
            "Manage Nodes",
            [
                (
                    "Node chie?",
                    "Server-e kharej ke traffic behesh mire.\n"
                    "Mesal: Hetzner (Germany), Walter (NL).",
                ),
                (
                    "Chetor add konam?",
                    "1. Name — esm-e yekta (hetzner, walter)\n"
                    "2. Host — IP ya domain\n"
                    "3. Location — ekhtiari\n"
                    "4. Note — ekhtiari",
                ),
                (
                    "Bad az add chi?",
                    "Az menu [4] (Simple) ya [5] (Balanced)\n"
                    "route besaz ke be in node bere.",
                ),
                (
                    "Age node ro pak konam?",
                    "Hame channel-hash ham pak mishan.\n"
                    "Route-haye marboote ham khali mishan.",
                ),
            ],
        ),
        "4": (
            "Create Simple Route",
            [
                (
                    "Simple Route chie?",
                    "1 channel baraye yek node.\nBedoone HAProxy.",
                ),
                (
                    "Che zaman estefade konam?",
                    "• Traffic-e kam\n• Test\n• Yek port-e sade",
                ),
                ("Che meghdar channel?", "Faghat 1 channel."),
                ("Mesal:", ":8443 rooye Iran → hetzner:8443 (Xray)"),
            ],
        ),
        "5": (
            "Create Balanced Route",
            [
                (
                    "Balanced Route chie?",
                    "N channel ba HAProxy.\nBandwidth-e bala + HA.",
                ),
                (
                    "Che zaman estefade konam?",
                    "• Bandwidth-e bala\n• Chand bar sari-tar\n• HA (age yek channel down shod)",
                ),
                ("Che meghdar channel?", "2-8 (pishnahad: 3-6)."),
                (
                    "Chand node?",
                    "Yek node ya chand node.\nMulti-node = resistant-tar.",
                ),
                ("Mesal:", ":443 → 3 ch be hetzner + 3 ch be walter"),
            ],
        ),
        "6": (
            "Manage Routes & Channels",
            [
                (
                    "Chi mitoonam bokonam?",
                    "• View / Restart / Stop / Delete route\n"
                    "• View channel-ha\n"
                    "• Logs-e har channel",
                ),
                (
                    "Chetori debug konam?",
                    "Route ra entekhab kon → [3] Logs → har channel log",
                ),
                (
                    "Delete-e route?",
                    "Route + hame channel-hash pak mishan.\n"
                    "Age balanced bashe, HAProxy rebuild mishe.",
                ),
            ],
        ),
        "7": (
            "Export Config for Node",
            [
                (
                    "Chi export mishe?",
                    "File-e compact shamel:\n"
                    "• channel name-ha\n"
                    "• IP-e HUB\n"
                    "• bind-port + token\n"
                    "• remote-port + target-port",
                ),
                (
                    "Chetori estefade konam?",
                    "File ra copy kon, rooye node az menu [8] paste kon.",
                ),
                ("Kojast?", "/opt/frp-manager/data/exports/<node>_compact.txt"),
            ],
        ),
        "8": (
            "Import Config on Node",
            [
                (
                    "In menu rooye chi ejra mishe?",
                    "ROOYE NODE (Kharej), na rooye HUB.",
                ),
                (
                    "Chetori?",
                    "Compact-e HUB ra paste kon.\n"
                    "Khodesh channel-ha ra misaze va start mikone.",
                ),
                (
                    "Age node nadare?",
                    "Khod script azat IP-e HUB ro miporse.",
                ),
            ],
        ),
        "9": (
            "Health Check",
            [
                (
                    "Chi check mishe?",
                    "• Systemd service-ha (frps/frpc)\n"
                    "• Listen-e bind-port-ha\n"
                    "• Online/OFFLINE-e har channel",
                ),
                (
                    "Che zaman?",
                    "• Ba'd az set-up\n"
                    "• Age chizi kar nakard\n"
                    "• Dore'i baraye monitoring",
                ),
            ],
        ),
        "10": (
            "iperf3 Speedtest",
            [
                (
                    "Chetori kar mikone?",
                    "1. Rooye node: server mode\n"
                    "2. Rooye hub: client test",
                ),
                (
                    "Chi bede?",
                    "Throughput (Mbps) rooye channel.\n"
                    "Mesal: 850 Mbps rooye TCP channel.",
                ),
                (
                    "Che zaman?",
                    "Ba'd az setup-e kamel, baraye test-e bandwidth.",
                ),
            ],
        ),
        "11": (
            "Optimize System",
            [
                (
                    "Chi avaz mishe?",
                    "• TCP BBR congestion control\n"
                    "• UDP buffer-ha\n"
                    "• Kernel limits (file descriptors)",
                ),
                (
                    "Che zaman?",
                    "Bad az nasb-e system.\n"
                    "Baraye bandwidth-e bala zaroori.",
                ),
            ],
        ),
        "12": (
            "Backup / Restore",
            [
                (
                    "Chi backup mishe?",
                    "• state.json (nodes, routes, channels)\n"
                    "• config-ha (frps/frpc toml)\n"
                    "• HAProxy config",
                ),
                ("Kojast?", "/opt/frp-manager/data/backups/backup_<timestamp>/"),
                (
                    "Restore-e cache?",
                    "Akharin backup ra peyda mikone.\n"
                    "Mitooni azash restore koni.",
                ),
            ],
        ),
        "13": (
            "Reset / Cleanup",
            [
                ("Khatar!", "In menu chiz-ha ra pak mikone."),
                (
                    "Gozine-ha:",
                    "1. Delete all routes (channel-ha ham)\n"
                    "2. Remove HAProxy only\n"
                    "3. Full reset",
                ),
                (
                    "Pishnahad:",
                    "Ghabl az reset, Menu [12] Backup begir.",
                ),
            ],
        ),
        "15": (
            "Rahnama (Help)",
            [
                (
                    "In chie?",
                    "Rahnama-ye kamel ba hame mafahim va mesal-ha.",
                ),
                (
                    "Che bakhsh-ha?",
                    "• Mafahim-e asli\n"
                    "• Do noe route\n"
                    "• Wizard\n"
                    "• Port-ha\n"
                    "• Protocol-ha\n"
                    "• FAQ",
                ),
            ],
        ),
        "16": (
            "Toggle Help Mode",
            [
                (
                    "Chi avaz mishe?",
                    "ON: hint-ha ziresh har menu neshoon dade mishan\n"
                    "OFF: faghat menu-ha (feshorde)",
                ),
                (
                    "Che zaman ON?",
                    "Baraye user-e jadid\n"
                    "Ya age yadet rafte har menu chi kare",
                ),
                (
                    "Che zaman OFF?",
                    "Baraye user-e karbala\n"
                    "Ya age screen-e kuchik dari",
                ),
            ],
        ),
        "17": (
            "Toggle Show IP",
            [
                (
                    "Chi avaz mishe?",
                    "ON: IP-e public rooye header neshoon dade mishe\n"
                    "OFF: makhfi mishe",
                ),
                (
                    "Che zaman OFF?",
                    "Age screen recording mikoni\n"
                    "Ya screenshot mikhay begiri",
                ),
            ],
        ),
        "18": (
            "Uninstall / Cleanup",
            [
                (
                    "Chi mikonan?",
                    "1. Stop all services\n"
                    "2. Remove HAProxy only\n"
                    "3. Reset all data\n"
                    "4. Full uninstall",
                ),
                (
                    "Che farghi dare?",
                    "[1] = faghat stop, [2] = HAProxy pak,\n"
                    "[3] = data pak, [4] = hame chiz",
                ),
                (
                    "Khatar!",
                    "Ba'd az [4], hich chizi namimone.\n"
                    "Ghabl az in, Menu [12] Backup begir.",
                ),
            ],
        ),
        "wizard": (
            "Combined Wizard",
            [
                (
                    "In chie?",
                    "Wizard-e kamel ke Node + Route ra dar yek jaryan misaze.",
                ),
                (
                    "Che mode-ha?",
                    "Quick: 3 so'al, baghie auto\n"
                    "Custom: kontrol-e kamel",
                ),
                (
                    "Che misaze?",
                    "• Node\n"
                    "• Route\n"
                    "• Channel-ha\n"
                    "• Systemd services\n"
                    "• HAProxy (age balanced bashe)",
                ),
                (
                    "Che zaman?",
                    "• Avalin setup\n"
                    "• Add-e node jadid be soorat-e sari'\n"
                    "• Test",
                ),
            ],
        ),
    }

    if menu_key not in help_map:
        console.print(f"[{C_WARNING}]Help baraye menu [{menu_key}] vojood nadare.[/]")
        return

    title, items = help_map[menu_key]
    console.clear()
    console.print()
    console.print(
        f"[bold {C_INFO}]╭─ 📖 Help: {title} "
        + "─" * max(0, 50 - len(title))
        + "╮[/]"
    )
    console.print()
    for key, val in items:
        console.print(f"  [bold {C_KHAREJ}]▸ {key}[/]")
        for line in val.split("\n"):
            console.print(f"    [{C_TITLE}]{line}[/]")
    console.print()
    console.input(f"[{C_MUTED}]Enter bezan baraye bargasht...[/]")
