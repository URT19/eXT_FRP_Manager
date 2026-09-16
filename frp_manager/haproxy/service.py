"""HAProxy systemd integration."""
from __future__ import annotations

import subprocess
from pathlib import Path

from ..constants import HAPROXY_CFG, HAPROXY_UNIT, SYSTEMD_DIR


def write_unit() -> Path:
    unit = SYSTEMD_DIR / HAPROXY_UNIT
    unit.write_text(f"""\
[Unit]
Description=HAProxy FRP Aggregation
After=network.target

[Service]
Type=notify
ExecStart=/usr/sbin/haproxy -f {HAPROXY_CFG} -Ws
ExecReload=/bin/kill -USR2 $MAINPID
Restart=always
RestartSec=3s
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
""", encoding="utf-8")
    return unit


def validate() -> tuple[bool, str]:
    r = subprocess.run(
        ["haproxy", "-c", "-f", str(HAPROXY_CFG)],
        capture_output=True, text=True,
    )
    return r.returncode == 0, (r.stdout or "") + (r.stderr or "")


def daemon_reload() -> None:
    subprocess.run(["systemctl", "daemon-reload"], check=False)


def enable() -> None:
    subprocess.run(["systemctl", "enable", HAPROXY_UNIT], check=False)


def disable() -> None:
    """Stop and disable HAProxy unit. Safe even if unit file is missing."""
    from ..constants import SYSTEMD_DIR
    unit_file = SYSTEMD_DIR / HAPROXY_UNIT
    # Only call systemctl if unit file exists OR service is loaded
    if unit_file.exists():
        subprocess.run(
            ["systemctl", "disable", "--now", HAPROXY_UNIT],
            capture_output=True, check=False, timeout=15,
        )
    else:
        # Just in case it's loaded in memory
        subprocess.run(
            ["systemctl", "stop", HAPROXY_UNIT],
            capture_output=True, check=False, timeout=15,
        )
        subprocess.run(
            ["systemctl", "reset-failed", HAPROXY_UNIT],
            capture_output=True, check=False,
        )
    # Kill any orphan haproxy processes
    subprocess.run(
        ["pkill", "-9", "-f", "haproxy.*frp-agg"],
        capture_output=True,
    )


def restart() -> None:
    subprocess.run(["systemctl", "restart", HAPROXY_UNIT], check=False)


def reload_or_restart() -> None:
    r = subprocess.run(["systemctl", "reload-or-restart", HAPROXY_UNIT])
    if r.returncode != 0:
        restart()


def is_active() -> bool:
    r = subprocess.run(["systemctl", "is-active", HAPROXY_UNIT],
                       capture_output=True, text=True)
    return r.stdout.strip() == "active"