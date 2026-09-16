"""Generate frpc config + systemd template unit."""
from __future__ import annotations

from pathlib import Path

from ..constants import CONFIG_DIR, SYSTEMD_DIR
from ..models import Channel, Node


def frpc_config_path(ch: Channel) -> Path:
    return CONFIG_DIR / f"frpc_{ch.name}.toml"


def render_frpc_toml(ch: Channel, node: Node,
                     pool_count: int = 80,
                     tcpmux: bool = False,
                     heartbeat_interval: int = 30,
                     heartbeat_timeout: int = 90) -> str:
    lines = [
        f'# Channel_Name = "{ch.name}"',
        f"# Protocol     = {ch.proto.upper()}",
        f"# Node         = {ch.node}",
        f"# Route        = {ch.route_id}",
        f'serverAddr = "{node.host}"',
        f"serverPort = {ch.bind_port}",
        'auth.method = "token"',
        f'auth.token = "{ch.token}"',
        f"transport.tcpMux = {'true' if tcpmux else 'false'}",
        f"transport.poolCount = {pool_count}",
        f"transport.heartbeatInterval = {heartbeat_interval}",
        f"transport.heartbeatTimeout = {heartbeat_timeout}",
    ]

    if ch.proto == "kcp":
        lines.append('transport.protocol = "kcp"')
    elif ch.proto == "quic":
        lines.append('transport.protocol = "quic"')
    elif ch.proto == "ws":
        lines.append('transport.protocol = "websocket"')

    lines += [
        "",
        "# Service proxy",
        "[[proxies]]",
        f'name = "{ch.name}_svc"',
        'type = "tcp"',
        'localIP = "127.0.0.1"',
        f"localPort = {ch.target_port}",
        f"remotePort = {ch.remote_port}",
    ]

    if ch.iperf_port:
        lines += [
            "",
            "# iperf3 test port",
            "[[proxies]]",
            f'name = "{ch.name}_iperf"',
            'type = "tcp"',
            'localIP = "127.0.0.1"',
            f"localPort = {ch.iperf_port}",
            f"remotePort = {ch.iperf_port}",
        ]

    return "\n".join(lines) + "\n"


def write_frpc_config(ch: Channel, node: Node,
                     pool_count: int = 80,
                     tcpmux: bool = False,
                     heartbeat_interval: int = 30,
                     heartbeat_timeout: int = 90) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    p = frpc_config_path(ch)
    p.write_text(
        render_frpc_toml(ch, node, pool_count, tcpmux,
                         heartbeat_interval, heartbeat_timeout),
        encoding="utf-8",
    )
    return p


def write_frpc_unit() -> Path:
    unit = SYSTEMD_DIR / "frpc@.service"
    unit.write_text("""[Unit]
Description=FRP Client Channel %i
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
ExecStart=/usr/local/bin/frpc -c /opt/frp-manager/data/configs/frpc_%i.toml
Restart=always
RestartSec=10s
LimitNOFILE=1048576
TimeoutStopSec=10s

[Install]
WantedBy=multi-user.target
""", encoding="utf-8")
    return unit


def delete_frpc_config(ch: Channel) -> None:
    p = frpc_config_path(ch)
    if p.exists():
        p.unlink()
