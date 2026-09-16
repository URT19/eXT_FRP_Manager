"""Generate HAProxy config from Routes."""
from __future__ import annotations

from ..models import Route, Channel


GLOBAL_BLOCK = """\
# FRP Manager v3 - HAProxy Aggregation Config
# Auto-generated. Do not edit manually.

global
    log /dev/log local0 notice
    maxconn 100000
    tune.bufsize 32768
    tune.maxrewrite 1024
    nbthread 2
    cpu-map auto:1/1-2 0-1

defaults
    log     global
    mode    tcp
    option  tcplog
    option  dontlognull
    option  redispatch
    option  clitcpka
    option  srvtcpka
    timeout connect 5s
    timeout client  1h
    timeout server  1h
    timeout tunnel  1h
    timeout check   3s
    maxconn 50000
    retries 3
"""


def render(routes: list[Route], channels: dict[str, Channel]) -> str:
    """Each balanced route -> one frontend + one backend.

    Simple routes are NOT included here (frps handles them directly).
    """
    parts = [GLOBAL_BLOCK]

    for route in routes:
        if route.mode != "balanced":
            continue

        p = route.entry_port
        fe = f"fe_p{p}"
        be = f"be_p{p}"

        servers: list[str] = []
        node_groups: dict[str, int] = {}

        for ch_name in route.channels:
            ch = channels.get(ch_name)
            if not ch:
                continue
            node_groups[ch.node] = node_groups.get(ch.node, 0) + 1
            # For balanced route: HAProxy talks to frps on the *remote_port*
            # (the port frps exposes for the proxy on the Hub), NOT bind_port
            # (which is the control/agent port).
            servers.append(
                f"    server {ch.name} 127.0.0.1:{ch.remote_port} "
                f"check inter 3s fall 3 rise 2 weight 100"
            )

        summary = ", ".join(f"{n}×{c}" for n, c in node_groups.items())

        parts.append(f"""
# ============================================================
# Route  : {route.id}  (mode=balanced)
# Public : :{p}
# Nodes  : {summary}
# Channels: {len(route.channels)}
# ============================================================
frontend {fe}
    bind *:{p}
    mode tcp
    default_backend {be}

backend {be}
    mode tcp
    balance {route.balance}
    option tcp-check
{chr(10).join(servers)}
""")

    return "".join(parts)


def write(routes: list[Route], channels: dict[str, Channel], path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(routes, channels), encoding="utf-8")
