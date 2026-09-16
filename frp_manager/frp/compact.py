"""Compact format for Hub -> Node config transfer.

Format (CSV, one per line):
    name,route_id,node,index,proto,bindPort,token,remotePort,targetPort,iperfPort
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ..constants import EXPORT_DIR
from ..models import Channel


HEADER = "# FRP Manager Compact v3"
# Column order:
#   hub_ip, name, route_id, node, index, proto, bind_port,
#   token, remote_port, target_port, iperf_port
FIELDS = ["hub_ip", "name", "route_id", "node", "index", "proto",
          "bind_port", "token", "remote_port", "target_port", "iperf_port"]


def to_line(ch: Channel, hub_ip: str = "") -> str:
    """Serialize one channel.

    Format:
        hub_ip,name,route_id,node,index,proto,bindPort,token,
        remotePort,targetPort,iperfPort

    hub_ip may be empty for backward-compat (import will fall back to header).
    """
    return ",".join(str(x) for x in [
        hub_ip, ch.name, ch.route_id, ch.node, ch.index, ch.proto,
        ch.bind_port, ch.token, ch.remote_port, ch.target_port, ch.iperf_port,
    ])


def from_line(line: str) -> Channel | None:
    """Parse one compact line.

    Accepts:
      - 11-column (new): hub_ip,name,route,node,index,proto,bind,token,remote,target,iperf
      - 10-column (old): name,route,node,index,proto,bind,token,remote,target,iperf
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    parts = [p.strip() for p in line.split(",")]

    try:
        if len(parts) == 11:
            # New format: hub_ip first
            hub_ip = parts[0]
            name, route_id, node, index, proto = parts[1:6]
            bind_port, token, remote_port, target_port, iperf_port = parts[6:11]
        elif len(parts) == 10:
            # Old format: no hub_ip
            name, route_id, node, index, proto = parts[0:5]
            bind_port, token, remote_port, target_port, iperf_port = parts[5:10]
        else:
            return None

        return Channel(
            route_id=route_id,
            node=node,
            index=int(index),
            proto=proto,           # type: ignore
            bind_port=int(bind_port),
            token=token,
            remote_port=int(remote_port),
            target_port=int(target_port),
            iperf_port=int(iperf_port) if iperf_port else 0,
        )
    except (ValueError, IndexError):
        return None


def extract_hub_ip_from_line(line: str) -> str:
    """Return hub_ip if present in the first column of an 11-column line."""
    import re
    line = line.strip()
    if not line or line.startswith("#"):
        return ""
    parts = [p.strip() for p in line.split(",")]
    if len(parts) == 11 and re.match(r"^\d{1,3}(\.\d{1,3}){3}$", parts[0]):
        return parts[0]
    return ""


def export_channels(channels: Iterable[Channel], node_name: str,
                    hub_ip: str = "") -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = EXPORT_DIR / f"{node_name}_compact.txt"
    lines = [
        HEADER,
        f"# Node = {node_name}",
        f"# HUB_IP = {hub_ip}",
        f"# Format: HUB_IP,name,route_id,node,index,proto,bindPort,token,remotePort,targetPort,iperfPort",
        "",
    ]
    for ch in channels:
        lines.append(to_line(ch, hub_ip))
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def import_lines(text: str) -> list[Channel]:
    out: list[Channel] = []
    for line in text.splitlines():
        ch = from_line(line)
        if ch:
            out.append(ch)
    return out


def extract_hub_ip_anywhere(text: str) -> str:
    """Extract hub_ip from anywhere: header comment OR first data line."""
    # 1) Try header comment: # HUB_IP = 1.2.3.4
    from_header = extract_hub_ip(text)
    if from_header:
        return from_header
    # 2) Try first data line column 0
    for line in text.splitlines():
        ip = extract_hub_ip_from_line(line)
        if ip:
            return ip
    return ""


def extract_hub_ip(text: str) -> str:
    """Extract HUB_IP from compact header if present.

    Formats supported:
        # HUB_IP = 1.2.3.4
        # HUB_IP=1.2.3.4
    """
    import re
    m = re.search(r"^#\s*HUB_IP\s*=\s*([0-9.]+)", text, re.MULTILINE)
    return m.group(1) if m else ""


def extract_node_name(text: str) -> str:
    """Extract Node name from compact header if present.

    Formats supported:
        # Node = name
        # Node=name
    """
    import re
    m = re.search(r"^#\s*Node\s*=\s*([a-zA-Z0-9\-]+)", text, re.MULTILINE)
    return m.group(1) if m else ""


def read_file(path: Path) -> list[Channel]:
    return import_lines(path.read_text(encoding="utf-8"))
