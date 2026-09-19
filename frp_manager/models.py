"""Data models for eXT FRP Manager v3.4.

Concepts:
    Hub      - a remote server the local machine connects to
    Channel  - a single FRP tunnel between Hub and Node
    Route    - a public port on the Hub mapped to channels

Hub roles:
    IRAN_SERVER   - a Hub that IS an Iran server (frps side)
                    -> used on Kharej to define which Iran to connect to
    KHAREJ_SERVER - a Hub that IS a Kharej server (frpc side)
                    -> used on Iran to define which Kharej to serve
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal

Protocol = Literal["tcp", "kcp", "quic", "ws"]
HubRole = Literal["iran_server", "kharej_server"]
HubType = Literal["simple", "balanced", "manual"]
RouteMode = Literal["simple", "balanced"]
BalanceAlgo = Literal["roundrobin", "leastconn", "source"]


# ═══════════════════════════════════════════════════════════════════════
#  Hub role metadata
# ═══════════════════════════════════════════════════════════════════════

ROLE_META = {
    "iran_server": {
        "badge": "IRAN Server (frps)",
        "color": "#f5d76e",       # yellow
        "menu_title": "Modiriyat Server-e IRAN",
        "what": "Server-e IRAN (frps) — inja behesh vasl mishim",
        "example": "iran-1, iran-hub-216, 115-1",
        "workflow": [
            "1. Inja Server-e IRAN ra add kon (esm + IP)",
            "2. Az menu [8] Import, compact-e IRAN ra paste kon",
            "3. Channel-ha khodkar be in Hub vasl mishan",
        ],
    },
    "kharej_server": {
        "badge": "KHAREJ Server (frpc)",
        "color": "#56d4dd",       # cyan
        "menu_title": "Modiriyat Server-e KHAREJ",
        "what": "Server-e KHAREJ (frpc) — inja behesh service midim",
        "example": "germany-1, hetzner-2, frankfurt-a",
        "workflow": [
            "1. Inja Server-e KHAREJ ra add kon (esm + IP)",
            "2. Az menu [4] ya [5], yek Route besaz baraye in Hub",
            "3. Az menu [7] Export kon, compact ro rooye Kharej import kon",
        ],
    },
}


@dataclass
class Hub:
    """A remote Hub server.

    On IRAN:  Hub.role = "kharej_server"  (this is a Kharej we serve)
    On KHAREJ: Hub.role = "iran_server"    (this is an Iran we connect to)
    """
    name: str
    host: str
    role: HubRole = "iran_server"
    location: str = ""
    note: str = ""
    type: HubType = "simple"
    routes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Hub":
        data = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        data.setdefault("role", "iran_server")
        data.setdefault("type", "simple")
        data.setdefault("routes", [])
        return cls(**data)

    @property
    def role_meta(self) -> dict:
        return ROLE_META.get(self.role, ROLE_META["iran_server"])


# Backward-compat alias
Node = Hub


@dataclass
class Channel:
    """A single FRP tunnel between Hub and one Node/Hub."""
    route_id: str
    hub: str
    index: int
    proto: Protocol
    bind_port: int
    token: str
    remote_port: int
    target_port: int
    iperf_port: int = 0
    enabled: bool = True

    @property
    def name(self) -> str:
        return f"ch-{self.route_id.replace('rt-', '')}-{self.hub}-{self.index:02d}"

    @property
    def frps_service(self) -> str:
        return f"frps@{self.name}.service"

    @property
    def frpc_service(self) -> str:
        return f"frpc@{self.name}.service"

    @property
    def node(self) -> str:
        return self.hub

    def to_dict(self) -> dict:
        d = asdict(self)
        d["name"] = self.name
        d["node"] = self.hub
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Channel":
        if "hub" not in d and "node" in d:
            d = dict(d)
            d["hub"] = d["node"]
        data = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**data)


@dataclass
class Route:
    """A public port on Hub mapped to one or more channels."""
    id: str
    entry_port: int
    mode: RouteMode
    channels: list = field(default_factory=list)
    balance: BalanceAlgo = "roundrobin"
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Route":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
