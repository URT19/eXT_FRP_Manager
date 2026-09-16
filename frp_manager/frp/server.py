"""Generate frps config + systemd template unit."""
from __future__ import annotations

from pathlib import Path

from ..constants import CONFIG_DIR, SYSTEMD_DIR
from ..models import Channel


def frps_config_path(ch: Channel) -> Path:
    return CONFIG_DIR / f"frps_{ch.name}.toml"


def render_frps_toml(ch: Channel, max_pool: int = 150,
                     tcpmux: bool = False, heartbeat_timeout: int = 90) -> str:
    lines = [
        f'# Channel_Name = "{ch.name}"',
        f"# Protocol     = {ch.proto.upper()}",
        f"# Node         = {ch.node}",
        f"# Route        = {ch.route_id}",
        'bindAddr = "0.0.0.0"',
        f"bindPort = {ch.bind_port}",
    ]
    if ch.proto == "kcp":
        lines.append(f"kcpBindPort = {ch.bind_port}")
    elif ch.proto == "quic":
        lines.append(f"quicBindPort = {ch.bind_port}")

    lines += [
        'auth.method = "token"',
        f'auth.token = "{ch.token}"',
        f"transport.tcpMux = {'true' if tcpmux else 'false'}",
        f"transport.maxPoolCount = {max_pool}",
        f"transport.heartbeatTimeout = {heartbeat_timeout}",
    ]
    return "\n".join(lines) + "\n"


def write_frps_config(ch: Channel, max_pool: int = 150,
                     tcpmux: bool = False, heartbeat_timeout: int = 90) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    p = frps_config_path(ch)
    p.write_text(render_frps_toml(ch, max_pool, tcpmux, heartbeat_timeout),
                 encoding="utf-8")
    return p


def write_frps_unit() -> Path:
    unit = SYSTEMD_DIR / "frps@.service"
    unit.write_text("""[Unit]
Description=FRP Server Channel %i
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
ExecStart=/usr/local/bin/frps -c /opt/frp-manager/data/configs/frps_%i.toml
Restart=always
RestartSec=10s
LimitNOFILE=1048576
TimeoutStopSec=10s

[Install]
WantedBy=multi-user.target
""", encoding="utf-8")
    return unit


def delete_frps_config(ch: Channel) -> None:
    p = frps_config_path(ch)
    if p.exists():
        p.unlink()
