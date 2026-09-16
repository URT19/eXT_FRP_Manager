"""Tunnel naming conventions and helpers.

Format: {proto}_{peer}_{group_port}_{index:02d}
Example: tcp_hetzner_443_01
"""
from __future__ import annotations
import re
from typing import Optional

NAME_RE = re.compile(
    r"^(?P<proto>tcp|kcp|quic|ws)_(?P<peer>[a-zA-Z0-9\-]+)_(?P<port>\d{1,5})_(?P<idx>\d{2})$"
)


def make_name(proto: str, peer: str, group_port: int, index: int) -> str:
    return f"{proto}_{peer}_{group_port}_{index:02d}"


def parse_name(name: str) -> Optional[dict]:
    m = NAME_RE.match(name)
    if not m:
        return None
    return {
        "proto": m.group("proto"),
        "peer": m.group("peer"),
        "group_port": int(m.group("port")),
        "index": int(m.group("idx")),
    }


def next_index(existing_names: list[str], proto: str, peer: str, group_port: int) -> int:
    max_i = 0
    for n in existing_names:
        p = parse_name(n)
        if not p:
            continue
        if p["proto"] == proto and p["peer"] == peer and p["group_port"] == group_port:
            max_i = max(max_i, p["index"])
    return max_i + 1


def validate_peer_name(name: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9\-]{2,32}$", name))