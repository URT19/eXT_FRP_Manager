"""Data models for FRP Manager v3.

Concepts:
    Node     — a Kharej server (remote target)
    Channel  — a single FRP tunnel
    Route    — a public port on the Hub mapped to one or more channels
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal

Protocol = Literal["tcp", "kcp", "quic", "ws"]
RouteMode = Literal["simple", "balanced"]
BalanceAlgo = Literal["roundrobin", "leastconn", "source"]


@dataclass
class Node:
    """A Kharej (foreign) server."""
    name: str
    host: str
    location: str = ""
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Node":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Channel:
    """A single FRP tunnel between Hub and one Node."""
    route_id: str          # e.g. "rt-443"
    node: str              # e.g. "hetzner"
    index: int             # 1, 2, 3...
    proto: Protocol
    bind_port: int         # on Hub (frps listen)
    token: str
    remote_port: int       # on Node (frps exposes)
    target_port: int       # Xray service on Node
    iperf_port: int = 0
    enabled: bool = True

    @property
    def name(self) -> str:
        return f"ch-{self.route_id.replace('rt-', '')}-{self.node}-{self.index:02d}"

    @property
    def frps_service(self) -> str:
        return f"frps@{self.name}.service"

    @property
    def frpc_service(self) -> str:
        return f"frpc@{self.name}.service"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["name"] = self.name
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Channel":
        return cls(**{k: v for k, v in d.items()
                      if k in cls.__dataclass_fields__})


@dataclass
class Route:
    """A public port on Hub mapped to one or more channels."""
    id: str                # "rt-443"
    entry_port: int        # public port on Hub
    mode: RouteMode        # "simple" | "balanced"
    channels: list[str] = field(default_factory=list)   # channel names
    balance: BalanceAlgo = "roundrobin"
    note: str = ""

    @property
    def nodes(self) -> list[str]:
        return list({ch.split("-")[2] for ch in self.channels
                     if ch.startswith("ch-")})

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Route":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
