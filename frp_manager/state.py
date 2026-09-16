"""Centralized state management for FRP Manager v3."""
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
from .models import Node, Channel, Route


def ensure_dirs() -> None:
    for d in (DATA_DIR, CONFIG_DIR, LOG_DIR, BACKUP_DIR, EXPORT_DIR, HAPROXY_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _fresh_state() -> dict:
    return {"nodes": {}, "routes": {}, "channels": {}, "meta": {"version": 3}}


def load() -> dict:
    ensure_dirs()
    if not STATE_FILE.exists():
        return _fresh_state()
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        # Auto-migrate from v2 (peers/tunnels/rules) if detected
        if "peers" in data and "nodes" not in data:
            return _fresh_state()   # start fresh, keep old as .old file
        # Fill missing keys
        for k in ("nodes", "routes", "channels", "meta"):
            data.setdefault(k, {} if k != "meta" else {})
        return data
    except Exception:
        bak = STATE_FILE.with_suffix(f".corrupt.{int(datetime.now().timestamp())}")
        shutil.copy(STATE_FILE, bak)
        return _fresh_state()


def save(state: dict) -> None:
    ensure_dirs()
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ───── Node helpers ─────

def add_node(state: dict, node: Node) -> None:
    state.setdefault("nodes", {})[node.name] = node.to_dict()


def get_node(state: dict, name: str) -> Optional[Node]:
    d = state.get("nodes", {}).get(name)
    return Node.from_dict(d) if d else None


def list_nodes(state: dict) -> list[Node]:
    return [Node.from_dict(d) for d in state.get("nodes", {}).values()]


def remove_node(state: dict, name: str) -> list[str]:
    """Remove node + all its channels. Returns removed channel names."""
    removed = []
    for cname, c in list(state.get("channels", {}).items()):
        if c["node"] == name:
            removed.append(cname)
            del state["channels"][cname]
    for r in state.get("routes", {}).values():
        r["channels"] = [c for c in r["channels"] if c not in removed]
    state.get("nodes", {}).pop(name, None)
    return removed


# ───── Route helpers ─────

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


def list_routes(state: dict) -> list[Route]:
    out = [Route.from_dict(d) for d in state.get("routes", {}).values()]
    out.sort(key=lambda r: r.entry_port)
    return out


def remove_route(state: dict, rid: str) -> list[str]:
    """Remove route + all its channels. Returns removed channel names."""
    r = get_route(state, rid)
    if not r:
        return []
    removed = list(r.channels)
    for cname in removed:
        state.get("channels", {}).pop(cname, None)
    state.get("routes", {}).pop(rid, None)
    return removed


# ───── Channel helpers ─────

def add_channel(state: dict, ch: Channel) -> None:
    state.setdefault("channels", {})[ch.name] = ch.to_dict()


def get_channel(state: dict, name: str) -> Optional[Channel]:
    d = state.get("channels", {}).get(name)
    return Channel.from_dict(d) if d else None


def list_channels(state: dict, route_id: str | None = None,
                  node: str | None = None) -> list[Channel]:
    out = []
    for d in state.get("channels", {}).values():
        c = Channel.from_dict(d)
        if route_id and c.route_id != route_id:
            continue
        if node and c.node != node:
            continue
        out.append(c)
    out.sort(key=lambda c: (c.route_id, c.node, c.index))
    return out


def next_channel_index(state: dict, route_id: str, node: str) -> int:
    max_i = 0
    for c in list_channels(state, route_id=route_id, node=node):
        max_i = max(max_i, c.index)
    return max_i + 1


# ───── All-in-one removal ─────

def remove_all(state: dict) -> None:
    state.clear()
    state.update(_fresh_state())
