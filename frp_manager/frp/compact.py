"""Compact format for eXT FRP Manager v3.2 (Hub-aware).

Format:
    HubName,HubIP,ChannelName,RouteID,Index,Proto,BindPort,Token,RemotePort,TargetPort,IperfPort

Example:
    iran-1,203.0.113.10,ch-443-iran-1-01,rt-443,1,tcp,48260,TOKEN_A,20043,443,55443

The Hub name appears at the start of each line so importers can group
channels under the right Hub.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from ..constants import EXPORT_DIR
from ..models import Channel


HEADER = "# eXT FRP Compact v3.2"
FIELDS = [
    "hub_name", "hub_ip", "channel_name", "route_id", "index",
    "proto", "bind_port", "token", "remote_port", "target_port", "iperf_port",
]


# ═══════════════════════════════════════════════════════════════════════
#  Line serialization
# ═══════════════════════════════════════════════════════════════════════

def to_line(ch, hub_name: str, hub_ip: str) -> str:
    """Serialize one channel to a compact CSV line."""
    return ",".join(str(x) for x in [
        hub_name,
        hub_ip,
        ch.name,
        ch.route_id,
        ch.index,
        ch.proto,
        ch.bind_port,
        ch.token,
        ch.remote_port,
        ch.target_port,
        ch.iperf_port or 0,
    ])


def from_line(line: str) -> dict | None:
    """Parse one compact line.

    Returns dict with keys: hub_name, hub_ip, channel, or None if invalid.
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    parts = [p.strip() for p in line.split(",")]

    # New format: 11 fields
    if len(parts) == 11:
        try:
            hub_name = parts[0]
            hub_ip = parts[1]
            channel = Channel(
                route_id=parts[3],
                hub=hub_name,
                index=int(parts[4]),
                proto=parts[5],           # type: ignore
                bind_port=int(parts[6]),
                token=parts[7],
                remote_port=int(parts[8]),
                target_port=int(parts[9]),
                iperf_port=int(parts[10]) if parts[10] else 0,
            )
            return {
                "hub_name": hub_name,
                "hub_ip": hub_ip,
                "channel": channel,
            }
        except (ValueError, IndexError):
            return None

    # Legacy format: 10 fields (old v3.0)
    if len(parts) == 10:
        try:
            channel = Channel(
                route_id=parts[1],
                hub=parts[2],
                index=int(parts[3]),
                proto=parts[4],           # type: ignore
                bind_port=int(parts[5]),
                token=parts[6],
                remote_port=int(parts[7]),
                target_port=int(parts[8]),
                iperf_port=int(parts[9]) if parts[9] else 0,
            )
            return {
                "hub_name": parts[2],   # fallback to old node field
                "hub_ip": "",
                "channel": channel,
            }
        except (ValueError, IndexError):
            return None

    return None


# ═══════════════════════════════════════════════════════════════════════
#  Export
# ═══════════════════════════════════════════════════════════════════════

def export_channels(channels: Iterable[Channel], hub_name: str,
                    hub_ip: str = "") -> Path:
    """Export channels for a specific hub to a compact file."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = EXPORT_DIR / f"{hub_name}_compact.txt"

    channels = list(channels)

    # Determine type
    if len(channels) <= 1:
        hub_type = "simple"
    else:
        hub_type = "balanced"

    lines = [
        HEADER,
        f"# HubName = {hub_name}",
        f"# HubIP = {hub_ip}",
        f"# Channels = {len(channels)}",
        f"# Type = {hub_type}",
        f"# Format: HubName,HubIP,ChannelName,RouteID,Index,Proto,BindPort,Token,RemotePort,TargetPort,IperfPort",
        "",
    ]
    for ch in channels:
        lines.append(to_line(ch, hub_name, hub_ip))
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


# ═══════════════════════════════════════════════════════════════════════
#  Import
# ═══════════════════════════════════════════════════════════════════════

def parse_compact(text: str) -> dict:
    """Parse a full compact text.

    Returns:
        {
            "meta": {
                "hub_name": str,
                "hub_ip": str,
                "type": "simple" | "balanced",
                "channels_count": int,
            },
            "lines": [ {hub_name, hub_ip, channel}, ... ],
            "errors": [ str, ... ],
        }
    """
    meta = {
        "hub_name": "",
        "hub_ip": "",
        "type": "simple",
        "channels_count": 0,
    }
    lines = []
    errors = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # ─── Parse metadata comments ───
        if line.startswith("#"):
            m = re.match(r"^#\s*HubName\s*=\s*(\S+)", line)
            if m:
                meta["hub_name"] = m.group(1)
                continue
            m = re.match(r"^#\s*HubIP\s*=\s*(\S+)", line)
            if m:
                meta["hub_ip"] = m.group(1)
                continue
            m = re.match(r"^#\s*Type\s*=\s*(\S+)", line)
            if m:
                meta["type"] = m.group(1)
                continue
            # Other comments ignored
            continue

        # ─── Parse data line ───
        parsed = from_line(line)
        if parsed:
            lines.append(parsed)
        else:
            errors.append(f"Invalid line: {line[:60]}")

    meta["channels_count"] = len(lines)

    # Auto-detect type if not set
    if not meta["type"] or meta["type"] not in ("simple", "balanced"):
        meta["type"] = "balanced" if len(lines) > 1 else "simple"

    # Auto-fill hub info from first line if missing
    if lines and not meta["hub_name"]:
        meta["hub_name"] = lines[0]["hub_name"]
    if lines and not meta["hub_ip"]:
        meta["hub_ip"] = lines[0]["hub_ip"]

    return {
        "meta": meta,
        "lines": lines,
        "errors": errors,
    }


def import_lines(text: str) -> list[Channel]:
    """Backward-compatible: return just the Channel objects."""
    result = parse_compact(text)
    return [item["channel"] for item in result["lines"]]


def read_file(path: Path) -> list[Channel]:
    return import_lines(path.read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════

def extract_hub_ip(text: str) -> str:
    """Extract HUB_IP from compact header (legacy support)."""
    m = re.search(r"^#\s*HUB_IP\s*=\s*([0-9.]+)", text, re.MULTILINE)
    if m:
        return m.group(1)
    m = re.search(r"^#\s*HubIP\s*=\s*([0-9.]+)", text, re.MULTILINE)
    if m:
        return m.group(1)
    return ""


def extract_hub_name(text: str) -> str:
    """Extract HubName from compact header."""
    m = re.search(r"^#\s*HubName\s*=\s*(\S+)", text, re.MULTILINE)
    return m.group(1) if m else ""


def extract_hub_ip_anywhere(text: str) -> str:
    """Extract hub IP from header or first data line."""
    ip = extract_hub_ip(text)
    if ip:
        return ip
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2 and re.match(r"^\d{1,3}(\.\d{1,3}){3}$", parts[1]):
            return parts[1]
    return ""
