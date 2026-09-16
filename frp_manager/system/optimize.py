"""System tuning for high-bandwidth FRP."""
from __future__ import annotations

import subprocess
from pathlib import Path


TCP_CONF = """\
net.core.rmem_max = 67108864
net.core.wmem_max = 67108864
net.core.rmem_default = 16777216
net.core.wmem_default = 16777216
net.core.netdev_max_backlog = 250000
net.core.somaxconn = 65535
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_mtu_probing = 1
"""

UDP_CONF = """\
net.core.rmem_max = 67108864
net.core.wmem_max = 67108864
net.core.rmem_default = 16777216
net.core.wmem_default = 16777216
net.core.netdev_max_backlog = 250000
net.ipv4.udp_rmem_min = 8192
net.ipv4.udp_wmem_min = 8192
net.ipv4.udp_mem = 8388608 12582912 16777216
"""

LIMITS_CONF = """\
* soft nofile 1048576
* hard nofile 1048576
root soft nofile 1048576
root hard nofile 1048576
"""


def _write_and_apply(path: str, content: str) -> None:
    p = Path(path)
    p.write_text(content)
    if p.suffix == ".conf" and "/sysctl.d/" in path:
        subprocess.run(["sysctl", "-p", path], capture_output=True)


def optimize_tcp() -> None:
    _write_and_apply("/etc/sysctl.d/99-frp-tcp.conf", TCP_CONF)


def optimize_udp() -> None:
    _write_and_apply("/etc/sysctl.d/99-frp-udp.conf", UDP_CONF)


def optimize_limits() -> None:
    Path("/etc/security/limits.d/99-frp.conf").write_text(LIMITS_CONF)


def optimize_all() -> None:
    optimize_tcp()
    optimize_udp()
    optimize_limits()