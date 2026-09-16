"""Defaults / bandwidth profile / UI lang."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

import tomli_w

from .constants import DEFAULTS_FILE, BW_PROFILES, DEFAULT_PORT_RANGE, DEFAULT_TOKEN_LENGTH


@dataclass
class Defaults:
    bw_profile: str = "1.5G"
    pool_count: int = 80
    max_pool_count: int = 150
    token_length: int = DEFAULT_TOKEN_LENGTH
    port_range_start: int = DEFAULT_PORT_RANGE[0]
    port_range_end: int = DEFAULT_PORT_RANGE[1]
    tcpmux: bool = False
    heartbeat_interval: int = 30
    heartbeat_timeout: int = 90
    ui_lang: str = "finglish"
    help_mode: bool = False
    show_ip: bool = True
    advanced_mode: bool = True

    def apply_profile(self, profile: str) -> None:
        if profile not in BW_PROFILES:
            return
        p = BW_PROFILES[profile]
        self.bw_profile = profile
        self.pool_count = p["pool_count"]
        self.max_pool_count = p["max_pool_count"]
        self.tcpmux = p["tcpmux"]
        self.heartbeat_interval = p["heartbeat_interval"]
        self.heartbeat_timeout = p["heartbeat_timeout"]

    def to_dict(self) -> dict:
        return asdict(self)


def load_defaults() -> Defaults:
    if DEFAULTS_FILE.exists():
        try:
            data = tomllib.loads(DEFAULTS_FILE.read_text(encoding="utf-8"))
            return Defaults(**{k: v for k, v in data.items()
                               if k in Defaults.__dataclass_fields__})
        except Exception:
            pass
    d = Defaults()
    save_defaults(d)
    return d


def save_defaults(d: Defaults) -> None:
    DEFAULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    DEFAULTS_FILE.write_text(tomli_w.dumps(d.to_dict()), encoding="utf-8")