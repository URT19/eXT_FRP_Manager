"""Global constants and paths."""
from pathlib import Path

# --- App metadata ---
APP_NAME = "frp-manager"
APP_VERSION = "3.7"
FRP_VERSION = "0.71.0"

# --- Data directory (self-contained) ---
DATA_ROOT = Path("/opt/frp-manager")
DATA_DIR = DATA_ROOT / "data"
CONFIG_DIR = DATA_DIR / "configs"
LOG_DIR = DATA_DIR / "logs"
BACKUP_DIR = DATA_DIR / "backups"
EXPORT_DIR = DATA_DIR / "exports"
HAPROXY_DIR = DATA_DIR / "haproxy"

STATE_FILE = DATA_DIR / "state.json"
DEFAULTS_FILE = DATA_DIR / "defaults.toml"
HAPROXY_CFG = HAPROXY_DIR / "haproxy-agg.cfg"

# --- Binaries ---
FRPS_BIN = Path("/usr/local/bin/frps")
FRPC_BIN = Path("/usr/local/bin/frpc")

# --- Systemd ---
SYSTEMD_DIR = Path("/etc/systemd/system")
HAPROXY_UNIT = "haproxy-frp-agg.service"

# --- Protocols ---
PROTOCOLS = ["tcp", "kcp", "quic", "ws"]
PROTO_DISPLAY = {
    "tcp": "TCP",
    "kcp": "KCP",
    "quic": "QUIC",
    "ws": "WebSocket",
}

# --- Bandwidth profiles ---
BW_PROFILES = {
    "1G": {
        "pool_count": 60,
        "max_pool_count": 100,
        "tcpmux": False,
        "heartbeat_interval": 30,
        "heartbeat_timeout": 90,
    },
    "1.5G": {
        "pool_count": 80,
        "max_pool_count": 150,
        "tcpmux": False,
        "heartbeat_interval": 30,
        "heartbeat_timeout": 90,
    },
    "5G": {
        "pool_count": 150,
        "max_pool_count": 300,
        "tcpmux": False,
        "heartbeat_interval": 20,
        "heartbeat_timeout": 60,
    },
    "10G": {
        "pool_count": 250,
        "max_pool_count": 500,
        "tcpmux": False,
        "heartbeat_interval": 15,
        "heartbeat_timeout": 45,
    },
}

# --- Defaults ---
DEFAULT_PORT_RANGE = (40000, 65000)
DEFAULT_TOKEN_LENGTH = 16
DEFAULT_IPERF_BASE = 55109