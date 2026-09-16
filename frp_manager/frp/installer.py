"""Download and install frps/frpc binaries + haproxy."""
from __future__ import annotations

import platform
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

import urllib.request

from ..constants import FRP_VERSION, FRPS_BIN, FRPC_BIN


ARCH_MAP = {
    "x86_64": "amd64",
    "aarch64": "arm64",
    "armv7l": "arm",
}


def detect_arch() -> str:
    machine = platform.machine()
    if machine not in ARCH_MAP:
        raise RuntimeError(f"Unsupported architecture: {machine}")
    return ARCH_MAP[machine]


def apt_install(packages: list[str]) -> None:
    subprocess.run(["apt-get", "update", "-y"], check=False)
    subprocess.run(["apt-get", "install", "-y", *packages], check=True)


def install_dependencies() -> None:
    pkgs = [
        "curl", "wget", "tar", "iperf3", "ufw", "bc",
        "cron", "netcat-openbsd", "nano", "psmisc",
        "python3", "python3-pip", "python3-venv", "haproxy",
    ]
    apt_install(pkgs)


def download_frp() -> Path:
    arch = detect_arch()
    url = (
        f"https://github.com/fatedier/frp/releases/download/"
        f"v{FRP_VERSION}/frp_{FRP_VERSION}_linux_{arch}.tar.gz"
    )
    tmp = Path(tempfile.mkdtemp(prefix="frp_install_"))
    archive = tmp / "frp.tar.gz"
    print(f"⬇  Downloading {url}")
    urllib.request.urlretrieve(url, archive)
    with tarfile.open(archive) as tf:
        tf.extractall(tmp)
    src_dir = tmp / f"frp_{FRP_VERSION}_linux_{arch}"
    shutil.copy2(src_dir / "frps", FRPS_BIN)
    shutil.copy2(src_dir / "frpc", FRPC_BIN)
    FRPS_BIN.chmod(0o755)
    FRPC_BIN.chmod(0o755)
    shutil.rmtree(tmp, ignore_errors=True)
    return FRPS_BIN


def is_installed() -> bool:
    return FRPS_BIN.exists() and FRPC_BIN.exists()