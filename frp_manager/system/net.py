"""Network helpers: IP detect, port allocation, ufw."""
from __future__ import annotations

import random
import socket
import subprocess
import urllib.request
from typing import Optional

from ..constants import DEFAULT_PORT_RANGE


def detect_public_ip(timeout: int = 5) -> Optional[str]:
    endpoints = [
        "http://ip-api.com/line/?fields=query",
        "https://ifconfig.me/ip",
        "https://api.ipify.org",
    ]
    for url in endpoints:
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                ip = r.read().decode().strip()
                if ip:
                    return ip
        except Exception:
            continue
    return None


def detect_country_code(timeout: int = 5) -> Optional[str]:
    endpoints = [
        "http://ip-api.com/line/?fields=countryCode",
        "https://ifconfig.co/country-iso",
    ]
    for url in endpoints:
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                cc = r.read().decode().strip()
                if cc:
                    return cc
        except Exception:
            continue
    return None


def is_port_free(port: int, host: str = "0.0.0.0") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def random_free_port(start: int | None = None, end: int | None = None,
                     max_tries: int = 50) -> int:
    lo = start or DEFAULT_PORT_RANGE[0]
    hi = end or DEFAULT_PORT_RANGE[1]
    for _ in range(max_tries):
        p = random.randint(lo, hi)
        if is_port_free(p):
            return p
    raise RuntimeError(f"No free port found in {lo}-{hi}")


def ufw_allow(port: int, proto: str = "tcp") -> None:
    try:
        r = subprocess.run(["ufw", "status"], capture_output=True, text=True)
        if "Status: active" in r.stdout:
            subprocess.run(["ufw", "allow", f"{port}/{proto}"],
                           capture_output=True)
    except FileNotFoundError:
        pass