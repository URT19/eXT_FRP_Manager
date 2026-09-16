"""Generic systemd helpers."""
from __future__ import annotations

import subprocess
from pathlib import Path

from ..constants import SYSTEMD_DIR


def daemon_reload() -> None:
    subprocess.run(["systemctl", "daemon-reload"], check=False)


def service_action(name: str, action: str) -> bool:
    r = subprocess.run(["systemctl", action, name],
                       capture_output=True, text=True)
    return r.returncode == 0


def is_active(name: str) -> bool:
    r = subprocess.run(["systemctl", "is-active", name],
                       capture_output=True, text=True)
    return r.stdout.strip() == "active"


def logs(name: str, lines: int = 50) -> str:
    r = subprocess.run(
        ["journalctl", "-u", name, "-n", str(lines), "--no-pager"],
        capture_output=True, text=True,
    )
    return r.stdout


def remove_unit(name: str) -> None:
    p = SYSTEMD_DIR / name
    if p.exists():
        subprocess.run(["systemctl", "disable", "--now", name],
                       capture_output=True)
        p.unlink()