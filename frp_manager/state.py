"""Centralized state management for eXT FRP Manager v3.2."""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from .constants import (
    STATE_FILE, DATA_DIR, CONFIG_DIR, LOG_DIR,
    BACKUP_DIR, EXPORT_DIR, HAPROXY_DIR,
)
from .models import Hub, Channel, Route


def ensure_dirs() -> None:
    for d in (DATA_DIR, CONFIG_DIR, LOG_DIR, BACKUP_DIR, EXPORT_DIR, HAPROXY_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _fresh_state() -> dict:
    return {
        "hubs": {},
        "routes": {},
        "channels": {},
        "meta": {"version": 4},
    }


def _migrate_v3_to_v4(data: dict) -> dict:
    if "nodes" in data and "hubs" not in data:
        data["hubs"] = data.pop("nodes")
    for cname, ch in data.get("channels", {}).items():
        if "node" in ch and "hub" not in ch:
            ch["hub"] = ch["node"]
    for hname, hub in data.get("hubs", {}).items():
        hub.setdefault("type", "simple")
        hub.setdefault("routes", [])
    data.setdefault("meta", {})["version"] = 4
    return data


def load() -> dict:
    ensure_dirs()
    if not STATE_FILE.exists():
        return _fresh_state()
    try:
        raw = STATE_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
        version = data.get("meta", {}).get("version", 3)
        if version < 4 or ("nodes" in data and "hubs" not in data):
            bak = STATE_FILE.with_suffix(
                f".pre-migrate.{int(datetime.now().timestamp())}.json"
            )
            shutil.copy(STATE_FILE, bak)
            data = _migrate_v3_to_v4(data)
            save(data)
        for k in ("hubs", "routes", "channels"):
            data.setdefault(k, {})
        data.setdefault("meta", {})
        return data
    except Exception:
        bak = STATE_FILE.with_suffix(f".corrupt.{int(datetime.now().timestamp())}")
        try:
            shutil.copy(STATE_FILE, bak)
        except Exception:
            pass
        return _fresh_state()


def save(state: dict) -> None:
    ensure_dirs()
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def add_hub(state: dict, hub: Hub) -> None:
    state.setdefault("hubs", {})[hub.name] = hub.to_dict()


def get_hub(state: dict, name: str) -> Optional[Hub]:
    d = state.get("hubs", {}).get(name)
    return Hub.from_dict(d) if d else None


def list_hubs(state: dict) -> list:
    return [Hub.from_dict(d) for d in state.get("hubs", {}).values()]


def remove_hub(state: dict, name: str) -> list:
    removed = []
    for cname, c in list(state.get("channels", {}).items()):
        if c.get("hub") == name or c.get("node") == name:
            removed.append(cname)
            del state["channels"][cname]
    for r in state.get("routes", {}).values():
        r["channels"] = [c for c in r["channels"] if c not in removed]
    state.get("hubs", {}).pop(name, None)
    return removed


add_node = add_hub
get_node = get_hub
list_nodes = list_hubs
remove_node = remove_hub


def add_route(state: dict, route: Route) -> None:
    state.setdefault("routes", {})[route.id] = route.to_dict()


def get_route(state: dict, rid: str) -> Optional[Route]:
    d = state.get("routes", {}).get(rid)
    return Route.from_dict(d) if d else None


def get_route_by_port(state: dict, port: int) -> Optional[Route]:
    for d in state.get("routes", {}).values():
        if d["entry_port"] == port:
            return Route.from_dict(d)
    return None


def list_routes(state: dict) -> list:
    out = [Route.from_dict(d) for d in state.get("routes", {}).values()]
    out.sort(key=lambda r: r.entry_port)
    return out


def remove_route(state: dict, rid: str) -> list:
    r = get_route(state, rid)
    if not r:
        return []
    removed = list(r.channels)
    for cname in removed:
        state.get("channels", {}).pop(cname, None)
    state.get("routes", {}).pop(rid, None)
    return removed


def add_channel(state: dict, ch: Channel) -> None:
    state.setdefault("channels", {})[ch.name] = ch.to_dict()


def get_channel(state: dict, name: str) -> Optional[Channel]:
    d = state.get("channels", {}).get(name)
    return Channel.from_dict(d) if d else None


def list_channels(state: dict, route_id=None, hub=None, node=None) -> list:
    filter_name = hub or node
    out = []
    for d in state.get("channels", {}).values():
        c = Channel.from_dict(d)
        if route_id and c.route_id != route_id:
            continue
        if filter_name and c.hub != filter_name:
            continue
        out.append(c)
    out.sort(key=lambda c: (c.route_id, c.hub, c.index))
    return out


def next_channel_index(state: dict, route_id: str, hub: str) -> int:
    max_i = 0
    for c in list_channels(state, route_id=route_id, hub=hub):
        max_i = max(max_i, c.index)
    return max_i + 1


def remove_all(state: dict) -> None:
    state.clear()
    state.update(_fresh_state())


def group_channels_by_hub(state: dict) -> dict:
    groups = {}
    for c in list_channels(state):
        groups.setdefault(c.hub, []).append(c)
    return groups


def hub_summary(state: dict, hub_name: str) -> dict:
    from .system import systemd
    channels = list_channels(state, hub=hub_name)
    summary = {
        "total": len(channels),
        "online": 0,
        "offline": 0,
        "by_proto": {"tcp": 0, "kcp": 0, "quic": 0, "ws": 0},
        "routes": sorted({c.target_port for c in channels}),
    }
    for c in channels:
        if systemd.is_active(c.frps_service) or systemd.is_active(c.frpc_service):
            summary["online"] += 1
        else:
            summary["offline"] += 1
        if c.proto in summary["by_proto"]:
            summary["by_proto"][c.proto] += 1
    return summary
