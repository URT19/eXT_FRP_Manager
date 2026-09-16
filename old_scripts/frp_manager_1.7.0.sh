#!/bin/bash

# ==========================================
# Advanced FRP Multi-Protocol Tunnel Manager v1.7.0
# Supports: TCP | KCP | QUIC | WebSocket
# Prefixes: tcp_ / kcp_ / quic_ / ws_  (no conflict)
# FRP Version: 0.71.0
# New in 1.6: tcpMux toggle, better high-BW defaults,
#             Multi-Tunnel HAProxy Bandwidth Aggregation
# ==========================================

VERSION="1.7.0-multi-agg"
FRP_VERSION="0.71.0"
CONFIG_DIR="/etc/frp"
LOG_DIR="/var/log/frp"
DEFAULTS_FILE="/etc/frp/multi_defaults.conf"
HAPROXY_CFG="/etc/haproxy/haproxy-frp-agg.cfg"

# Colors
RED='\033[0;31m'
LIGHT_RED='\033[1;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
ORANGE_LIGHT='\033[38;5;214m'
ORANGE='\033[38;5;208m'
NC='\033[0m'

# Check Root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Error: Script ro ba root ejra kon. (run as root)${NC}"
  exit 1
fi

mkdir -p "$CONFIG_DIR" "$LOG_DIR"

# Load or create defaults
load_defaults() {
    if [ -f "$DEFAULTS_FILE" ]; then
        source "$DEFAULTS_FILE"
    else
        # Default profile: 1.5 Gbps
        DEFAULT_BW_PROFILE="1.5G"
        DEFAULT_MAX_POOL_COUNT=150
        DEFAULT_POOL_COUNT=80
        DEFAULT_TOKEN_LENGTH=16
        DEFAULT_PORT_RANGE_START=40000
        DEFAULT_PORT_RANGE_END=65000
        DEFAULT_TCPMUX="false"
        DEFAULT_HEARTBEAT_INTERVAL=30
        DEFAULT_HEARTBEAT_TIMEOUT=90
        UI_LANG="finglish"
        save_defaults
    fi
    DEFAULT_BW_PROFILE=${DEFAULT_BW_PROFILE:-1.5G}
    UI_LANG=${UI_LANG:-finglish}
}

save_defaults() {
    cat << EOF > "$DEFAULTS_FILE"
DEFAULT_BW_PROFILE=${DEFAULT_BW_PROFILE:-1.5G}
DEFAULT_MAX_POOL_COUNT=${DEFAULT_MAX_POOL_COUNT:-150}
DEFAULT_POOL_COUNT=${DEFAULT_POOL_COUNT:-80}
DEFAULT_TOKEN_LENGTH=${DEFAULT_TOKEN_LENGTH:-16}
DEFAULT_PORT_RANGE_START=${DEFAULT_PORT_RANGE_START:-40000}
DEFAULT_PORT_RANGE_END=${DEFAULT_PORT_RANGE_END:-65000}
DEFAULT_TCPMUX=${DEFAULT_TCPMUX:-false}
DEFAULT_HEARTBEAT_INTERVAL=${DEFAULT_HEARTBEAT_INTERVAL:-30}
DEFAULT_HEARTBEAT_TIMEOUT=${DEFAULT_HEARTBEAT_TIMEOUT:-90}
UI_LANG=${UI_LANG:-finglish}
EOF
}


# ========== UI Language: finglish (default) | english ==========
M() {
    local key="$1"
    case "${UI_LANG:-finglish}" in
    english)
        case "$key" in
            logo_sub) echo "Multi-Protocol Tunnel Manager v${VERSION}" ;;
            logo_proto) echo "TCP | KCP | QUIC | WebSocket + HAProxy Aggregation" ;;
            loc_status) echo "Server Location Status" ;;
            menu_1) echo "Install Dependencies & FRP" ;;
            menu_2) echo "Setup Server (Iran)" ;;
            menu_3) echo "Setup Client (Kharej)" ;;
            menu_4) echo "Check Tunnel Health" ;;
            menu_5) echo "Manage / Restart / Logs / Delete Tunnels" ;;
            menu_6) echo "Run iperf3 Speedtest" ;;
            menu_7) echo "Change Location Mode (Toggle Iran/Kharej)" ;;
            menu_8) echo "Set Default Values / Bandwidth Profile" ;;
            menu_9) echo "Optimize System (TCP/BBR or UDP)" ;;
            menu_10) echo "Multi-Tunnel HAProxy Aggregation (High Bandwidth)" ;;
            menu_11) echo "Manage HAProxy Aggregation (edit / restart / logs)" ;;
            menu_12) echo "Server Bandwidth Test (FR / NL / IR)" ;;
            menu_13) echo "Reset / Cleanup (all tunnels / HAProxy / full reset)" ;;
            menu_14) echo "Language (Finglish / English)" ;;
            menu_0) echo "Exit" ;;
            choose) echo "Choose an option" ;;
            press_enter) echo "Press Enter to return..." ;;
            invalid) echo "Invalid choice!" ;;
            exiting) echo "Exiting..." ;;
            lang_title) echo "UI Language" ;;
            lang_cur) echo "Current language" ;;
            lang_set_f) echo "Language set to Finglish" ;;
            lang_set_e) echo "Language set to English" ;;
            no_tunnels) echo "No tunnels configured yet." ;;
            tunnels_header) echo "Active Configured Tunnels (All Protocols)" ;;
            conf_yn) echo "[Y/n]" ;;
            *) echo "$key" ;;
        esac
        ;;
    *)
        case "$key" in
            logo_sub) echo "Modiriyat Tunnel Multi-Protocol v${VERSION}" ;;
            logo_proto) echo "TCP | KCP | QUIC | WebSocket + HAProxy Aggregation" ;;
            loc_status) echo "Vaziyat Location Server" ;;
            menu_1) echo "Nasb Dependencies va FRP" ;;
            menu_2) echo "Setup Server (Iran)" ;;
            menu_3) echo "Setup Client (Kharej)" ;;
            menu_4) echo "Check Salamat Tunnel" ;;
            menu_5) echo "Manage / Restart / Log / Delete Tunnel-ha" ;;
            menu_6) echo "Ejraye iperf3 Speedtest" ;;
            menu_7) echo "Avaz kardan Mode Location (Iran/Kharej)" ;;
            menu_8) echo "Set Default Values / Profile Bandwidth" ;;
            menu_9) echo "Optimize System (TCP/BBR ya UDP)" ;;
            menu_10) echo "Aggregation Multi-Tunnel ba HAProxy (Bandwidth bala)" ;;
            menu_11) echo "Manage HAProxy Aggregation (edit / restart / log)" ;;
            menu_12) echo "Test Bandwidth Server (FR / NL / IR)" ;;
            menu_13) echo "Reset / Pak kardan (tunnel-ha / HAProxy / full reset)" ;;
            menu_14) echo "Zaban (Finglish / English)" ;;
            menu_0) echo "Khoroj" ;;
            choose) echo "Yek gozine entekhab kon" ;;
            press_enter) echo "Enter bezan baraye bargasht..." ;;
            invalid) echo "Gozine eshtebah!" ;;
            exiting) echo "Dar hale khoroj..." ;;
            lang_title) echo "Zaban UI" ;;
            lang_cur) echo "Zaban feli" ;;
            lang_set_f) echo "Zaban shod Finglish" ;;
            lang_set_e) echo "Zaban shod English" ;;
            no_tunnels) echo "Hanooz tunnel-i set nashode." ;;
            tunnels_header) echo "Tunnel-haye Active (Hame Protocol-ha)" ;;
            conf_yn) echo "[Y/n]" ;;
            *) echo "$key" ;;
        esac
        ;;
    esac
}

set_language() {
    show_logo
    load_defaults
    echo -e "${CYAN}--- $(M lang_title) ---${NC}\n"
    echo -e "$(M lang_cur): ${YELLOW}${UI_LANG}${NC}\n"
    echo -e "  1) Finglish  ${GREEN}(pishfarz / default)${NC}"
    echo -e "  2) English"
    echo -e "  0) Back"
    read -p "$(M choose): " LCHOICE
    case $LCHOICE in
        1) UI_LANG="finglish"; save_defaults; echo -e "${GREEN}$(M lang_set_f)${NC}" ;;
        2) UI_LANG="english"; save_defaults; echo -e "${GREEN}$(M lang_set_e)${NC}" ;;
        *) return ;;
    esac
    sleep 1
}

# Print Logo
show_logo() {
    clear
    echo -e "${CYAN}"
    echo '  ______ _____  _____    _______ _   _ _   _ _   _ ______ _      '
    echo ' |  ____|  __ \|  __ \  |__   __| | | | \ | | \ | |  ____| |     '
    echo ' | |__  | |__) | |__) |    | |  | | | |  \| |  \| | |__  | |     '
    echo ' |  __| |  _  /|  ___/     | |  | | | | . ` | . ` |  __| | |     '
    echo ' | |    | | \ \| |         | |  | |_| | |\  | |\  | |____| |____ '
    echo ' |_|    |_|  \_\_|         |_|   \___/|_| \_|_| \_|______|______|'
    echo -e "${YELLOW}     -- $(M logo_sub) --${NC}"
    echo -e "${CYAN}          $(M logo_proto)${NC}\n"
}

# Location Auto Detection
detect_location() {
    if [ -z "$SERVER_MODE" ]; then
        COUNTRY_CODE=$(curl -s --max-time 3 http://ip-api.com/line/?fields=countryCode 2>/dev/null)
        if [ -z "$COUNTRY_CODE" ]; then
            COUNTRY_CODE=$(curl -s --max-time 3 https://myip.wtf/json 2>/dev/null | grep -o '"countryCode": "[^"]*' | grep -o '[^"]*$')
        fi
        if [ -z "$COUNTRY_CODE" ]; then
            COUNTRY_CODE=$(curl -s --max-time 3 https://ifconfig.co/country-iso 2>/dev/null)
        fi

        if [ "$COUNTRY_CODE" == "IR" ]; then
            SERVER_MODE="IRAN"
        else
            SERVER_MODE="KHAREJ"
        fi
    fi
}

get_editor() {
    if command -v nano >/dev/null 2>&1; then echo "nano";
    elif command -v vim >/dev/null 2>&1; then echo "vim";
    else echo "vi"; fi
}

allow_ufw_port() {
    local port=$1
    local proto=${2:-tcp}
    if command -v ufw >/dev/null 2>&1; then
        if ufw status | grep -q "Status: active"; then
            ufw allow "$port"/"$proto" >/dev/null 2>&1
            echo -e "${GREEN}[UFW] Port $port/$proto added to whitelist.${NC}"
        fi
    fi
}

generate_token() {
    local len=${1:-16}
    tr -dc A-Za-z0-9 </dev/urandom | head -c "$len"
}

generate_random_port() {
    shuf -i ${DEFAULT_PORT_RANGE_START:-40000}-${DEFAULT_PORT_RANGE_END:-65000} -n 1
}

confirm_yn() {
    local prompt="$1"
    local reply
    read -p "${prompt} $(M conf_yn): " reply
    reply=${reply:-Y}
    case "$reply" in
        [Yy]|[Yy][Ee][Ss]) return 0 ;;
        *) return 1 ;;
    esac
}

select_protocol() {
    echo -e "\n${CYAN}Select Protocol:${NC}"
    echo -e "  1) TCP          (Best pure performance / recommended for aggregation)"
    echo -e "  2) KCP          (Good for lossy networks)"
    echo -e "  3) QUIC         (Modern + good bandwidth)"
    echo -e "  4) WebSocket    (Bypass firewall/proxy)"
    read -p "Choose [1-4]: " PROTO_CHOICE

    case $PROTO_CHOICE in
        1) PROTOCOL="tcp"; PROTO_NAME="TCP"; PROTO_COLOR="$CYAN" ;;
        2) PROTOCOL="kcp"; PROTO_NAME="KCP"; PROTO_COLOR="$PURPLE" ;;
        3) PROTOCOL="quic"; PROTO_NAME="QUIC"; PROTO_COLOR="$BLUE" ;;
        4) PROTOCOL="ws"; PROTO_NAME="WebSocket"; PROTO_COLOR="$GREEN" ;;
        *) echo -e "${RED}Invalid choice, defaulting to TCP${NC}"; PROTOCOL="tcp"; PROTO_NAME="TCP"; PROTO_COLOR="$CYAN" ;;
    esac
    echo -e "${GREEN}Selected Protocol: ${PROTO_COLOR}${PROTO_NAME}${NC}"
}

install_dependencies_and_frp() {
    show_logo
    echo -e "${YELLOW}[1/3] Installing Dependencies...${NC}"
    apt-get update -y
    apt-get install -y curl wget tar iperf3 ufw bc cron netcat-openbsd nano psmisc python3 haproxy

    echo -e "${YELLOW}[2/3] Downloading FRP v${FRP_VERSION}...${NC}"
    ARCH=$(uname -m)
    case $ARCH in
        x86_64) ARCH_TYPE="amd64" ;;
        aarch64) ARCH_TYPE="arm64" ;;
        *) echo -e "${RED}Unsupported architecture: $ARCH${NC}"; return ;;
    esac

    TMP_DIR="/tmp/frp_install_multi"
    mkdir -p "$TMP_DIR"
    wget -q --show-progress "https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_linux_${ARCH_TYPE}.tar.gz" -O "$TMP_DIR/frp.tar.gz"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to download FRP.${NC}"
        rm -rf "$TMP_DIR"
        read -p "Press Enter to return..."
        return
    fi

    tar -zxvf "$TMP_DIR/frp.tar.gz" -C "$TMP_DIR"
    cp "$TMP_DIR/frp_${FRP_VERSION}_linux_${ARCH_TYPE}/frps" /usr/local/bin/
    cp "$TMP_DIR/frp_${FRP_VERSION}_linux_${ARCH_TYPE}/frpc" /usr/local/bin/
    chmod +x /usr/local/bin/frps /usr/local/bin/frpc
    rm -rf "$TMP_DIR"

    echo -e "${GREEN}[3/3] FRP v${FRP_VERSION} + HAProxy installed successfully!${NC}"
    echo -e "${CYAN}Note: Binary is shared. Each protocol uses its own prefix (tcp_/kcp_/quic_/ws_).${NC}"
    read -p "Press Enter to return..."
}

set_default_values() {
    show_logo
    load_defaults
    echo -e "${CYAN}--- Set Default Values / Bandwidth Profile ---${NC}\n"
    echo -e "Current profile : ${YELLOW}${DEFAULT_BW_PROFILE}${NC}"
    echo -e "  Max Pool Count (Server) : ${YELLOW}${DEFAULT_MAX_POOL_COUNT}${NC}"
    echo -e "  Pool Count (Client)     : ${YELLOW}${DEFAULT_POOL_COUNT}${NC}"
    echo -e "  TCP Mux                 : ${YELLOW}${DEFAULT_TCPMUX}${NC}"
    echo -e "  Token Length            : ${YELLOW}${DEFAULT_TOKEN_LENGTH}${NC}"
    echo -e "  Port Range              : ${YELLOW}${DEFAULT_PORT_RANGE_START}-${DEFAULT_PORT_RANGE_END}${NC}"
    echo -e "  Heartbeat Interval/Timeout: ${YELLOW}${DEFAULT_HEARTBEAT_INTERVAL}/${DEFAULT_HEARTBEAT_TIMEOUT}${NC}\n"

    echo -e "${ORANGE}Quick Bandwidth Profiles (recommended):${NC}"
    echo -e "  1) 1 Gbps    → pool 60/100, tcpMux=false"
    echo -e "  2) 1.5 Gbps  → pool 80/150, tcpMux=false  ${GREEN}(default)${NC}"
    echo -e "  3) 5 Gbps    → pool 150/300, tcpMux=false, larger heartbeats"
    echo -e "  4) 10 Gbps   → pool 250/500, tcpMux=false, aggressive buffers"
    echo -e "  5) Custom / manual edit all values"
    echo -e "  0) Back without change"
    read -p "Select profile [0-5]: " PROF
    case $PROF in
        1)
            DEFAULT_BW_PROFILE="1G"
            DEFAULT_POOL_COUNT=60
            DEFAULT_MAX_POOL_COUNT=100
            DEFAULT_TCPMUX="false"
            DEFAULT_HEARTBEAT_INTERVAL=30
            DEFAULT_HEARTBEAT_TIMEOUT=90
            ;;
        2)
            DEFAULT_BW_PROFILE="1.5G"
            DEFAULT_POOL_COUNT=80
            DEFAULT_MAX_POOL_COUNT=150
            DEFAULT_TCPMUX="false"
            DEFAULT_HEARTBEAT_INTERVAL=30
            DEFAULT_HEARTBEAT_TIMEOUT=90
            ;;
        3)
            DEFAULT_BW_PROFILE="5G"
            DEFAULT_POOL_COUNT=150
            DEFAULT_MAX_POOL_COUNT=300
            DEFAULT_TCPMUX="false"
            DEFAULT_HEARTBEAT_INTERVAL=20
            DEFAULT_HEARTBEAT_TIMEOUT=60
            ;;
        4)
            DEFAULT_BW_PROFILE="10G"
            DEFAULT_POOL_COUNT=250
            DEFAULT_MAX_POOL_COUNT=500
            DEFAULT_TCPMUX="false"
            DEFAULT_HEARTBEAT_INTERVAL=15
            DEFAULT_HEARTBEAT_TIMEOUT=45
            ;;
        5)
            read -p "Profile name [custom]: " input
            DEFAULT_BW_PROFILE=${input:-custom}
            read -p "Max Pool Count Server [current: $DEFAULT_MAX_POOL_COUNT]: " input
            DEFAULT_MAX_POOL_COUNT=${input:-$DEFAULT_MAX_POOL_COUNT}
            read -p "Pool Count Client [current: $DEFAULT_POOL_COUNT]: " input
            DEFAULT_POOL_COUNT=${input:-$DEFAULT_POOL_COUNT}
            read -p "Token Length [current: $DEFAULT_TOKEN_LENGTH]: " input
            DEFAULT_TOKEN_LENGTH=${input:-$DEFAULT_TOKEN_LENGTH}
            read -p "Port Range Start [current: $DEFAULT_PORT_RANGE_START]: " input
            DEFAULT_PORT_RANGE_START=${input:-$DEFAULT_PORT_RANGE_START}
            read -p "Port Range End [current: $DEFAULT_PORT_RANGE_END]: " input
            DEFAULT_PORT_RANGE_END=${input:-$DEFAULT_PORT_RANGE_END}
            read -p "TCP Mux true/false [current: $DEFAULT_TCPMUX]: " input
            DEFAULT_TCPMUX=${input:-$DEFAULT_TCPMUX}
            read -p "Heartbeat Interval [current: $DEFAULT_HEARTBEAT_INTERVAL]: " input
            DEFAULT_HEARTBEAT_INTERVAL=${input:-$DEFAULT_HEARTBEAT_INTERVAL}
            read -p "Heartbeat Timeout [current: $DEFAULT_HEARTBEAT_TIMEOUT]: " input
            DEFAULT_HEARTBEAT_TIMEOUT=${input:-$DEFAULT_HEARTBEAT_TIMEOUT}
            ;;
        0|*) echo -e "${YELLOW}No change.${NC}"; read -p "Press Enter..."; return ;;
    esac

    save_defaults
    echo -e "\n${GREEN}Profile [${DEFAULT_BW_PROFILE}] saved successfully!${NC}"
    echo -e "  poolCount=${DEFAULT_POOL_COUNT}  maxPoolCount=${DEFAULT_MAX_POOL_COUNT}  tcpMux=${DEFAULT_TCPMUX}"
    read -p "Press Enter to return..."
}

ask_advanced_options() {
    echo -e "\n${ORANGE}--- Advanced Options (High Bandwidth Tuning) ---${NC}"
    echo -e "${YELLOW}Recommendation for high bandwidth (1Gbps+):${NC}"
    echo -e "  - TCP Mux = false  (better single-stream throughput)"
    echo -e "  - Higher poolCount / maxPoolCount"
    echo ""

    echo -e "1) Use recommended High-BW defaults (tcpMux=false, higher pools)"
    echo -e "2) Use script defaults"
    echo -e "3) Manual / Custom"
    read -p "Select [1-3]: " ADV_MODE
    ADV_MODE=${ADV_MODE:-1}

    if [ "$ADV_MODE" == "1" ]; then
        USE_TCPMUX="false"
        if [ "$1" == "server" ]; then
            MAX_POOL=200
        else
            POOL_COUNT=80
        fi
        HEARTBEAT_INTERVAL=30
        HEARTBEAT_TIMEOUT=90
        echo -e "${GREEN}High-BW mode → tcpMux=false | pool elevated${NC}"
    elif [ "$ADV_MODE" == "2" ]; then
        USE_TCPMUX="$DEFAULT_TCPMUX"
        if [ "$1" == "server" ]; then
            MAX_POOL=$DEFAULT_MAX_POOL_COUNT
        else
            POOL_COUNT=$DEFAULT_POOL_COUNT
        fi
        HEARTBEAT_INTERVAL=$DEFAULT_HEARTBEAT_INTERVAL
        HEARTBEAT_TIMEOUT=$DEFAULT_HEARTBEAT_TIMEOUT
    else
        read -p "Enable transport.tcpMux? (true/false) [default: $DEFAULT_TCPMUX]: " input
        USE_TCPMUX=${input:-$DEFAULT_TCPMUX}

        if [ "$1" == "server" ]; then
            read -p "Enter transport.maxPoolCount [Default: $DEFAULT_MAX_POOL_COUNT]: " MAX_POOL
            MAX_POOL=${MAX_POOL:-$DEFAULT_MAX_POOL_COUNT}
        else
            read -p "Enter transport.poolCount [Default: $DEFAULT_POOL_COUNT]: " POOL_COUNT
            POOL_COUNT=${POOL_COUNT:-$DEFAULT_POOL_COUNT}
        fi

        read -p "Heartbeat Interval (sec) [Default: $DEFAULT_HEARTBEAT_INTERVAL]: " input
        HEARTBEAT_INTERVAL=${input:-$DEFAULT_HEARTBEAT_INTERVAL}
        read -p "Heartbeat Timeout (sec) [Default: $DEFAULT_HEARTBEAT_TIMEOUT]: " input
        HEARTBEAT_TIMEOUT=${input:-$DEFAULT_HEARTBEAT_TIMEOUT}
    fi
}

setup_frps() {
    show_logo
    load_defaults
    select_protocol

    echo -e "\n${ORANGE}--- Setup FRP ${PROTO_NAME} Server (Iran / Inbound) ---${NC}\n"
    echo -e "${CYAN}Important: It is better to use the same tunnel number on both Iran and Kharej servers${NC}"
    echo -e "${CYAN}(Example: If you choose tunnel 10 on Iran, choose tunnel 10 on Kharej as well)${NC}\n"

    echo -e "${PURPLE}Current existing tunnels:${NC}"
    list_tunnels
    
    read -p "Enter Tunnel Index Number (1 to 10): " ID
    if ! [[ "$ID" =~ ^[1-9]$|^10$ ]]; then
        echo -e "${RED}Invalid ID! Use 1 to 10.${NC}"
        sleep 2; return
    fi

    if show_existing_tunnel_info "server" "$PROTOCOL" "$ID"; then
        echo -e "${LIGHT_RED}A service with this Protocol + ID already exists.${NC}"
        echo -e "${YELLOW}Creating a new one will OVERWRITE the previous config and service.${NC}"
        if ! confirm_yn "Overwrite existing service?"; then
            echo -e "${YELLOW}Cancelled. No changes made.${NC}"
            sleep 1
            return
        fi
        systemctl stop "frps_${PROTOCOL}_tunnel${ID}.service" 2>/dev/null
    fi

    read -p "Enter Tunnel Name (e.g. nl1, de2): " TUNNEL_NAME
    TUNNEL_NAME=${TUNNEL_NAME:-"tunnel${ID}"}

    echo -e "\n${ORANGE}Choose configuration mode:${NC}"
    echo -e "  1) Use Defaults (recommended)"
    echo -e "  2) Manual / Custom values"
    read -p "Select [1-2]: " MODE
    MODE=${MODE:-1}

    if [ "$MODE" == "1" ]; then
        BIND_PORT=$(generate_random_port)
        AUTH_TOKEN=$(generate_token "$DEFAULT_TOKEN_LENGTH")
        ask_advanced_options "server"
        echo -e "${GREEN}Using → Port: $BIND_PORT | Token: $AUTH_TOKEN | maxPoolCount: $MAX_POOL | tcpMux: $USE_TCPMUX${NC}"
    else
        RANDOM_BIND=$(generate_random_port)
        read -p "Enter Bind Port [Suggested: $RANDOM_BIND]: " BIND_PORT
        BIND_PORT=${BIND_PORT:-$RANDOM_BIND}
        
        DEFAULT_TOKEN=$(generate_token "$DEFAULT_TOKEN_LENGTH")
        read -p "Enter Authentication Token [Auto: $DEFAULT_TOKEN]: " AUTH_TOKEN
        AUTH_TOKEN=${AUTH_TOKEN:-$DEFAULT_TOKEN}

        ask_advanced_options "server"
    fi

    CONF_FILE="$CONFIG_DIR/frps_${PROTOCOL}_tunnel${ID}.toml"

    case $PROTOCOL in
        tcp|ws)
            cat << EOF > "$CONF_FILE"
# Tunnel_Name = "$TUNNEL_NAME"
# Protocol   = $PROTO_NAME
bindAddr = "0.0.0.0"
bindPort = $BIND_PORT
auth.method = "token"
auth.token = "$AUTH_TOKEN"
transport.tcpMux = $USE_TCPMUX
transport.maxPoolCount = $MAX_POOL
transport.heartbeatTimeout = $HEARTBEAT_TIMEOUT
EOF
            allow_ufw_port "$BIND_PORT" "tcp"
            ;;
        kcp)
            cat << EOF > "$CONF_FILE"
# Tunnel_Name = "$TUNNEL_NAME"
# Protocol   = $PROTO_NAME
bindAddr = "0.0.0.0"
bindPort = $BIND_PORT
kcpBindPort = $BIND_PORT
auth.method = "token"
auth.token = "$AUTH_TOKEN"
transport.tcpMux = $USE_TCPMUX
transport.maxPoolCount = $MAX_POOL
transport.heartbeatTimeout = $HEARTBEAT_TIMEOUT
EOF
            allow_ufw_port "$BIND_PORT" "udp"
            allow_ufw_port "$BIND_PORT" "tcp"
            ;;
        quic)
            cat << EOF > "$CONF_FILE"
# Tunnel_Name = "$TUNNEL_NAME"
# Protocol   = $PROTO_NAME
bindAddr = "0.0.0.0"
bindPort = $BIND_PORT
quicBindPort = $BIND_PORT
auth.method = "token"
auth.token = "$AUTH_TOKEN"
transport.tcpMux = $USE_TCPMUX
transport.maxPoolCount = $MAX_POOL
transport.heartbeatTimeout = $HEARTBEAT_TIMEOUT
EOF
            allow_ufw_port "$BIND_PORT" "udp"
            allow_ufw_port "$BIND_PORT" "tcp"
            ;;
    esac

    SERVICE_FILE="/etc/systemd/system/frps_${PROTOCOL}_tunnel${ID}.service"
    cat << EOF > "$SERVICE_FILE"
[Unit]
Description=FRP ${PROTO_NAME} Server Tunnel ${ID} (${TUNNEL_NAME})
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/frps -c $CONF_FILE
Restart=always
RestartSec=5s
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "frps_${PROTOCOL}_tunnel${ID}.service"

    echo ""
    if confirm_yn "Start/restart the service now?"; then
        systemctl restart "frps_${PROTOCOL}_tunnel${ID}.service"
        echo -e "${GREEN}Service started/restarted.${NC}"
    else
        echo -e "${YELLOW}Service enabled but not started. You can start it later from Manage menu.${NC}"
    fi

    MY_IP=$(curl -s --max-time 3 http://ip-api.com/line/?fields=query 2>/dev/null)

    echo -e "\n${ORANGE}================ ${PROTO_NAME} SERVER (IRAN) CREATED SUCCESSFULLY ================${NC}"
    echo -e "Tunnel ID     : ${ORANGE}${ID}${NC}"
    echo -e "Tunnel Name   : ${ORANGE}${TUNNEL_NAME}${NC}"
    echo -e "Protocol      : ${PROTO_COLOR}${PROTO_NAME}${NC}"
    echo -e "Server IP     : ${CYAN}${MY_IP}${NC}"
    echo -e "Bind Port     : ${CYAN}${BIND_PORT}${NC}"
    echo -e "Auth Token    : ${CYAN}${AUTH_TOKEN}${NC}"
    echo -e "maxPoolCount  : ${CYAN}${MAX_POOL}${NC}"
    echo -e "tcpMux        : ${CYAN}${USE_TCPMUX}${NC}"
    echo -e "${ORANGE}==============================================================================${NC}\n"

    read -p "Press Enter to return..."
}

setup_frpc() {
    show_logo
    load_defaults
    select_protocol

    echo -e "\n${YELLOW}--- Setup FRP ${PROTO_NAME} Client (Kharej / Outbound) ---${NC}\n"
    echo -e "${CYAN}Important: It is better to use the same tunnel number on both Iran and Kharej servers${NC}"
    echo -e "${CYAN}(Example: If you choose tunnel 10 on Iran, choose tunnel 10 on Kharej as well)${NC}\n"

    echo -e "${PURPLE}Current existing tunnels:${NC}"
    list_tunnels
    
    read -p "Enter Tunnel Index Number (1 to 10): " ID
    if ! [[ "$ID" =~ ^[1-9]$|^10$ ]]; then
        echo -e "${RED}Invalid ID! Use 1 to 10.${NC}"
        sleep 2; return
    fi

    if show_existing_tunnel_info "client" "$PROTOCOL" "$ID"; then
        echo -e "${LIGHT_RED}A service with this Protocol + ID already exists.${NC}"
        echo -e "${YELLOW}Creating a new one will OVERWRITE the previous config and service.${NC}"
        if ! confirm_yn "Overwrite existing service?"; then
            echo -e "${YELLOW}Cancelled. No changes made.${NC}"
            sleep 1
            return
        fi
        systemctl stop "frpc_${PROTOCOL}_tunnel${ID}.service" 2>/dev/null
    fi

    read -p "Enter Tunnel Name (e.g. nl1, de2): " TUNNEL_NAME
    TUNNEL_NAME=${TUNNEL_NAME:-"tunnel${ID}"}

    read -p "Enter Iran Server IP or Domain: " IRAN_IP
    read -p "Enter FRP Server Bind Port: " BIND_PORT
    read -p "Enter Authentication Token: " AUTH_TOKEN

    ask_advanced_options "client"

    case $PROTOCOL in
        tcp)  IPERF_PORT=$((55109 + ID)) ;;
        kcp)  IPERF_PORT=$((55209 + ID)) ;;
        quic) IPERF_PORT=$((55409 + ID)) ;;
        ws)   IPERF_PORT=$((55309 + ID)) ;;
    esac

    echo -e "${YELLOW}Enter local ports to forward separated by comma (e.g. 443,80,8443):${NC}"
    read -p "Ports: " PORTS_INPUT

    CONF_FILE="$CONFIG_DIR/frpc_${PROTOCOL}_tunnel${ID}.toml"

    cat << EOF > "$CONF_FILE"
# Tunnel_Name = "$TUNNEL_NAME"
# Protocol   = $PROTO_NAME
serverAddr = "$IRAN_IP"
serverPort = $BIND_PORT
auth.method = "token"
auth.token = "$AUTH_TOKEN"
transport.tcpMux = $USE_TCPMUX
transport.poolCount = $POOL_COUNT
transport.heartbeatInterval = $HEARTBEAT_INTERVAL
transport.heartbeatTimeout = $HEARTBEAT_TIMEOUT
EOF

    case $PROTOCOL in
        tcp)
            ;;
        kcp)
            echo 'transport.protocol = "kcp"' >> "$CONF_FILE"
            ;;
        quic)
            echo 'transport.protocol = "quic"' >> "$CONF_FILE"
            ;;
        ws)
            echo 'transport.protocol = "websocket"' >> "$CONF_FILE"
            ;;
    esac

    cat << EOF >> "$CONF_FILE"

# iperf3 SpeedTest Port Auto-Added
[[proxies]]
name = "${TUNNEL_NAME}_iperf3_${IPERF_PORT}"
type = "tcp"
localIP = "127.0.0.1"
localPort = $IPERF_PORT
remotePort = $IPERF_PORT

EOF

    IFS=',' read -ra ADDR <<< "$PORTS_INPUT"
    for PORT in "${ADDR[@]}"; do
        PORT=$(echo "$PORT" | xargs)
        if [ -n "$PORT" ]; then
            cat << EOF >> "$CONF_FILE"
[[proxies]]
name = "${TUNNEL_NAME}_tcp_${PORT}"
type = "tcp"
localIP = "127.0.0.1"
localPort = $PORT
remotePort = $PORT

EOF
            allow_ufw_port "$PORT"
        fi
    done

    allow_ufw_port "$IPERF_PORT"

    SERVICE_FILE="/etc/systemd/system/frpc_${PROTOCOL}_tunnel${ID}.service"
    cat << EOF > "$SERVICE_FILE"
[Unit]
Description=FRP ${PROTO_NAME} Client Tunnel ${ID} (${TUNNEL_NAME})
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/frpc -c $CONF_FILE
Restart=always
RestartSec=5s
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "frpc_${PROTOCOL}_tunnel${ID}.service"

    echo ""
    if confirm_yn "Start/restart the service now?"; then
        systemctl restart "frpc_${PROTOCOL}_tunnel${ID}.service"
        echo -e "${GREEN}Service started/restarted.${NC}"
    else
        echo -e "${YELLOW}Service enabled but not started. You can start it later from Manage menu.${NC}"
    fi

    echo -e "\n${YELLOW}FRP ${PROTO_NAME} Client Tunnel ${ID} (${TUNNEL_NAME}) created successfully!${NC}"
    echo -e "poolCount used: ${CYAN}${POOL_COUNT}${NC} | tcpMux: ${CYAN}${USE_TCPMUX}${NC}"
    read -p "Press Enter to return..."
}

list_tunnels() {
    echo -e "${PURPLE}--- $(M tunnels_header) ---${NC}"
    local found=0
    for proto in tcp kcp quic ws; do
        for i in {1..10}; do
            S_CONF="$CONFIG_DIR/frps_${proto}_tunnel${i}.toml"
            C_CONF="$CONFIG_DIR/frpc_${proto}_tunnel${i}.toml"
            
            if [ -f "$S_CONF" ]; then
                found=1
                NAME=$(grep "Tunnel_Name" "$S_CONF" | cut -d'"' -f2)
                BIND=$(grep -E "bindPort|kcpBindPort|quicBindPort" "$S_CONF" | head -1 | awk '{print $3}')
                STATUS=$(systemctl is-active "frps_${proto}_tunnel${i}.service" 2>/dev/null)
                if [ "$STATUS" == "active" ]; then ST_TXT="${GREEN}ONLINE${NC}"; else ST_TXT="${RED}OFFLINE${NC}"; fi
                echo -e "Tunnel $i [${ORANGE}${proto^^} Server / IRAN${NC} | Name: ${CYAN}${NAME:-N/A}${NC}] Status: [$ST_TXT] | Port: ${YELLOW}${BIND:-N/A}${NC}"
            elif [ -f "$C_CONF" ]; then
                found=1
                NAME=$(grep "Tunnel_Name" "$C_CONF" | cut -d'"' -f2)
                PORTS=$(grep "remotePort" "$C_CONF" | awk '{print $3}' | tr '\n' ',' | sed 's/,$//')
                STATUS=$(systemctl is-active "frpc_${proto}_tunnel${i}.service" 2>/dev/null)
                if [ "$STATUS" == "active" ]; then ST_TXT="${GREEN}ONLINE${NC}"; else ST_TXT="${RED}OFFLINE${NC}"; fi
                echo -e "Tunnel $i [${YELLOW}${proto^^} Client / KHAREJ${NC} | Name: ${CYAN}${NAME:-N/A}${NC}] Status: [$ST_TXT] | Ports: ${YELLOW}[${PORTS:-N/A}]${NC}"
            fi
        done
    done
    if [ "$found" -eq 0 ]; then
        echo -e "${YELLOW}$(M no_tunnels)${NC}"
    fi
    echo "---------------------------------"
    if [ -f "$HAPROXY_CFG" ]; then
        show_haproxy_port_map
    fi
}

show_existing_tunnel_info() {
    local role=$1
    local proto=$2
    local id=$3
    local conf=""
    local svc=""

    if [ "$role" == "server" ]; then
        conf="$CONFIG_DIR/frps_${proto}_tunnel${id}.toml"
        svc="frps_${proto}_tunnel${id}.service"
    else
        conf="$CONFIG_DIR/frpc_${proto}_tunnel${id}.toml"
        svc="frpc_${proto}_tunnel${id}.service"
    fi

    if [ ! -f "$conf" ]; then
        return 1
    fi

    local name=$(grep "Tunnel_Name" "$conf" 2>/dev/null | cut -d'"' -f2)
    local status=$(systemctl is-active "$svc" 2>/dev/null)
    local st_txt
    if [ "$status" == "active" ]; then st_txt="${GREEN}ONLINE${NC}"; else st_txt="${RED}OFFLINE${NC}"; fi

    echo -e "\n${YELLOW}⚠ Existing ${role^^} tunnel found for Protocol [${proto^^}] / ID [${id}]:${NC}"
    echo -e "  Name     : ${CYAN}${name:-N/A}${NC}"
    echo -e "  Service  : ${CYAN}${svc}${NC}"
    echo -e "  Status   : [$st_txt]"
    echo -e "  Config   : ${CYAN}${conf}${NC}"

    if [ "$role" == "server" ]; then
        local bind=$(grep -E "bindPort|kcpBindPort|quicBindPort" "$conf" | head -1 | awk '{print $3}')
        local token=$(grep "auth.token" "$conf" | cut -d'"' -f2)
        echo -e "  Bind Port: ${YELLOW}${bind:-N/A}${NC}"
        echo -e "  Token    : ${YELLOW}${token:-N/A}${NC}"
    else
        local server=$(grep "serverAddr" "$conf" | cut -d'"' -f2)
        local sport=$(grep "serverPort" "$conf" | awk '{print $3}')
        local ports=$(grep "remotePort" "$conf" | awk '{print $3}' | tr '\n' ',' | sed 's/,$//')
        echo -e "  Iran IP  : ${YELLOW}${server:-N/A}${NC}"
        echo -e "  ServerPort: ${YELLOW}${sport:-N/A}${NC}"
        echo -e "  Ports    : ${YELLOW}${ports:-N/A}${NC}"
    fi
    echo ""
    return 0
}

check_tunnel_health() {
    show_logo
    echo -e "${CYAN}--- Active Tunnel Connectivity Test ---${NC}"

    echo -e "${PURPLE}Current existing tunnels:${NC}"
    list_tunnels

    select_protocol
    read -p "Enter Tunnel Index (1 to 10): " ID
    
    C_CONF="$CONFIG_DIR/frpc_${PROTOCOL}_tunnel${ID}.toml"
    S_CONF="$CONFIG_DIR/frps_${PROTOCOL}_tunnel${ID}.toml"

    if [ -f "$C_CONF" ]; then
        IRAN_IP=$(grep "serverAddr" "$C_CONF" | cut -d'"' -f2)
        SERVER_PORT=$(grep "serverPort" "$C_CONF" | awk '{print $3}')
        echo -e "${YELLOW}Testing ${PROTO_NAME} connection from Kharej to Iran ($IRAN_IP:$SERVER_PORT)...${NC}"
        
        if [ "$PROTOCOL" == "kcp" ] || [ "$PROTOCOL" == "quic" ]; then
            nc -zu -w 5 "$IRAN_IP" "$SERVER_PORT" 2>/dev/null
        else
            nc -z -w 5 "$IRAN_IP" "$SERVER_PORT" 2>/dev/null
        fi
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[SUCCESS] Connectivity looks good.${NC}"
        else
            echo -e "${RED}[FAILED] Cannot reach Iran server port $SERVER_PORT.${NC}"
        fi

    elif [ -f "$S_CONF" ]; then
        BIND=$(grep -E "bindPort|kcpBindPort|quicBindPort" "$S_CONF" | head -1 | awk '{print $3}')
        echo -e "${ORANGE}Testing local ${PROTO_NAME} Server on port $BIND...${NC}"
        
        if [ "$PROTOCOL" == "kcp" ] || [ "$PROTOCOL" == "quic" ]; then
            if ss -ulnp | grep -q ":$BIND "; then
                echo -e "${GREEN}[SUCCESS] Server is ONLINE (UDP).${NC}"
            else
                echo -e "${RED}[FAILED] Port $BIND not responding.${NC}"
            fi
        else
            nc -z -w 3 127.0.0.1 "$BIND" 2>/dev/null
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}[SUCCESS] Server is ONLINE.${NC}"
            else
                echo -e "${RED}[FAILED] Port $BIND not responding.${NC}"
            fi
        fi
    else
        echo -e "${RED}Tunnel $ID (${PROTO_NAME}) is not configured on this server!${NC}"
    fi

    read -p "Press Enter to return..."
}

manage_tunnels() {
    show_logo
    echo -e "${CYAN}--- Manage / Restart / Logs / Delete Tunnels ---${NC}\n"

    list_tunnels

    echo -e "${CYAN}1. Restart Tunnel${NC}"
    echo -e "${CYAN}2. Stop Tunnel${NC}"
    echo -e "${CYAN}3. View Logs${NC}"
    echo -e "${CYAN}4. Edit Config Manually${NC}"
    echo -e "${LIGHT_RED}5. Delete Tunnel${NC}"
    echo -e "${CYAN}6. Set Auto-Restart Schedule${NC}"
    echo -e "${LIGHT_RED}7. Delete ALL Tunnels${NC}"
    echo -e "${CYAN}0. Back${NC}"
    read -p "Select choice: " ACT
    
    if [ "$ACT" == "0" ]; then return; fi

    if [ "$ACT" == "7" ]; then
        echo -e "${LIGHT_RED}Delete ALL tunnels on this server?${NC}"
        if confirm_yn "Confirm delete all?"; then
            for proto in tcp kcp quic ws; do
                for i in {1..10}; do
                    for role in frps frpc; do
                        svc="${role}_${proto}_tunnel${i}.service"
                        systemctl disable --now "$svc" 2>/dev/null
                        rm -f "/etc/systemd/system/$svc"
                        rm -f "$CONFIG_DIR/${role}_${proto}_tunnel${i}.toml"
                    done
                done
            done
            systemctl daemon-reload
            echo -e "${GREEN}All tunnels deleted.${NC}"
        else
            echo -e "${YELLOW}Cancelled.${NC}"
        fi
        read -p "Press Enter to continue..."
        return
    fi

    select_protocol
    read -p "Enter Tunnel Index (1-10): " ID

    if ! [[ "$ID" =~ ^[1-9]$|^10$ ]]; then
        echo -e "${RED}Invalid ID! Use 1 to 10.${NC}"
        sleep 2
        return
    fi

    S_SVC="frps_${PROTOCOL}_tunnel${ID}.service"
    C_SVC="frpc_${PROTOCOL}_tunnel${ID}.service"
    SVC=""
    ROLE=""
    NAME=""
    CONF=""

    if [ -f "/etc/systemd/system/$S_SVC" ]; then
        SVC="$S_SVC"
        ROLE="Server (Iran)"
        CONF="$CONFIG_DIR/frps_${PROTOCOL}_tunnel${ID}.toml"
        NAME=$(grep "Tunnel_Name" "$CONF" 2>/dev/null | cut -d'"' -f2)
    elif [ -f "/etc/systemd/system/$C_SVC" ]; then
        SVC="$C_SVC"
        ROLE="Client (Kharej)"
        CONF="$CONFIG_DIR/frpc_${PROTOCOL}_tunnel${ID}.toml"
        NAME=$(grep "Tunnel_Name" "$CONF" 2>/dev/null | cut -d'"' -f2)
    fi

    if [ -z "$SVC" ]; then
        echo -e "${RED}Tunnel $ID (${PROTO_NAME}) not found!${NC}"
        sleep 2
        return
    fi

    echo -e "\n${YELLOW}You selected:${NC}"
    echo -e "  Protocol   : ${PROTO_COLOR}${PROTO_NAME}${NC}"
    echo -e "  Tunnel ID  : ${CYAN}${ID}${NC}"
    echo -e "  Name       : ${CYAN}${NAME:-N/A}${NC}"
    echo -e "  Role       : ${CYAN}${ROLE}${NC}"
    echo -e "  Service    : ${CYAN}${SVC}${NC}"
    echo ""

    if [ "$ACT" == "5" ]; then
        echo -e "${LIGHT_RED}WARNING: This will permanently delete the tunnel and its config!${NC}"
        if ! confirm_yn "Delete this tunnel?"; then
            echo -e "${YELLOW}Deletion cancelled.${NC}"
            sleep 1
            return
        fi
    else
        if ! confirm_yn "Is this the correct tunnel? Continue?"; then
            echo -e "${YELLOW}Cancelled.${NC}"
            sleep 1
            return
        fi
    fi

    case $ACT in
        1)
            systemctl restart "$SVC"
            echo -e "${GREEN}Tunnel ${ID} (${PROTO_NAME}) restarted.${NC}"
            ;;
        2)
            systemctl stop "$SVC"
            echo -e "${YELLOW}Tunnel ${ID} (${PROTO_NAME}) stopped.${NC}"
            ;;
        3)
            journalctl -u "$SVC" -n 50 --no-pager
            ;;
        4)
            if [ -n "$CONF" ] && [ -f "$CONF" ]; then
                $(get_editor) "$CONF"
                echo ""
                if confirm_yn "Config edited. Restart the service now?"; then
                    systemctl restart "$SVC"
                    echo -e "${GREEN}Config updated and service restarted.${NC}"
                else
                    echo -e "${YELLOW}Config saved. Service was NOT restarted. Restart manually if needed.${NC}"
                fi
            else
                echo -e "${RED}Config file not found.${NC}"
            fi
            ;;
        5)
            systemctl disable --now "$SVC" 2>/dev/null
            rm -f "/etc/systemd/system/$SVC"
            rm -f "$CONFIG_DIR/frps_${PROTOCOL}_tunnel${ID}.toml"
            rm -f "$CONFIG_DIR/frpc_${PROTOCOL}_tunnel${ID}.toml"
            systemctl daemon-reload
            echo -e "${LIGHT_RED}Tunnel ${ID} (${PROTO_NAME}) deleted.${NC}"
            ;;
        6)
            read -p "Enter restart interval in hours (e.g. 6): " HRS
            if [[ "$HRS" =~ ^[0-9]+$ ]]; then
                (crontab -l 2>/dev/null; echo "0 */$HRS * * * systemctl restart $SVC") | crontab -
                echo -e "${GREEN}Auto-restart set for every $HRS hours.${NC}"
            else
                echo -e "${RED}Invalid number.${NC}"
            fi
            ;;
        *)
            echo -e "${RED}Invalid choice.${NC}"
            ;;
    esac

    read -p "Press Enter to continue..."
}

run_speedtest() {
    show_logo
    echo -e "${CYAN}--- Bandwidth SpeedTest Module ---${NC}\n"
    echo -e "${YELLOW}Important: First run Option 1 (Server Mode) on Kharej server,${NC}"
    echo -e "${YELLOW}then run Option 2 (Client Test) on Iran server.${NC}\n"

    echo -e "${PURPLE}Current existing tunnels:${NC}"
    list_tunnels

    select_protocol
    read -p "Enter Tunnel Index (1 to 10): " ID
    if ! [[ "$ID" =~ ^[1-9]$|^10$ ]]; then
        echo -e "${RED}Invalid ID!${NC}"; sleep 2; return
    fi

    case $PROTOCOL in
        tcp)  DEFAULT_PORT=$((55109 + ID)) ;;
        kcp)  DEFAULT_PORT=$((55209 + ID)) ;;
        quic) DEFAULT_PORT=$((55409 + ID)) ;;
        ws)   DEFAULT_PORT=$((55309 + ID)) ;;
    esac

    echo -e "${YELLOW}Default iperf3 port for this tunnel: ${DEFAULT_PORT}${NC}\n"
    echo "1. Run iperf3 Server Mode (aval rooye Kharej)"
    echo "2. Run iperf3 Client Test (baad rooye Iran)"
    read -p "Select option: " TEST_OPT

    if [ "$TEST_OPT" == "1" ]; then
        read -p "Port iperf server [Default: $DEFAULT_PORT]: " SPORT
        SPORT=${SPORT:-$DEFAULT_PORT}
        if ! [[ "$SPORT" =~ ^[0-9]+$ ]]; then
            echo -e "${RED}Port na-motabar.${NC}"; sleep 2; return
        fi
        allow_ufw_port "$SPORT"
        fuser -k "${SPORT}/tcp" >/dev/null 2>&1
        echo -e "${GREEN}Starting iperf3 server on port $SPORT... (CTRL+C to stop)${NC}"
        iperf3 -s -p "$SPORT"
    elif [ "$TEST_OPT" == "2" ]; then
        read -p "Enter target port [Default: $DEFAULT_PORT]: " TARGET_PORT
        TARGET_PORT=${TARGET_PORT:-$DEFAULT_PORT}

        echo -e "\n1) 5s  2) 10s  3) Custom"
        read -p "Duration: " DUR_OPT
        case $DUR_OPT in
            1) DURATION=5 ;;
            2) DURATION=10 ;;
            3) read -p "Seconds: " DURATION; DURATION=${DURATION:-10} ;;
            *) DURATION=10 ;;
        esac

        echo -e "\n${YELLOW}Testing through ${PROTO_NAME} tunnel...${NC}"
        RAW_JSON=$(iperf3 -c 127.0.0.1 -p "$TARGET_PORT" -P 8 -t "$DURATION" --json 2>/dev/null)
        
        if [ -z "$RAW_JSON" ]; then
            echo -e "${RED}[ERROR] Failed! Make sure Server mode is running on Kharej first.${NC}"
        else
            MBPS=$(python3 -c '
import sys, json
try:
    data = json.loads(sys.argv[1])
    bps = data["end"]["sum_received"]["bits_per_second"]
    print(f"{bps / 1e6:.2f}")
except:
    try:
        bps = data["end"]["sum_sent"]["bits_per_second"]
        print(f"{bps / 1e6:.2f}")
    except:
        print("0")
' "$RAW_JSON" 2>/dev/null)

            if [ -n "$MBPS" ] && [ "$MBPS" != "0" ]; then
                echo -e "\n${GREEN}================ SPEEDTEST RESULTS ================${NC}"
                echo -e "Protocol       : ${PROTO_COLOR}${PROTO_NAME}${NC}"
                echo -e "Tunnel ID      : ${ORANGE}${ID}${NC}"
                echo -e "Throughput     : ${CYAN}${MBPS} Mbps${NC}"
                echo -e "${GREEN}===================================================${NC}\n"
            else
                echo -e "${RED}Failed to parse results.${NC}"
            fi
        fi
    fi
    read -p "Press Enter to return..."
}

optimize_system() {
    show_logo
    echo -e "${CYAN}--- System Optimization (High Bandwidth) ---${NC}\n"
    echo "1) Optimize for TCP / WebSocket (BBR + large TCP buffers)"
    echo "2) Optimize for KCP / QUIC (UDP buffers)"
    echo "3) Both + Extra high-BW tweaks"
    read -p "Select: " OPT

    if [ "$OPT" == "1" ] || [ "$OPT" == "3" ]; then
        cat << EOF > /etc/sysctl.d/99-frp-tcp.conf
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
EOF
        sysctl -p /etc/sysctl.d/99-frp-tcp.conf >/dev/null 2>&1
        echo -e "${GREEN}TCP/BBR + large buffers optimized.${NC}"
    fi

    if [ "$OPT" == "2" ] || [ "$OPT" == "3" ]; then
        cat << EOF > /etc/sysctl.d/99-frp-udp.conf
net.core.rmem_max = 67108864
net.core.wmem_max = 67108864
net.core.rmem_default = 16777216
net.core.wmem_default = 16777216
net.core.netdev_max_backlog = 250000
net.ipv4.udp_rmem_min = 8192
net.ipv4.udp_wmem_min = 8192
net.ipv4.udp_mem = 8388608 12582912 16777216
EOF
        sysctl -p /etc/sysctl.d/99-frp-udp.conf >/dev/null 2>&1
        echo -e "${GREEN}UDP buffers optimized.${NC}"
    fi

    if [ "$OPT" == "3" ]; then
        cat << EOF > /etc/security/limits.d/99-frp.conf
* soft nofile 1048576
* hard nofile 1048576
root soft nofile 1048576
root hard nofile 1048576
EOF
        echo -e "${GREEN}File descriptor limits raised.${NC}"
    fi

    echo -e "${YELLOW}Recommendation: Restart services or reboot for full effect.${NC}"
    read -p "Press Enter to return..."
}



setup_aggregation() {
    show_logo
    load_defaults
    echo -e "${ORANGE}=== Multi-Tunnel + HAProxy ===${NC}\n"
    echo -e "Iran: chand tunnel FRP + HAProxy (har public port = yek balanser)"
    echo -e "Kharej: frpc → Xray/service local"
    echo -e "Mesal: Client → Iran:443 → tunnels → Kharej:443 (Xray)\n"
    echo -e "${PURPLE}Tunnel-haye feli:${NC}"
    list_tunnels

    echo -e "\n${CYAN}Samt:${NC}"
    echo -e "  1) Iran  (frps + HAProxy + ghavanin routing)  ← AVVAL inja"
    echo -e "  2) Kharej (frpc)  ← baad, line-haye compact az Iran ra paste kon"
    read -p "Select [1-2]: " SIDE
    SIDE=${SIDE:-1}

    if [ "$SIDE" == "1" ]; then
        # ========== IRAN SIDE ==========
        echo -e "
${ORANGE}=== Tunnel Protocol Preset ===${NC}"
        echo -e "${YELLOW}Noe ertebat control FRP (TCP/WS/KCP). Traffic Xray hamishe TCP proxy ast.${NC}"
        echo -e "  1) All TCP x4      — sadeh/paydar (pishnahad Xray gRPC)"
        echo -e "  2) 2x TCP + 2x WS  — nime TCP, nime WebSocket"
        echo -e "  3) Mix TCP + WS    — tedad dasti"
        echo -e "  4) N x WebSocket   — faghat WS"
        echo -e "  5) N x KCP         — bar asase UDP"
        echo -e "  6) N x TCP only    — tedad TCP (1-8)"
        echo -e "  7) Custom mix      — TCP + WS + KCP"
        echo -e "Mesal: 4 tunnel TCP baraye bandwidth → gozine 1"
        read -p "Select preset [1-7]: " PRESET
        PRESET=${PRESET:-1}

        NUM_TCP=0; NUM_WS=0; NUM_KCP=0
        case $PRESET in
            1) NUM_TCP=4 ;;
            2) NUM_TCP=2; NUM_WS=2 ;;
            3)
                read -p "TCP count: " NUM_TCP; NUM_TCP=${NUM_TCP:-2}
                read -p "WebSocket count: " NUM_WS; NUM_WS=${NUM_WS:-2}
                ;;
            4) read -p "WebSocket count: " NUM_WS; NUM_WS=${NUM_WS:-4} ;;
            5) read -p "KCP count: " NUM_KCP; NUM_KCP=${NUM_KCP:-4} ;;
            6) read -p "TCP count: " NUM_TCP; NUM_TCP=${NUM_TCP:-4} ;;
            7)
                read -p "TCP count: " NUM_TCP; NUM_TCP=${NUM_TCP:-0}
                read -p "WebSocket count: " NUM_WS; NUM_WS=${NUM_WS:-0}
                read -p "KCP count: " NUM_KCP; NUM_KCP=${NUM_KCP:-0}
                ;;
            *) NUM_TCP=4 ;;
        esac
        NUM_TCP=${NUM_TCP:-0}; NUM_WS=${NUM_WS:-0}; NUM_KCP=${NUM_KCP:-0}
        NUM_TUNNELS=$((NUM_TCP + NUM_WS + NUM_KCP))
        if [ "$NUM_TUNNELS" -lt 1 ] || [ "$NUM_TUNNELS" -gt 8 ]; then
            echo -e "${RED}Total tunnels must be 1-8 (got $NUM_TUNNELS).${NC}"
            sleep 2; return
        fi
        echo -e "${GREEN}Plan: TCP=$NUM_TCP  WS=$NUM_WS  KCP=$NUM_KCP  (total $NUM_TUNNELS)${NC}"

        declare -a PROTO_LIST=()
        for ((i=0; i<NUM_TCP; i++)); do PROTO_LIST+=("tcp"); done
        for ((i=0; i<NUM_WS; i++)); do PROTO_LIST+=("ws"); done
        for ((i=0; i<NUM_KCP; i++)); do PROTO_LIST+=("kcp"); done

        echo -e "\n${CYAN}--- Base Tunnel Index ---${NC}"
        echo -e "Shomare shoroo'e tunnel-ha (poshte sar ham)."
        echo -e "  Mesal: base=1 va 4 tunnel → ID-ha: 1,2,3,4"
        echo -e "  Mesal: base=5 va 2 tunnel → ID-ha: 5,6"
        echo -e "Agar ghablan tunnel 1-3 dari, base ra 4 begzar ta conflict nashe."
        read -p "Base Tunnel Index (1-10) [1]: " BASE_ID
        BASE_ID=${BASE_ID:-1}
        if ! [[ "$BASE_ID" =~ ^[1-9]$|^10$ ]]; then
            echo -e "${RED}Invalid base ID.${NC}"; sleep 2; return
        fi
        END_ID=$((BASE_ID + NUM_TUNNELS - 1))
        if [ "$END_ID" -gt 10 ]; then
            echo -e "${RED}Not enough free IDs (max 10).${NC}"
            sleep 2; return
        fi

# (no HAProxy iperf frontend)

        echo -e "\n${ORANGE}--- Configuring IRAN side (frps) ---${NC}"

        declare -a BIND_PORTS
        declare -a TOKENS
        declare -a REMOTE_PORTS
        declare -a IPERF_REMOTE_PORTS
        declare -a ALL_TIDS
        COMPACT_LINES=""

        for ((i=0; i<NUM_TUNNELS; i++)); do
            TID=$((BASE_ID + i))
            ALL_TIDS[$i]=$TID
            THIS_PROTO="${PROTO_LIST[$i]}"
            THIS_PROTO_NAME=$(echo "$THIS_PROTO" | tr 'a-z' 'A-Z')
            [ "$THIS_PROTO" == "ws" ] && THIS_PROTO_NAME="WebSocket"
            echo -e "\n${CYAN}Tunnel #$((i+1)) (ID $TID) Protocol=${THIS_PROTO_NAME}${NC}"

            if show_existing_tunnel_info "server" "$THIS_PROTO" "$TID"; then
                if ! confirm_yn "Overwrite existing tcp tunnel $TID?"; then
                    echo -e "${YELLOW}Skipping this ID...${NC}"
                    continue
                fi
                systemctl stop "frps_${THIS_PROTO}_tunnel${TID}.service" 2>/dev/null
            fi

            BIND_PORT=$(generate_random_port)
            AUTH_TOKEN=$(generate_token "$DEFAULT_TOKEN_LENGTH")
            REMOTE_PORT=$((20000 + BASE_ID * 100 + i))
            IPERF_RPORT=$((21000 + BASE_ID * 100 + i))

            BIND_PORTS[$i]=$BIND_PORT
            TOKENS[$i]=$AUTH_TOKEN
            REMOTE_PORTS[$i]=$REMOTE_PORT
            IPERF_REMOTE_PORTS[$i]=$IPERF_RPORT

            COMPACT_LINES="${COMPACT_LINES}${TID},${THIS_PROTO},${BIND_PORT},${AUTH_TOKEN},${REMOTE_PORT},${IPERF_RPORT}\n"

            TUNNEL_NAME="agg${BASE_ID}_${i}"
            USE_TCPMUX="false"
            MAX_POOL=150
            HEARTBEAT_TIMEOUT=90

            CONF_FILE="$CONFIG_DIR/frps_${THIS_PROTO}_tunnel${TID}.toml"
            case $THIS_PROTO in
                tcp|ws)
                    cat << EOF > "$CONF_FILE"
# Tunnel_Name = "$TUNNEL_NAME"
# Protocol   = $THIS_PROTO_NAME
# Aggregation group base=$BASE_ID
bindAddr = "0.0.0.0"
bindPort = $BIND_PORT
auth.method = "token"
auth.token = "$AUTH_TOKEN"
transport.tcpMux = $USE_TCPMUX
transport.maxPoolCount = $MAX_POOL
transport.heartbeatTimeout = $HEARTBEAT_TIMEOUT
EOF
                    allow_ufw_port "$BIND_PORT" "tcp"
                    ;;
                kcp)
                    cat << EOF > "$CONF_FILE"
# Tunnel_Name = "$TUNNEL_NAME"
# Protocol   = KCP
# Aggregation group base=$BASE_ID
bindAddr = "0.0.0.0"
bindPort = $BIND_PORT
kcpBindPort = $BIND_PORT
auth.method = "token"
auth.token = "$AUTH_TOKEN"
transport.tcpMux = $USE_TCPMUX
transport.maxPoolCount = $MAX_POOL
transport.heartbeatTimeout = $HEARTBEAT_TIMEOUT
EOF
                    allow_ufw_port "$BIND_PORT" "udp"
                    allow_ufw_port "$BIND_PORT" "tcp"
                    ;;
            esac

            SERVICE_FILE="/etc/systemd/system/frps_${THIS_PROTO}_tunnel${TID}.service"
            cat << EOF > "$SERVICE_FILE"
[Unit]
Description=FRP ${THIS_PROTO_NAME} Server Aggregation Tunnel ${TID} (${TUNNEL_NAME})
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/frps -c $CONF_FILE
Restart=always
RestartSec=5s
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF
            systemctl daemon-reload
            systemctl enable "frps_${THIS_PROTO}_tunnel${TID}.service"
            systemctl restart "frps_${THIS_PROTO}_tunnel${TID}.service"
            echo -e "${GREEN}frps ${THIS_PROTO_NAME} tunnel $TID started (bind $BIND_PORT | remote $REMOTE_PORT)${NC}"
        done

        # ---- Routing rules: one balancer per public port ----
        echo -e "\n${ORANGE}=== HAProxy Routing (yeki balanser per port) ===${NC}"
        echo -e "Har public port = yek frontend + yek backend joda."
        echo -e "Client be an port mizanad; HAProxy beyne tunnel-haye an port load-balance mikonad.\n"
        echo -e "${CYAN}Mesal:${NC}"
        echo -e "  Port 443  + tunnels all  → balanser baraye Xray asli"
        echo -e "  Port 2053 + tunnels all  → balanser joda baraye inbound digar"
        echo -e "  Port 2090 + tunnels 1,2  → faghat 2 tunnel\n"
        echo -e "Tunnel IDs: benevis ${GREEN}all${NC} ya Enter = hame tunnel-ha"
        echo -e "Port khali = payan.\n"

        declare -a RULE_PORTS
        declare -a RULE_TUNNELS
        RULE_COUNT=0
        ALL_TIDS_STR=$(IFS=,; echo "${ALL_TIDS[*]}")

        while true; do
            RULE_COUNT=$((RULE_COUNT + 1))
            echo -e "${CYAN}--- Balancer #$RULE_COUNT ---${NC}"
            read -p "Public port (e.g. 443) ya khali=payan: " PORTS_IN
            PORTS_IN=$(echo "$PORTS_IN" | xargs)
            if [ -z "$PORTS_IN" ]; then
                RULE_COUNT=$((RULE_COUNT - 1))
                break
            fi
            # If user entered multiple ports comma-separated, expand later to one rule each
            echo -n "Tunnel-ha (all / Enter / 1,2,3): "
            echo -n "available=[${ALL_TIDS_STR}] "
            read -p "" TIDS_IN
            TIDS_IN=$(echo "$TIDS_IN" | xargs)
            if [ -z "$TIDS_IN" ] || [ "$TIDS_IN" = "all" ] || [ "$TIDS_IN" = "ALL" ]; then
                TIDS_IN="$ALL_TIDS_STR"
            fi

            IFS=',' read -ra PARR <<< "$PORTS_IN"
            for p in "${PARR[@]}"; do
                p=$(echo "$p" | xargs)
                [ -z "$p" ] && continue
                if ! [[ "$p" =~ ^[0-9]+$ ]]; then
                    echo -e "${RED}Port na-motabar: $p — skip${NC}"
                    continue
                fi
                RULE_PORTS+=("$p")
                RULE_TUNNELS+=("$TIDS_IN")
                echo -e "${GREEN}  + balanser :${p} → tunnels [${TIDS_IN}]${NC}"
            done
        done

        if [ ${#RULE_PORTS[@]} -eq 0 ]; then
            echo -e "${YELLOW}Hich porti nadadi — pishfarz 443 → all tunnels${NC}"
            RULE_PORTS+=("443")
            RULE_TUNNELS+=("$ALL_TIDS_STR")
        fi
        RULE_COUNT=${#RULE_PORTS[@]}

        echo -e "\n${YELLOW}Installing HAProxy (agar nist)...${NC}"
        if ! command -v haproxy >/dev/null 2>&1; then
            apt-get install -y haproxy
        fi

        # Build HAProxy: one frontend/backend per port (2GB RAM / 2 CPU defaults)
        HAPROXY_BODY=""
        for ((r=0; r<RULE_COUNT; r++)); do
            p="${RULE_PORTS[$r]}"
            TIDS_LIST="${RULE_TUNNELS[$r]}"
            FE_NAME="fe_p${p}"
            BE_NAME="be_p${p}"

            SERVERS=""
            IFS=',' read -ra TARR <<< "$TIDS_LIST"
            for tid in "${TARR[@]}"; do
                tid=$(echo "$tid" | xargs)
                [ -z "$tid" ] && continue
                rport=""
                for ((i=0; i<NUM_TUNNELS; i++)); do
                    if [ "${ALL_TIDS[$i]}" = "$tid" ]; then
                        rport="${REMOTE_PORTS[$i]}"
                        break
                    fi
                done
                if [ -z "$rport" ]; then
                    echo -e "${RED}Tunnel ID $tid remotePort nadarad — skip${NC}"
                    continue
                fi
                SERVERS="${SERVERS}    server t${tid} 127.0.0.1:${rport} check inter 3s fall 3 rise 2 weight 100\n"
            done

            HAPROXY_BODY="${HAPROXY_BODY}
# Port ${p} → tunnels [${TIDS_LIST}]
frontend ${FE_NAME}
    bind *:${p}
    mode tcp
    default_backend ${BE_NAME}

backend ${BE_NAME}
    mode tcp
    balance roundrobin
    option tcp-check
$(echo -e "$SERVERS")
"
            allow_ufw_port "$p" "tcp"
        done

        cat << EOF > "$HAPROXY_CFG"
# FRP Multi-Tunnel HAProxy
# BaseID=${BASE_ID} tunnels=${NUM_TUNNELS} balancers=${RULE_COUNT}
# Tuned for ~2GB RAM / 2 CPU

global
    log /dev/log local0 notice
    maxconn 100000
    tune.bufsize 32768
    tune.maxrewrite 1024
    nbthread 2
    cpu-map auto:1/1-2 0-1

defaults
    log     global
    mode    tcp
    option  tcplog
    option  dontlognull
    option  redispatch
    option  clitcpka
    option  srvtcpka
    timeout connect 5s
    timeout client  1h
    timeout server  1h
    timeout tunnel  1h
    timeout check   3s
    maxconn 50000
    retries 3

$(echo -e "$HAPROXY_BODY")
EOF

        cat << EOF > /etc/systemd/system/haproxy-frp-agg.service
[Unit]
Description=HAProxy FRP Aggregation
After=network.target

[Service]
Type=notify
ExecStart=/usr/sbin/haproxy -f $HAPROXY_CFG -Ws
ExecReload=/bin/kill -USR2 \$MAINPID
Restart=always
RestartSec=3s
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF

        if haproxy -c -f "$HAPROXY_CFG" >/dev/null 2>&1; then
            systemctl daemon-reload
            systemctl enable haproxy-frp-agg.service
            systemctl restart haproxy-frp-agg.service
            echo -e "${GREEN}HAProxy OK — ${RULE_COUNT} balanser${NC}"
        else
            echo -e "${RED}HAProxy config invalid:${NC}"
            haproxy -c -f "$HAPROXY_CFG"
        fi

        MY_IP=$(curl -s --max-time 3 http://ip-api.com/line/?fields=query 2>/dev/null)

        # Save compact + rules
        COMPACT_FILE="$CONFIG_DIR/aggregation_${BASE_ID}_compact.txt"
        {
            echo "# FRP Aggregation Compact Config - BaseID=$BASE_ID"
            echo "# IranIP=${MY_IP}"
            echo "# Format: ID,protocol,bindPort,token,remotePort,iperfRemotePort"
            echo -e "$COMPACT_LINES"
            echo ""
            echo "# Routing rules (Iran public ports → tunnel IDs):"
            for ((r=0; r<RULE_COUNT; r++)); do
                echo "# Rule $((r+1)): ports=${RULE_PORTS[$r]} → tunnels=${RULE_TUNNELS[$r]}"
            done
            echo "# On Kharej set localPort per tunnel group to match your Xray/services."
        } > "$COMPACT_FILE"

        # Save rules for later edit
        RULES_FILE="$CONFIG_DIR/aggregation_${BASE_ID}_rules.conf"
        {
            echo "BASE_ID=$BASE_ID"
            echo "NUM_TUNNELS=$NUM_TUNNELS"
            echo "IRAN_IP=${MY_IP}"
            echo "RULE_COUNT=$RULE_COUNT"
            for ((r=0; r<RULE_COUNT; r++)); do
                echo "RULE_${r}_PORTS=${RULE_PORTS[$r]}"
                echo "RULE_${r}_TUNNELS=${RULE_TUNNELS[$r]}"
            done
            for ((i=0; i<NUM_TUNNELS; i++)); do
                echo "T${ALL_TIDS[$i]}_REMOTE=${REMOTE_PORTS[$i]}"
                echo "T${ALL_TIDS[$i]}_IPERF=${IPERF_REMOTE_PORTS[$i]}"
            done
        } > "$RULES_FILE"

        echo -e "\n${GREEN}================ IRAN SIDE AGGREGATION READY ================${NC}"
        echo -e "Server IP            : ${CYAN}${MY_IP}${NC}"
        echo -e "\n${CYAN}Active routing rules:${NC}"
        for ((r=0; r<RULE_COUNT; r++)); do
            echo -e "  Rule $((r+1)): ports [${YELLOW}${RULE_PORTS[$r]}${NC}] → tunnels [${YELLOW}${RULE_TUNNELS[$r]}${NC}]"
        done
        echo -e "\n${ORANGE}========== COPY THESE LINES TO KHAREJ (option 10 → side 2) ==========${NC}"
        echo -e "${CYAN}# Format: ID,protocol,bindPort,token,remotePort,iperfRemotePort${NC}"
        echo -e "$COMPACT_LINES"
        echo -e "${ORANGE}====================================================================${NC}"
        echo -e "\n${GREEN}Saved: ${COMPACT_FILE}${NC}"
        echo -e "${GREEN}Rules: ${RULES_FILE}${NC}"
        echo -e "${YELLOW}You can change routing later from menu option 11.${NC}\n"

    else
        # ========== KHAREJ SIDE - compact paste ==========
        echo -e "\n${YELLOW}--- Configuring KHAREJ side (frpc clients) ---${NC}"
        echo -e "${YELLOW}IP ya domain server Iran (hamanja ke frps + HAProxy hast).${NC}"
        echo -e "  Mesal: 2.3.4.5   ya   iran.example.com"
        read -p "Iran Server IP/Domain: " IRAN_IP

        echo -e "\n${CYAN}Local service port(s) on THIS server (Kharej)${NC}"
        echo -e "${YELLOW}Inja Xray/service rooye 127.0.0.1 gush midahad (na port public Iran).${NC}"
        echo -e "${YELLOW}Agar chand config Xray dari, baraye har goruh tunnel localPort joda bedeh.${NC}"
        echo -e "  ${CYAN}Mesal 1:${NC} 443                    → hame tunnel-ha be 443"
        echo -e "  ${CYAN}Mesal 2:${NC} 1=443,2=443,3=2080,4=2080"
        echo -e "  ${CYAN}Mesal 3:${NC} 1-2=443,3-4=2090,5-6=8080"
        echo -e "  ${CYAN}Mesal 4:${NC} 443,8080               → avalin port = default (443)"
        echo -e "${GREEN}Default: 443${NC}"
                echo -e "${YELLOW}In adad bayad ba inbound Xray rooye HAMIN server yeki bashad.${NC}"
        echo -e "  Agar HAProxy Iran port 443 → tunnel 1-2 va Xray Kharej :443  →  1-2=443"
        echo -e "  Agar HAProxy Iran port 2090 → tunnel 3-4 va Xray :2090 →  3-4=2090"
        echo -e "  Port public Iran ra inja NA-nevis; faqat port local Xray/service.${NC}"
read -p "Local port map [443]: " LOCAL_PORTS_IN
        LOCAL_PORTS_IN=${LOCAL_PORTS_IN:-443}

        # Build TID→localPort map (default 443)
        declare -A TID_LOCAL_MAP
        DEFAULT_LOCAL=443
        if [[ "$LOCAL_PORTS_IN" =~ ^[0-9]+$ ]]; then
            DEFAULT_LOCAL=$LOCAL_PORTS_IN
        elif [[ "$LOCAL_PORTS_IN" == *=* ]]; then
            IFS=',' read -ra _parts <<< "$LOCAL_PORTS_IN"
            for part in "${_parts[@]}"; do
                part=$(echo "$part" | xargs)
                [ -z "$part" ] && continue
                left=${part%%=*}
                right=${part#*=}
                right=$(echo "$right" | xargs)
                [[ "$right" =~ ^[0-9]+$ ]] || continue
                if [[ "$left" =~ ^[0-9]+-[0-9]+$ ]]; then
                    lo=${left%-*}; hi=${left#*-}
                    for ((t=lo; t<=hi; t++)); do TID_LOCAL_MAP[$t]=$right; done
                elif [[ "$left" =~ ^[0-9]+$ ]]; then
                    TID_LOCAL_MAP[$left]=$right
                fi
            done
        else
            # comma list of ports → use first as default for all
            DEFAULT_LOCAL=$(echo "$LOCAL_PORTS_IN" | cut -d',' -f1 | xargs)
            DEFAULT_LOCAL=${DEFAULT_LOCAL:-443}
        fi
        PRIMARY_LOCAL=$DEFAULT_LOCAL

        echo -e "${CYAN}Default localPort: ${PRIMARY_LOCAL}${NC}"
        if [ ${#TID_LOCAL_MAP[@]} -gt 0 ]; then
            echo -e "${CYAN}Per-tunnel map:${NC}"
            for k in $(echo "${!TID_LOCAL_MAP[@]}" | tr ' ' '\n' | sort -n); do
                echo -e "  tunnel $k → 127.0.0.1:${TID_LOCAL_MAP[$k]}"
            done
        fi

        # warn if default not listening
        if command -v ss >/dev/null 2>&1; then
            if ss -tlnp 2>/dev/null | grep -q ":${PRIMARY_LOCAL} "; then
                echo -e "${GREEN}OK: something listening on :${PRIMARY_LOCAL}${NC}"
            else
                echo -e "${LIGHT_RED}WARNING: nothing listening on :${PRIMARY_LOCAL} now.${NC}"
                if ! confirm_yn "Continue anyway?"; then
                    echo -e "${YELLOW}Cancelled.${NC}"; sleep 2; return
                fi
            fi
        fi

        echo -e "\n${CYAN}Paste the compact lines from Iran (one per line).${NC}"
        echo -e "${CYAN}Format: ID,protocol,bindPort,token,remotePort,iperfRemotePort${NC}"
        echo -e "${YELLOW}Rule comment lines (# Rule ...) optional; empty line = finish.${NC}\n"

declare -a PASTED_LINES
        while true; do
            read -p "Line (or empty to finish): " LINE
            LINE=$(echo "$LINE" | xargs)
            if [ -z "$LINE" ]; then
                break
            fi
            if [[ "$LINE" == \#* ]]; then
                continue
            fi
            PASTED_LINES+=("$LINE")
        done

        if [ ${#PASTED_LINES[@]} -eq 0 ]; then
            echo -e "${RED}No lines pasted. Cancelled.${NC}"
            sleep 2; return
        fi

        echo -e "\n${GREEN}Processing ${#PASTED_LINES[@]} tunnel(s)...${NC}"

        for LINE in "${PASTED_LINES[@]}"; do
            # Support both old (5 fields) and new (6 fields with protocol)
            IFS=',' read -r F1 F2 F3 F4 F5 F6 <<< "$LINE"
            if [ -n "$F6" ]; then
                TID=$(echo "$F1" | xargs)
                THIS_PROTO=$(echo "$F2" | xargs)
                BIND_PORT=$(echo "$F3" | xargs)
                AUTH_TOKEN=$(echo "$F4" | xargs)
                REMOTE_PORT=$(echo "$F5" | xargs)
                IPERF_RPORT=$(echo "$F6" | xargs)
            else
                TID=$(echo "$F1" | xargs)
                THIS_PROTO="tcp"
                BIND_PORT=$(echo "$F2" | xargs)
                AUTH_TOKEN=$(echo "$F3" | xargs)
                REMOTE_PORT=$(echo "$F4" | xargs)
                IPERF_RPORT=$(echo "$F5" | xargs)
            fi

            if [ -z "$TID" ] || [ -z "$BIND_PORT" ] || [ -z "$AUTH_TOKEN" ] || [ -z "$REMOTE_PORT" ]; then
                echo -e "${RED}Invalid line, skipping: $LINE${NC}"
                continue
            fi

            echo -e "\n${CYAN}=== Tunnel ID $TID ===${NC}"
            echo -e "  BindPort=$BIND_PORT  RemotePort=$REMOTE_PORT  Iperf=$IPERF_RPORT"

            if show_existing_tunnel_info "client" "$THIS_PROTO" "$TID"; then
                if ! confirm_yn "Overwrite existing tcp client tunnel $TID?"; then
                    echo -e "${YELLOW}Skipping...${NC}"
                    continue
                fi
                systemctl stop "frpc_${THIS_PROTO}_tunnel${TID}.service" 2>/dev/null
            fi

            TUNNEL_NAME="agg${TID}"
            USE_TCPMUX="false"
            POOL_COUNT=80
            HEARTBEAT_INTERVAL=30
            HEARTBEAT_TIMEOUT=90
            LOCAL_IPERF_PORT=$((55109 + TID))

            CONF_FILE="$CONFIG_DIR/frpc_${THIS_PROTO}_tunnel${TID}.toml"
            cat << EOF > "$CONF_FILE"
# Tunnel_Name = "$TUNNEL_NAME"
# Protocol   = $THIS_PROTO
# Aggregation (from compact import)
serverAddr = "$IRAN_IP"
serverPort = $BIND_PORT
auth.method = "token"
auth.token = "$AUTH_TOKEN"
transport.tcpMux = $USE_TCPMUX
transport.poolCount = $POOL_COUNT
transport.heartbeatInterval = $HEARTBEAT_INTERVAL
transport.heartbeatTimeout = $HEARTBEAT_TIMEOUT
EOF
            case $THIS_PROTO in
                kcp) echo 'transport.protocol = "kcp"' >> "$CONF_FILE" ;;
                ws)  echo 'transport.protocol = "websocket"' >> "$CONF_FILE" ;;
            esac
            cat << EOF >> "$CONF_FILE"

EOF
            # Add one proxy per local service port → same remotePort
            # Note: FRP allows only one remotePort per proxy; for multi local ports
            # we map each local port to the SAME remotePort only if one port,
            # but for multi-port rules we need the service on Kharej to listen on those ports.
            # Simplest correct approach: map each local port to its own remotePort only if single,
            # but for aggregation HAProxy expects specific remotePorts.
            # So we map the *first* local port to remotePort, and user should run the real service
            # on that port, OR we create multiple proxies with same remotePort (not allowed).
            # Correct: for multi public ports going to same tunnel group, the backend service
            # on Kharej is usually one process; HAProxy differentiates by public port only.
            # So on Kharej we only need to expose the service once per tunnel (one localPort).
            # User can choose primary local port.
            THIS_LOCAL=${TID_LOCAL_MAP[$TID]:-$DEFAULT_LOCAL}
            THIS_LOCAL=${THIS_LOCAL:-443}

            cat << EOF >> "$CONF_FILE"
[[proxies]]
name = "${TUNNEL_NAME}_svc_${REMOTE_PORT}"
type = "tcp"
localIP = "127.0.0.1"
localPort = $THIS_LOCAL
remotePort = $REMOTE_PORT

[[proxies]]
name = "${TUNNEL_NAME}_iperf_${IPERF_RPORT}"
type = "tcp"
localIP = "127.0.0.1"
localPort = $LOCAL_IPERF_PORT
remotePort = $IPERF_RPORT
EOF

            # If user has multiple local ports and wants each tunnel to forward multiple,
            # we can add extra proxies only when remote ports differ - but for same backend group
            # all tunnels share the same service. So one localPort is enough.
            # Optionally map extra local ports to the same remotePort is invalid in FRP.
            # Document this clearly.

            allow_ufw_port "$THIS_LOCAL"
            allow_ufw_port "$LOCAL_IPERF_PORT"

            SERVICE_FILE="/etc/systemd/system/frpc_${THIS_PROTO}_tunnel${TID}.service"
            cat << EOF > "$SERVICE_FILE"
[Unit]
Description=FRP ${THIS_PROTO} Client Aggregation Tunnel ${TID} (${TUNNEL_NAME})
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/frpc -c $CONF_FILE
Restart=always
RestartSec=5s
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF
            systemctl daemon-reload
            systemctl enable "frpc_${THIS_PROTO}_tunnel${TID}.service"
            systemctl restart "frpc_${THIS_PROTO}_tunnel${TID}.service"
            echo -e "${GREEN}frpc tunnel $TID started (local service port(s) mapped per tunnel)${NC}"
        done

        echo -e "\n${GREEN}================ KHAREJ SIDE READY ================${NC}"
        echo -e "Primary local service port used: ${CYAN}${PRIMARY_LOCAL}${NC}"
        echo -e "${YELLOW}Note: HAProxy on Iran routes different *public* ports to different tunnel groups.${NC}"
        echo -e "${YELLOW}On Kharej the real service usually listens on one port; all tunnels of a group${NC}"
        echo -e "${YELLOW}point to that same local service. Multiple public ports → same backend is fine.${NC}"
        echo -e "\n${YELLOW}Test:${NC} iperf3 from Iran to the aggregated iperf port with -P 16"
        echo -e "${GREEN}===================================================${NC}\n"
    fi

    read -p "Press Enter to return..."
}

# ========== Manage HAProxy Aggregation ==========


# ========== Show HAProxy port mapping ==========
show_haproxy_port_map() {
    if [ ! -f "$HAPROXY_CFG" ]; then
        return 1
    fi
    echo -e "${PURPLE}--- HAProxy Port Mapping ---${NC}"
    local fe="" be="" bindp=""
    while IFS= read -r line || [ -n "$line" ]; do
        if echo "$line" | grep -qE '^frontend '; then
            fe=$(echo "$line" | awk '{print $2}')
            bindp=""
        elif echo "$line" | grep -qE '^[[:space:]]*bind '; then
            bindp=$(echo "$line" | sed -n 's/.*:\([0-9][0-9]*\).*/\1/p')
        elif echo "$line" | grep -qE '^backend '; then
            be=$(echo "$line" | awk '{print $2}')
            if [ -n "$fe" ] && [ -n "$bindp" ]; then
                echo -e "  ${CYAN}Frontend ${fe}${NC}  bind :${GREEN}${bindp}${NC}  →  backend ${YELLOW}${be}${NC}"
            fi
        elif echo "$line" | grep -qE '^[[:space:]]*server '; then
            local sname sport st
            sname=$(echo "$line" | awk '{print $2}')
            sport=$(echo "$line" | sed -n 's/.*127\.0\.0\.1:\([0-9][0-9]*\).*/\1/p')
            [ -z "$sport" ] && sport=$(echo "$line" | sed -n 's/.*:\([0-9][0-9]*\).*/\1/p')
            if [ -n "$sport" ] && ss -tlnp 2>/dev/null | grep -q ":${sport} "; then
                st="${GREEN}LISTEN${NC}"
            else
                st="${YELLOW}?${NC}"
            fi
            echo -e "      → ${sname}  127.0.0.1:${CYAN}${sport}${NC}  [$st]"
        fi
    done < "$HAPROXY_CFG"
    echo -e "${PURPLE}----------------------------${NC}"
    return 0
}

manage_haproxy() {
    show_logo
    echo -e "${CYAN}=== Manage HAProxy ===${NC}\n"

    if [ ! -f "$HAPROXY_CFG" ]; then
        echo -e "${YELLOW}Config HAProxy nist. Aval option 10 (Iran) ra ejra kon.${NC}"
        read -p "Enter..."
        return
    fi

    STATUS=$(systemctl is-active haproxy-frp-agg.service 2>/dev/null || echo "off")
    if [ "$STATUS" == "active" ]; then
        ST_TXT="${GREEN}ONLINE${NC}"
    else
        ST_TXT="${RED}${STATUS}${NC}"
    fi
    echo -e "Service : haproxy-frp-agg  [$ST_TXT]"
    echo -e "Config  : ${CYAN}${HAPROXY_CFG}${NC}\n"
    show_haproxy_port_map
    echo ""

    echo -e "1) Restart"
    echo -e "2) Stop"
    echo -e "3) Start"
    echo -e "4) Status / Logs"
    echo -e "5) Edit config"
    echo -e "6) Validate config"
    echo -e "7) Show compact (baraye Kharej) + Iran IP"
    echo -e "8) Rebuild balancers (port → tunnels)"
    echo -e "9) Remove HAProxy service"
    echo -e "0) Back"
    read -p "Select: " ACT

    case $ACT in
        1) systemctl restart haproxy-frp-agg.service; echo -e "${GREEN}Restarted${NC}" ;;
        2) systemctl stop haproxy-frp-agg.service; echo -e "${YELLOW}Stopped${NC}" ;;
        3) systemctl start haproxy-frp-agg.service; echo -e "${GREEN}Started${NC}" ;;
        4)
            systemctl status haproxy-frp-agg.service --no-pager -l
            journalctl -u haproxy-frp-agg.service -n 40 --no-pager
            ;;
        5)
            $(get_editor) "$HAPROXY_CFG"
            if confirm_yn "Validate & reload?"; then
                if haproxy -c -f "$HAPROXY_CFG" >/dev/null 2>&1; then
                    systemctl reload haproxy-frp-agg.service 2>/dev/null || systemctl restart haproxy-frp-agg.service
                    echo -e "${GREEN}OK${NC}"
                else
                    haproxy -c -f "$HAPROXY_CFG"
                fi
            fi
            ;;
        6) haproxy -c -f "$HAPROXY_CFG" ;;
        7)
            LIVE_IP=$(curl -s --max-time 3 http://ip-api.com/line/?fields=query 2>/dev/null)
            [ -z "$LIVE_IP" ] && LIVE_IP=$(curl -s --max-time 3 https://ifconfig.me 2>/dev/null)
            for f in "$CONFIG_DIR"/aggregation_*_compact.txt; do
                [ -f "$f" ] || continue
                RF="${f/_compact.txt/_rules.conf}"
                FILE_IP=$(grep -E '^# IranIP=' "$f" 2>/dev/null | cut -d= -f2)
                [ -f "$RF" ] && FILE_IP=${FILE_IP:-$(grep -E '^IRAN_IP=' "$RF" 2>/dev/null | cut -d= -f2)}
                echo -e "${ORANGE}===== $f =====${NC}"
                echo -e "Iran IP (saved): ${GREEN}${FILE_IP:-?}${NC}"
                echo -e "Iran IP (live) : ${CYAN}${LIVE_IP:-?}${NC}\n"
                cat "$f"
                echo ""
            done
            ;;
        8)
            RULES_CANDIDATES=("$CONFIG_DIR"/aggregation_*_rules.conf)
            if [ ! -f "${RULES_CANDIDATES[0]}" ]; then
                echo -e "${RED}Rules file nist. Option 10 ra dobare bezan.${NC}"
                read -p "Enter..."; return
            fi
            echo -e "Rules files:"
            select RF in "${RULES_CANDIDATES[@]}" "Cancel"; do
                [ "$RF" == "Cancel" ] || [ -z "$RF" ] && return
                break
            done
            # shellcheck source=/dev/null
            source "$RF"
            ALL_TIDS_STR=""
            for ((i=0; i<NUM_TUNNELS; i++)); do
                eval "rp=\$T${i}_REMOTE"
                # rebuild from T*_REMOTE keys
                :
            done
            # Build list of tunnel IDs from Txx_REMOTE
            declare -a ALL_TIDS
            declare -a REMOTE_PORTS
            NUM_TUNNELS=0
            for key in $(compgen -A variable | grep -E '^T[0-9]+_REMOTE$' | sort -V); do
                tid=${key#T}; tid=${tid%_REMOTE}
                ALL_TIDS+=("$tid")
                eval "REMOTE_PORTS+=(\"\$$key\")"
                NUM_TUNNELS=$((NUM_TUNNELS + 1))
            done
            # fallback: sequential from BASE_ID if empty
            if [ "$NUM_TUNNELS" -eq 0 ]; then
                echo -e "${RED}Remote port map empty in rules file.${NC}"
                read -p "Enter..."; return
            fi
            ALL_TIDS_STR=$(IFS=,; echo "${ALL_TIDS[*]}")
            echo -e "Tunnels: ${ALL_TIDS_STR}"
            echo -e "Har port = yek balanser. Tunnel: ${GREEN}all${NC} ya Enter = hame. Port khali = payan.\n"
            declare -a NEW_PORTS NEW_TUNNELS
            NR=0
            while true; do
                NR=$((NR+1))
                read -p "Balancer #$NR public port (khali=payan): " PIN
                PIN=$(echo "$PIN" | xargs)
                [ -z "$PIN" ] && { NR=$((NR-1)); break; }
                read -p "Tunnels [all]: " TIN
                TIN=$(echo "$TIN" | xargs)
                if [ -z "$TIN" ] || [ "$TIN" = "all" ] || [ "$TIN" = "ALL" ]; then
                    TIN="$ALL_TIDS_STR"
                fi
                IFS=',' read -ra PARR <<< "$PIN"
                for p in "${PARR[@]}"; do
                    p=$(echo "$p" | xargs)
                    [[ "$p" =~ ^[0-9]+$ ]] || continue
                    NEW_PORTS+=("$p")
                    NEW_TUNNELS+=("$TIN")
                    echo -e "  + :${p} → [$TIN]"
                done
            done
            if [ ${#NEW_PORTS[@]} -eq 0 ]; then
                echo -e "${YELLOW}Cancelled${NC}"; read -p "Enter..."; return
            fi
            NR=${#NEW_PORTS[@]}
            HAPROXY_BODY=""
            for ((r=0; r<NR; r++)); do
                p="${NEW_PORTS[$r]}"
                TIDS_LIST="${NEW_TUNNELS[$r]}"
                SERVERS=""
                IFS=',' read -ra TARR <<< "$TIDS_LIST"
                for tid in "${TARR[@]}"; do
                    tid=$(echo "$tid" | xargs)
                    rport=""
                    for ((i=0; i<NUM_TUNNELS; i++)); do
                        if [ "${ALL_TIDS[$i]}" = "$tid" ]; then
                            rport="${REMOTE_PORTS[$i]}"
                            break
                        fi
                    done
                    [ -z "$rport" ] && continue
                    SERVERS="${SERVERS}    server t${tid} 127.0.0.1:${rport} check inter 3s fall 3 rise 2 weight 100\n"
                done
                HAPROXY_BODY="${HAPROXY_BODY}
frontend fe_p${p}
    bind *:${p}
    mode tcp
    default_backend be_p${p}

backend be_p${p}
    mode tcp
    balance roundrobin
    option tcp-check
$(echo -e "$SERVERS")
"
                allow_ufw_port "$p" "tcp"
            done
            cat << EOF > "$HAPROXY_CFG"
# FRP Multi-Tunnel HAProxy (rebuilt)
# Tuned for ~2GB RAM / 2 CPU

global
    log /dev/log local0 notice
    maxconn 100000
    tune.bufsize 32768
    tune.maxrewrite 1024
    nbthread 2
    cpu-map auto:1/1-2 0-1

defaults
    log     global
    mode    tcp
    option  tcplog
    option  dontlognull
    option  redispatch
    option  clitcpka
    option  srvtcpka
    timeout connect 5s
    timeout client  1h
    timeout server  1h
    timeout tunnel  1h
    timeout check   3s
    maxconn 50000
    retries 3

$(echo -e "$HAPROXY_BODY")
EOF
            {
                echo "BASE_ID=$BASE_ID"
                echo "NUM_TUNNELS=$NUM_TUNNELS"
                echo "IRAN_IP=${IRAN_IP:-}"
                echo "RULE_COUNT=$NR"
                for ((r=0; r<NR; r++)); do
                    echo "RULE_${r}_PORTS=${NEW_PORTS[$r]}"
                    echo "RULE_${r}_TUNNELS=${NEW_TUNNELS[$r]}"
                done
                for ((i=0; i<NUM_TUNNELS; i++)); do
                    echo "T${ALL_TIDS[$i]}_REMOTE=${REMOTE_PORTS[$i]}"
                    eval "echo T${ALL_TIDS[$i]}_IPERF=\$T${ALL_TIDS[$i]}_IPERF" 2>/dev/null || true
                done
            } > "$RF"
            if haproxy -c -f "$HAPROXY_CFG" >/dev/null 2>&1; then
                systemctl restart haproxy-frp-agg.service
                echo -e "${GREEN}Rebuild OK — $NR balanser${NC}"
            else
                echo -e "${RED}Invalid config${NC}"
                haproxy -c -f "$HAPROXY_CFG"
            fi
            ;;
        9)
            if confirm_yn "Remove HAProxy aggregation service?"; then
                systemctl disable --now haproxy-frp-agg.service 2>/dev/null
                rm -f /etc/systemd/system/haproxy-frp-agg.service
                systemctl daemon-reload
                echo -e "${GREEN}Removed (tunnel-ha pak nashodand)${NC}"
            fi
            ;;
        0) return ;;
        *) echo -e "${RED}Invalid${NC}" ;;
    esac
    read -p "Enter..."
}


# ========== Server Bandwidth Test (FR / NL / Irancell-oriented) ==========
run_bandwidth_test() {
    show_logo
    echo -e "${CYAN}--- Server Bandwidth Test ---${NC}"
    echo -e "${YELLOW}Tests download speed toward France, Netherlands and Iran-related endpoints.${NC}"
    echo -e "${YELLOW}No disk IO benchmark. Pure network.${NC}\n"

    # Helper: timed curl download
    # usage: bw_curl_test "Label" "URL" [bytes]
    bw_curl_test() {
        local label="$1"
        local url="$2"
        local size=${3:-50000000}   # default ~50MB
        echo -ne "  ${CYAN}${label}${NC} ... "
        local result
        result=$(curl -H 'Cache-Control: no-cache' -H 'Pragma: no-cache' \
            -o /dev/null -w '%{speed_download}' \
            --connect-timeout 8 --max-time 25 \
            -L -s -C - "${url}" 2>/dev/null || echo "0")
        # speed_download is bytes/sec
        if [ -z "$result" ] || [ "$result" = "0" ]; then
            echo -e "${RED}FAILED${NC}"
            return
        fi
        # convert to Mbps
        local mbps
        mbps=$(python3 -c "print(f'{float('$result')*8/1e6:.2f}')" 2>/dev/null || echo "?")
        echo -e "${GREEN}${mbps} Mbps${NC}"
    }

    echo -e "${ORANGE}[1/3] France${NC}"
    # OVH / Scaleway style public test files (common in FR)
    bw_curl_test "FR - OVH (Gravelines)" "https://proof.ovh.net/files/100Mb.dat"
    bw_curl_test "FR - Scaleway" "https://scaleway.com"  # may redirect; still measures

    echo -e "\n${ORANGE}[2/3] Netherlands${NC}"
    bw_curl_test "NL - Online.net/Scaleway NL" "https://mirror.nl.leaseweb.net/speedtest/100mb.bin"
    bw_curl_test "NL - Hetzner (nearby EU)" "https://speed.hetzner.de/100MB.bin"

    echo -e "\n${ORANGE}[3/3] Iran / Irancell oriented${NC}"
    # Public Iranian mirrors / CDNs that are often reachable
    bw_curl_test "IR - ArvanCloud test" "https://dl.arvancloud.ir/"
    bw_curl_test "IR - Download test (hostiran)" "https://download.iranhost.com/"

    echo -e "\n${YELLOW}Note: Results depend on current routing and peering.${NC}"
    echo -e "${YELLOW}For tunnel throughput use option 6 (iperf through tunnel) or aggregated iperf port.${NC}"
    read -p "Press Enter to return..."
}


# ========== Full Reset / Cleanup ==========
reset_all_frp() {
    show_logo
    echo -e "${LIGHT_RED}=== Reset / Cleanup ===${NC}\n"
    echo -e "${CYAN}1. Delete ALL FRP tunnels (configs + systemd services)${NC}"
    echo -e "${CYAN}2. Remove HAProxy aggregation only${NC}"
    echo -e "${LIGHT_RED}3. Full reset (all tunnels + HAProxy + aggregation files)${NC}"
    echo -e "${CYAN}0. Back${NC}"
    read -p "Select: " ACT

    case $ACT in
        1)
            echo -e "${LIGHT_RED}This will stop and delete ALL frps/frpc tunnel services and configs.${NC}"
            if ! confirm_yn "Delete ALL tunnels?"; then
                echo -e "${YELLOW}Cancelled.${NC}"; read -p "Press Enter..."; return
            fi
            for proto in tcp kcp quic ws; do
                for i in {1..10}; do
                    for role in frps frpc; do
                        svc="${role}_${proto}_tunnel${i}.service"
                        if [ -f "/etc/systemd/system/$svc" ] || systemctl list-unit-files 2>/dev/null | grep -q "^$svc"; then
                            systemctl disable --now "$svc" 2>/dev/null
                            rm -f "/etc/systemd/system/$svc"
                            echo -e "  removed service $svc"
                        fi
                        rm -f "$CONFIG_DIR/${role}_${proto}_tunnel${i}.toml"
                    done
                done
            done
            systemctl daemon-reload
            echo -e "${GREEN}All FRP tunnels deleted.${NC}"
            ;;
        2)
            echo -e "${YELLOW}Stopping and removing HAProxy aggregation service + config...${NC}"
            if ! confirm_yn "Remove HAProxy aggregation?"; then
                echo -e "${YELLOW}Cancelled.${NC}"; read -p "Press Enter..."; return
            fi
            systemctl disable --now haproxy-frp-agg.service 2>/dev/null
            rm -f /etc/systemd/system/haproxy-frp-agg.service
            rm -f "$HAPROXY_CFG"
            rm -f "$CONFIG_DIR"/aggregation_*_compact.txt
            rm -f "$CONFIG_DIR"/aggregation_*_rules.conf
            rm -f "$CONFIG_DIR"/aggregation_*.info
            systemctl daemon-reload
            echo -e "${GREEN}HAProxy aggregation removed.${NC}"
            ;;
        3)
            echo -e "${LIGHT_RED}FULL RESET: all tunnels + HAProxy + aggregation metadata.${NC}"
            echo -e "${YELLOW}FRP binary and defaults file are kept.${NC}"
            if ! confirm_yn "Really full reset?"; then
                echo -e "${YELLOW}Cancelled.${NC}"; read -p "Press Enter..."; return
            fi
            # tunnels
            for proto in tcp kcp quic ws; do
                for i in {1..10}; do
                    for role in frps frpc; do
                        svc="${role}_${proto}_tunnel${i}.service"
                        systemctl disable --now "$svc" 2>/dev/null
                        rm -f "/etc/systemd/system/$svc"
                        rm -f "$CONFIG_DIR/${role}_${proto}_tunnel${i}.toml"
                    done
                done
            done
            # haproxy agg
            systemctl disable --now haproxy-frp-agg.service 2>/dev/null
            rm -f /etc/systemd/system/haproxy-frp-agg.service
            rm -f "$HAPROXY_CFG"
            rm -f "$CONFIG_DIR"/aggregation_*_compact.txt
            rm -f "$CONFIG_DIR"/aggregation_*_rules.conf
            rm -f "$CONFIG_DIR"/aggregation_*.info
            # leftover logs optional
            systemctl daemon-reload
            echo -e "${GREEN}Full reset done. You can run option 10 again from scratch.${NC}"
            ;;
        0) return ;;
        *) echo -e "${RED}Invalid.${NC}" ;;
    esac
    read -p "Press Enter to return..."
}

main_menu() {
    detect_location
    load_defaults
    while true; do
        show_logo
        echo -e "$(M loc_status): ${YELLOW}[ ${SERVER_MODE} ]${NC}"
        echo -e "FRP Version: ${GREEN}v${FRP_VERSION}${NC} | Protocols: ${CYAN}TCP · KCP · QUIC · WS${NC}\n"
        
        list_tunnels

        echo -e "${CYAN}1. $(M menu_1) v${FRP_VERSION}${NC}"
        echo -e "${ORANGE}2. $(M menu_2)${NC}"
        echo -e "${YELLOW}3. $(M menu_3)${NC}"
        echo -e "${CYAN}4. $(M menu_4)${NC}"
        echo -e "${CYAN}5. $(M menu_5)${NC}"
        echo -e "${CYAN}6. $(M menu_6)${NC}"
        echo -e "${CYAN}7. $(M menu_7)${NC}"
        echo -e "${CYAN}8. $(M menu_8)${NC}"
        echo -e "${CYAN}9. $(M menu_9)${NC}"
        echo -e "${ORANGE_LIGHT}10. $(M menu_10)${NC}"
        echo -e "${CYAN}11. $(M menu_11)${NC}"
        echo -e "${CYAN}12. $(M menu_12)${NC}"
        echo -e "${LIGHT_RED}13. $(M menu_13)${NC}"
        echo -e "${CYAN}14. $(M menu_14)${NC}"
        echo -e "${LIGHT_RED}0. $(M menu_0)${NC}"
        echo "---------------------------------"
        read -p "$(M choose): " OPT

        case $OPT in
            1) install_dependencies_and_frp ;;
            2) setup_frps ;;
            3) setup_frpc ;;
            4) check_tunnel_health ;;
            5) manage_tunnels ;;
            6) run_speedtest ;;
            7) 
                if [ "$SERVER_MODE" == "IRAN" ]; then SERVER_MODE="KHAREJ"; else SERVER_MODE="IRAN"; fi
                ;;
            8) set_default_values ;;
            9) optimize_system ;;
            10) setup_aggregation ;;
            11) manage_haproxy ;;
            12) run_bandwidth_test ;;
            13) reset_all_frp ;;
            14) set_language ;;
            0) echo -e "${LIGHT_RED}$(M exiting)${NC}"; exit 0 ;;
            *) echo -e "${RED}$(M invalid)${NC}"; sleep 1 ;;
        esac
    done
}

main_menu
