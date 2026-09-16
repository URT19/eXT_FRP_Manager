#!/usr/bin/env bash
# =============================================================================
#  FRP Manager v3.0 — Smart Installer
#  Target : Ubuntu 22.04 / 24.04 (also Debian 12+)
#  Modes  : --cli | --tui | --full (default) | --uninstall | --upgrade
#  Notes  : No Persian text. Only English / Finglish.
# =============================================================================
set -euo pipefail

# -----------------------------------------------------------------------------
#  Global config
# -----------------------------------------------------------------------------
readonly APP_NAME="frp-manager"
readonly APP_VERSION="3.0.0"
readonly FRP_VERSION="0.71.0"
readonly APP_DIR="/opt/frp-manager"
readonly VENV_DIR="${APP_DIR}/venv"
readonly DATA_DIR="${APP_DIR}/data"
readonly BIN_LINK="/usr/local/bin/frp-manager"
readonly TUI_LINK="/usr/local/bin/frp-tui"
readonly CLI_LINK="/usr/local/bin/frp-cli"
readonly EXPORT_LINK="/usr/local/bin/frp-export"
readonly LOG_FILE="/var/log/frp-manager-install.log"
readonly MIN_PY="3.10"

# -----------------------------------------------------------------------------
#  Colors
# -----------------------------------------------------------------------------
readonly C_RESET=$'\033[0m'
readonly C_BOLD=$'\033[1m'
readonly C_DIM=$'\033[2m'
readonly C_RED=$'\033[0;31m'
readonly C_LRED=$'\033[1;31m'
readonly C_GREEN=$'\033[0;32m'
readonly C_YELLOW=$'\033[0;33m'
readonly C_BLUE=$'\033[0;34m'
readonly C_PURPLE=$'\033[0;35m'
readonly C_CYAN=$'\033[0;36m'
readonly C_ORANGE=$'\033[38;5;214m'
readonly C_GRAY=$'\033[38;5;244m'

# -----------------------------------------------------------------------------
#  Logging helpers
# -----------------------------------------------------------------------------
log()      { printf "%s[INFO]%s %s\n"     "${C_CYAN}"   "${C_RESET}" "$*" | tee -a "$LOG_FILE" >&2; }
ok()       { printf "%s[ OK ]%s %s\n"     "${C_GREEN}"  "${C_RESET}" "$*" | tee -a "$LOG_FILE" >&2; }
warn()     { printf "%s[WARN]%s %s\n"     "${C_YELLOW}" "${C_RESET}" "$*" | tee -a "$LOG_FILE" >&2; }
err()      { printf "%s[FAIL]%s %s\n"     "${C_LRED}"   "${C_RESET}" "$*" | tee -a "$LOG_FILE" >&2; }
step()     { printf "\n%s%s==>%s %s%s\n"  "${C_BOLD}" "${C_BLUE}" "${C_RESET}" "${C_BOLD}" "$*${C_RESET}" | tee -a "$LOG_FILE" >&2; }
substep()  { printf "   %s-%s %s\n"       "${C_GRAY}"   "${C_RESET}" "$*" | tee -a "$LOG_FILE" >&2; }
die()      { err "$*"; exit 1; }

# -----------------------------------------------------------------------------
#  Logo
# -----------------------------------------------------------------------------
show_logo() {
    printf "%s" "${C_CYAN}"
    cat <<'EOF'
   ______ _____  _____    __  __
  |  ____|  __ \|  __ \  |  \/  |   FRP Manager v3.0
  | |__  | |__) | |__) | | \  / |   Multi-Protocol Tunnel Manager
  |  __| |  _  /|  ___/  | |\/| |   with HAProxy Aggregation + TUI
  | |    | | \ \| |      | |  | |
  |_|    |_|  \_\_|      |_|  |_|
EOF
    printf "%s\n" "${C_RESET}"
}

# -----------------------------------------------------------------------------
#  Banner
# -----------------------------------------------------------------------------
banner() {
    local txt="$1"
    local pad=$(( 66 - ${#txt} ))
    [ "$pad" -lt 0 ] && pad=0
    printf "\n%s%s╔══════════════════════════════════════════════════════════════════╗%s\n" "${C_BOLD}" "${C_BLUE}" "${C_RESET}"
    printf "%s%s║ %s%*s ║%s\n" "${C_BOLD}" "${C_BLUE}" "${C_CYAN}${txt}" "${pad}" "" "${C_RESET}"
    printf "%s%s╚══════════════════════════════════════════════════════════════════╝%s\n" "${C_BOLD}" "${C_BLUE}" "${C_RESET}"
}

# -----------------------------------------------------------------------------
#  Must be root
# -----------------------------------------------------------------------------
require_root() {
    if [ "${EUID}" -ne 0 ]; then
        die "This script must be run as root. Try: sudo bash $0 $*"
    fi
}

# -----------------------------------------------------------------------------
#  Detect OS + version
# -----------------------------------------------------------------------------
detect_os() {
    if [ ! -f /etc/os-release ]; then
        die "Cannot detect OS: /etc/os-release is missing."
    fi
    # shellcheck disable=SC1091
    . /etc/os-release
    OS_ID="${ID:-unknown}"
    OS_VER="${VERSION_ID:-unknown}"
    OS_NAME="${PRETTY_NAME:-$OS_ID $OS_VER}"

    log "Detected OS: ${C_BOLD}${OS_NAME}${C_RESET}"

    case "$OS_ID" in
        ubuntu)
            if [[ "${OS_VER}" != "22.04" && "${OS_VER}" != "24.04" \
                  && "${OS_VER}" != "24.10" && "${OS_VER}" != "25.04" ]]; then
                warn "Ubuntu ${OS_VER} is not officially tested. Proceeding anyway..."
            fi
            ;;
        debian)
            log "Debian ${OS_VER} detected - supported mode."
            ;;
        *)
            warn "OS '${OS_ID}' is not Debian/Ubuntu. Some steps may fail."
            ;;
    esac
}

# -----------------------------------------------------------------------------
#  Package manager
# -----------------------------------------------------------------------------
PKG_MGR=""
detect_pkg_mgr() {
    if command -v apt-get >/dev/null 2>&1; then
        PKG_MGR="apt"
    else
        die "No supported package manager (apt) found."
    fi
    log "Package manager: ${C_BOLD}${PKG_MGR}${C_RESET}"
}

apt_quiet() {
    DEBIAN_FRONTEND=noninteractive apt-get -y -qq \
        -o Dpkg::Options::=--force-confdef \
        -o Dpkg::Options::=--force-confold "$@" >>"$LOG_FILE" 2>&1
}

# -----------------------------------------------------------------------------
#  Detect source directory
# -----------------------------------------------------------------------------
SRC_DIR=""
detect_src_dir() {
    local here
    here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -d "${here}/frp_manager" ] && [ -f "${here}/pyproject.toml" ]; then
        SRC_DIR="$here"
    elif [ -d "${here}/../frp_manager" ]; then
        SRC_DIR="$(cd "${here}/.." && pwd)"
    else
        die "Cannot find 'frp_manager/' next to this script. Run install.sh from the project root."
    fi
    ok "Source directory: ${C_CYAN}${SRC_DIR}${C_RESET}"
}

# -----------------------------------------------------------------------------
#  Python version check
# -----------------------------------------------------------------------------
PYTHON_BIN=""
check_python() {
    for cand in python3.12 python3.11 python3.10 python3; do
        if command -v "$cand" >/dev/null 2>&1; then
            local v
            v=$("$cand" -c 'import sys;print("%d.%d"%sys.version_info[:2])')
            if printf '%s\n%s\n' "$MIN_PY" "$v" | sort -V -C; then
                PYTHON_BIN="$(command -v "$cand")"
                ok "Python ${v} found at ${C_CYAN}${PYTHON_BIN}${C_RESET}"
                return 0
            fi
        fi
    done
    die "Python >= ${MIN_PY} is required but not found."
}

# -----------------------------------------------------------------------------
#  Parse arguments
# -----------------------------------------------------------------------------
INSTALL_DEPS=true
INSTALL_HAPROXY=true
MODE="full"
ACTION="install"

parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --cli)        MODE="cli" ;;
            --tui)        MODE="tui" ;;
            --full)       MODE="full" ;;
            --no-deps)    INSTALL_DEPS=false ;;
            --no-haproxy) INSTALL_HAPROXY=false ;;
            --uninstall)  ACTION="uninstall" ;;
            --upgrade)    ACTION="upgrade" ;;
            -h|--help)
                cat <<EOF
FRP Manager v${APP_VERSION} Installer

Usage: sudo bash install.sh [OPTIONS]

Options:
  --full         Install everything: FRP, HAProxy, Python package (default)
  --cli          Install and only enable the classic CLI entry
  --tui          Install and only enable the Textual TUI entry
  --no-deps      Skip system dependency installation
  --no-haproxy   Skip HAProxy installation
  --upgrade      Reinstall / upgrade the Python package only
  --uninstall    Remove FRP Manager (keeps data unless confirmed)
  -h, --help     Show this help
EOF
                exit 0
                ;;
            *) die "Unknown option: $1 (try --help)" ;;
        esac
        shift
    done
}

# -----------------------------------------------------------------------------
#  APT dependencies
# -----------------------------------------------------------------------------
APT_PACKAGES=(
    python3 python3-venv python3-pip python3-full
    curl wget tar unzip zip
    iperf3
    ufw
    bc
    cron
    netcat-openbsd
    psmisc
    nano
    rsync
    ca-certificates
    gnupg
    lsb-release
)

install_deps() {
    step "[1/8] Installing system dependencies"

    substep "apt-get update"
    apt_quiet update || warn "apt-get update reported warnings (continuing)."

    substep "Installing ${#APT_PACKAGES[@]} packages"
    if apt_quiet install "${APT_PACKAGES[@]}"; then
        ok "System dependencies installed."
    else
        warn "One or more optional packages failed. Core functionality will still work."
    fi
}

# -----------------------------------------------------------------------------
#  HAProxy
# -----------------------------------------------------------------------------
install_haproxy() {
    if [ "$INSTALL_HAPROXY" != true ]; then
        warn "Skipping HAProxy install (--no-haproxy)."
        return
    fi
    step "[2/8] Installing HAProxy"

    if command -v haproxy >/dev/null 2>&1; then
        local v
        v=$(haproxy -v 2>/dev/null | head -1)
        ok "HAProxy already present: ${C_CYAN}${v}${C_RESET}"
    else
        if apt_quiet install haproxy; then
            ok "HAProxy installed."
        else
            warn "HAProxy install failed. You can still use FRP tunnels without aggregation."
            INSTALL_HAPROXY=false
        fi
    fi

    if [ -d /etc/systemd/system ]; then
        ok "systemd detected."
    else
        warn "systemd not found - services will not auto-start."
    fi
}

# -----------------------------------------------------------------------------
#  Copy sources to /opt/frp-manager
# -----------------------------------------------------------------------------
copy_sources() {
    step "[3/8] Installing sources to ${APP_DIR}"

    mkdir -p "$APP_DIR" "$DATA_DIR" "${DATA_DIR}/configs" \
             "${DATA_DIR}/logs" "${DATA_DIR}/backups" \
             "${DATA_DIR}/exports" "${DATA_DIR}/haproxy"

    # Preserve existing data dir across upgrades
    local tmp_data=""
    if [ -d "${APP_DIR}/data" ] && [ -f "${APP_DIR}/data/state.json" ]; then
        tmp_data="$(mktemp -d)"
        cp -a "${APP_DIR}/data/." "$tmp_data/" 2>/dev/null || true
        substep "Backed up existing data/ before upgrade"
    fi

    if command -v rsync >/dev/null 2>&1; then
        rsync -a --delete \
            --exclude 'venv' \
            --exclude '.git' \
            --exclude '__pycache__' \
            --exclude '.pytest_cache' \
            --exclude 'data' \
            "${SRC_DIR}/frp_manager" "${APP_DIR}/" >>"$LOG_FILE" 2>&1

        [ -f "${SRC_DIR}/pyproject.toml" ] && \
            cp -f "${SRC_DIR}/pyproject.toml" "${APP_DIR}/" >>"$LOG_FILE" 2>&1

        [ -f "${SRC_DIR}/README.md" ] && \
            cp -f "${SRC_DIR}/README.md" "${APP_DIR}/" >>"$LOG_FILE" 2>&1

        [ -d "${SRC_DIR}/tests" ] && \
            rsync -a --delete "${SRC_DIR}/tests" "${APP_DIR}/" >>"$LOG_FILE" 2>&1
    else
        rm -rf "${APP_DIR}/frp_manager"
        cp -r "${SRC_DIR}/frp_manager" "${APP_DIR}/"
        [ -f "${SRC_DIR}/pyproject.toml" ] && cp -f "${SRC_DIR}/pyproject.toml" "${APP_DIR}/"
        [ -f "${SRC_DIR}/README.md" ] && cp -f "${SRC_DIR}/README.md" "${APP_DIR}/"
        [ -d "${SRC_DIR}/tests" ] && cp -r "${SRC_DIR}/tests" "${APP_DIR}/"
    fi

    if [ -n "$tmp_data" ]; then
        cp -a "$tmp_data/." "${APP_DIR}/data/"
        rm -rf "$tmp_data"
        substep "Restored previous data/"
    fi

    ok "Sources installed."
}

# -----------------------------------------------------------------------------
#  Python venv + package install
# -----------------------------------------------------------------------------
setup_venv() {
    step "[4/8] Setting up Python environment"

    if [ -d "$VENV_DIR" ]; then
        substep "Existing venv found - reusing."
    else
        substep "Creating venv at ${VENV_DIR}"
        "$PYTHON_BIN" -m venv "$VENV_DIR" || die "Failed to create venv."
    fi

    substep "Upgrading pip / wheel / setuptools"
    "${VENV_DIR}/bin/pip" install --quiet --upgrade \
        pip wheel setuptools >>"$LOG_FILE" 2>&1

    substep "Installing ${APP_NAME} package"
    if "${VENV_DIR}/bin/pip" install --quiet -e "${APP_DIR}" >>"$LOG_FILE" 2>&1; then
        ok "Python package installed."
    else
        err "pip install failed. Check ${LOG_FILE} for details."
        tail -n 30 "$LOG_FILE" >&2
        exit 1
    fi
}

# -----------------------------------------------------------------------------
#  Install FRP binary
# -----------------------------------------------------------------------------
install_frp_binary() {
    step "[5/8] Installing FRP v${FRP_VERSION} binary"

    if [ -x /usr/local/bin/frps ] && [ -x /usr/local/bin/frpc ]; then
        local v
        v=$(/usr/local/bin/frps --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "")
        if [ "$v" = "$FRP_VERSION" ]; then
            ok "FRP v${v} already installed."
            return
        fi
        substep "Different version detected (v${v:-unknown}) — re-downloading."
    fi

    local arch
    arch=$(uname -m)
    case "$arch" in
        x86_64)  FRP_ARCH="amd64" ;;
        aarch64) FRP_ARCH="arm64" ;;
        armv7l)  FRP_ARCH="arm" ;;
        *) die "Unsupported architecture: $arch" ;;
    esac

    local url="https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_linux_${FRP_ARCH}.tar.gz"
    local tmp
    tmp="$(mktemp -d)"

    substep "Downloading from GitHub"
    if ! wget -q --show-progress -O "${tmp}/frp.tar.gz" "$url" 2>>"$LOG_FILE"; then
        warn "Failed to download FRP. You can install it later from CLI menu [1]."
        rm -rf "$tmp"
        return
    fi

    substep "Extracting"
    tar -xzf "${tmp}/frp.tar.gz" -C "$tmp" >>"$LOG_FILE" 2>&1
    local src_dir="${tmp}/frp_${FRP_VERSION}_linux_${FRP_ARCH}"

    if [ -f "${src_dir}/frps" ] && [ -f "${src_dir}/frpc" ]; then
        install -m 0755 "${src_dir}/frps" /usr/local/bin/frps
        install -m 0755 "${src_dir}/frpc" /usr/local/bin/frpc
        ok "FRP binaries installed at /usr/local/bin/frps and /usr/local/bin/frpc"
    else
        warn "Extracted archive missing binaries."
    fi

    rm -rf "$tmp"
}

# -----------------------------------------------------------------------------
#  Create CLI entrypoints
# -----------------------------------------------------------------------------
create_entrypoints() {
    step "[6/8] Creating command-line entrypoints"

    # Main launcher
    cat > "$BIN_LINK" <<EOF
#!/usr/bin/env bash
# FRP Manager launcher - generated by install.sh
cd / || exit 1
exec "${VENV_DIR}/bin/python" -m frp_manager "\$@"
EOF
    chmod +x "$BIN_LINK"
    ok "Created ${C_CYAN}${BIN_LINK}${C_RESET}"

    # TUI shortcut
    cat > "$TUI_LINK" <<EOF
#!/usr/bin/env bash
cd / || exit 1
exec "${VENV_DIR}/bin/python" -m frp_manager --tui "\$@"
EOF
    chmod +x "$TUI_LINK"
    ok "Created ${C_CYAN}${TUI_LINK}${C_RESET}"

    # CLI shortcut
    cat > "$CLI_LINK" <<EOF
#!/usr/bin/env bash
cd / || exit 1
exec "${VENV_DIR}/bin/python" -m frp_manager --cli "\$@"
EOF
    chmod +x "$CLI_LINK"
    ok "Created ${C_CYAN}${CLI_LINK}${C_RESET}"

    if ! printf '%s' "$PATH" | tr ':' '\n' | grep -q "^/usr/local/bin$"; then
        warn "/usr/local/bin is not in your PATH. Add it to use the shortcuts."
    fi
}

# -----------------------------------------------------------------------------
#  Install frp-export helper
# -----------------------------------------------------------------------------
install_frp_export() {
    step "[7/8] Installing frp-export helper (clean project exporter)"

    cat > "$EXPORT_LINK" <<'FRPEXPORT_EOF'
#!/usr/bin/env bash
# =============================================================================
#  FRP Manager - Clean Project Export
#  Creates a ZIP with ONLY source code. No data, no secrets, no logs.
# =============================================================================
set -euo pipefail

PROJECT_SRC="${1:-/opt/frp-manager}"
OUTPUT_DIR="${2:-/root}"
TS=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="frp-manager-clean-${TS}.zip"
TMP=$(mktemp -d)
STAGE="${TMP}/frp-manager"

C_RESET=$'\033[0m'
C_GREEN=$'\033[0;32m'
C_YELLOW=$'\033[0;33m'
C_RED=$'\033[0;31m'
C_CYAN=$'\033[0;36m'

echo "🔧 [1/5] Preparing staging directory..."
mkdir -p "$STAGE"

if [ ! -d "$PROJECT_SRC/frp_manager" ]; then
    echo "${C_RED}❌ frp_manager/ not found in $PROJECT_SRC${C_RESET}"
    exit 1
fi

echo "🔧 [2/5] Copying source code (excluding secrets)..."

if command -v rsync >/dev/null 2>&1; then
    rsync -a \
        --exclude 'data/' \
        --exclude 'venv/' \
        --exclude '.venv/' \
        --exclude '__pycache__/' \
        --exclude '*.pyc' \
        --exclude '*.pyo' \
        --exclude '.pytest_cache/' \
        --exclude '.mypy_cache/' \
        --exclude '.ruff_cache/' \
        --exclude '.git/' \
        --exclude '.gitignore' \
        --exclude '*.log' \
        --exclude '*.bak' \
        --exclude '*.old' \
        --exclude '*.backup' \
        --exclude '*.zip' \
        --exclude '*.tar.gz' \
        --exclude '*.egg-info/' \
        --exclude 'build/' \
        --exclude 'dist/' \
        --exclude 'node_modules/' \
        --exclude '.env' \
        --exclude '.env.*' \
        --exclude 'state.json*' \
        --exclude 'defaults.toml' \
        --exclude '*_compact.txt' \
        --exclude 'haproxy-agg.cfg' \
        --exclude '_archived_*' \
        --exclude 'cli.py.v2.bak' \
        --exclude 'tables.py.v2.bak' \
        --exclude '*.tcss' \
        "$PROJECT_SRC/frp_manager" "$STAGE/" 2>/dev/null
else
    cp -r "$PROJECT_SRC/frp_manager" "$STAGE/"
    find "$STAGE" -type d \( \
        -name 'data' -o -name 'venv' -o -name '.venv' \
        -o -name '__pycache__' -o -name '.pytest_cache' \
        -o -name '.mypy_cache' -o -name '.git' \
    \) -exec rm -rf {} + 2>/dev/null || true
    find "$STAGE" -type f \( \
        -name '*.pyc' -o -name '*.pyo' -o -name '*.log' \
        -o -name '*.bak' -o -name '*.old' -o -name 'state.json*' \
        -o -name 'defaults.toml' -o -name '*_compact.txt' \
        -o -name '*.env' \
    \) -delete 2>/dev/null || true
fi

for f in pyproject.toml README.md install.sh bootstrap.sh; do
    if [ -f "$PROJECT_SRC/$f" ]; then
        cp "$PROJECT_SRC/$f" "$STAGE/"
    fi
done

if [ -d "$PROJECT_SRC/tests" ]; then
    cp -r "$PROJECT_SRC/tests" "$STAGE/"
fi

echo "🔧 [3/5] Scanning for sensitive data..."

SENSITIVE_PATTERNS=(
    '[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}'
    'token\s*=\s*"[A-Za-z0-9]\{12,\}"'
    'auth\.token\s*=\s*"[^"]\{12,\}"'
)

FOUND_ISSUES=0
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    MATCHES=$(grep -rEn "$pattern" "$STAGE" 2>/dev/null \
        | grep -v "127.0.0.1" \
        | grep -v "0.0.0.0" \
        | grep -v "255.255" \
        | grep -v "example" \
        | grep -v "# " \
        || true)
    if [ -n "$MATCHES" ]; then
        echo "${C_YELLOW}⚠  Potential sensitive pattern: $pattern${C_RESET}"
        echo "$MATCHES" | head -5
        FOUND_ISSUES=$((FOUND_ISSUES + 1))
    fi
done

if [ "$FOUND_ISSUES" -gt 0 ]; then
    echo ""
    echo "${C_YELLOW}⚠  Found $FOUND_ISSUES suspicious pattern(s).${C_RESET}"
    read -p "Continue creating ZIP? [y/N] " ans
    ans=${ans:-N}
    case "$ans" in
        [Yy]|[Yy][Ee][Ss]) ;;
        *) echo "Cancelled."; rm -rf "$TMP"; exit 1 ;;
    esac
fi

cat > "$STAGE/EXPORT_MANIFEST.txt" <<EOF
FRP Manager - Clean Source Export
==================================

Exported  : $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Package   : frp-manager

Contents
--------
This archive contains ONLY source code.

EXCLUDED:
  - data/state.json         (server config, IPs, tokens)
  - data/configs/*.toml     (frps/frpc configs with tokens)
  - data/haproxy/*.cfg      (HAProxy config)
  - data/exports/*.txt      (compact files with tokens)
  - data/defaults.toml      (user preferences)
  - data/backups/*          (backups)
  - data/logs/*             (runtime logs)
  - venv/                   (virtual environment)
  - __pycache__/ *.pyc      (bytecode)
  - *.bak *.old             (file backups)
  - .git/                   (version history)

Installation on new server
--------------------------
  unzip frp-manager-clean-*.zip
  cd frp-manager
  sudo bash install.sh
  sudo frp-cli
EOF

echo "🔧 [4/5] Creating ZIP archive..."
cd "$TMP"
if command -v zip >/dev/null 2>&1; then
    zip -rq "${OUTPUT_DIR}/${ARCHIVE_NAME}" frp-manager
else
    ARCHIVE_NAME="${ARCHIVE_NAME%.zip}.tar.gz"
    tar -czf "${OUTPUT_DIR}/${ARCHIVE_NAME}" frp-manager
fi
cd - >/dev/null

echo "🔧 [5/5] Verifying archive..."
if [ -f "${OUTPUT_DIR}/${ARCHIVE_NAME}" ]; then
    SIZE=$(du -h "${OUTPUT_DIR}/${ARCHIVE_NAME}" | cut -f1)
    echo ""
    echo "${C_GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"
    echo "${C_GREEN}✅ Export complete!${C_RESET}"
    echo ""
    echo "  ${C_CYAN}File :${C_RESET} ${OUTPUT_DIR}/${ARCHIVE_NAME}"
    echo "  ${C_CYAN}Size :${C_RESET} ${SIZE}"
    echo ""
    echo "  ${C_GREEN}→ Copy to a new server:${C_RESET}"
    echo "    scp ${OUTPUT_DIR}/${ARCHIVE_NAME} user@newserver:/root/"
    echo ""
    echo "  ${C_GREEN}→ On the new server:${C_RESET}"
    echo "    unzip ${ARCHIVE_NAME}"
    echo "    cd frp-manager"
    echo "    sudo bash install.sh"
    echo "${C_GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"
    echo ""
else
    echo "${C_RED}❌ Archive creation failed.${C_RESET}"
    rm -rf "$TMP"
    exit 1
fi

rm -rf "$TMP"
FRPEXPORT_EOF

    chmod +x "$EXPORT_LINK"
    ok "Created ${C_CYAN}${EXPORT_LINK}${C_RESET}"
    substep "Usage: sudo frp-export"
    substep "       sudo frp-export /path/to/src /path/to/output"
}

# -----------------------------------------------------------------------------
#  Smoke test
# -----------------------------------------------------------------------------
smoke_test() {
    step "[8/8] Verifying installation"

    local ver
    if ver=$("${VENV_DIR}/bin/python" -m frp_manager --help 2>&1 | head -1); then
        ok "frp_manager module loads: ${C_CYAN}${ver}${C_RESET}"
    else
        err "Python module failed to load. Check ${LOG_FILE}"
        exit 1
    fi

    if [ -x /usr/local/bin/frps ] && [ -x /usr/local/bin/frpc ]; then
        local frpver
        frpver=$(/usr/local/bin/frps --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "?")
        ok "FRP binaries present (v${frpver})."
    else
        warn "FRP binaries not found — install later via CLI menu [1]."
    fi

    if [ "$INSTALL_HAPROXY" = true ] && command -v haproxy >/dev/null 2>&1; then
        ok "HAProxy binary is reachable."
    fi

    if command -v iperf3 >/dev/null 2>&1; then
        ok "iperf3 available for speed tests."
    fi

    if [ -x "$EXPORT_LINK" ]; then
        ok "frp-export helper installed."
    fi

    if command -v ufw >/dev/null 2>&1; then
        local ufw_state
        ufw_state=$(ufw status 2>/dev/null | head -1 | awk '{print $2}')
        if [ "$ufw_state" = "active" ]; then
            ok "UFW is active - ports will be auto-whitelisted."
        else
            substep "UFW is inactive (or not configured)."
        fi
    fi
}

# -----------------------------------------------------------------------------
#  Success summary
# -----------------------------------------------------------------------------
print_summary() {
    local ip=""
    ip=$(curl -4 -s --max-time 3 https://myip.wtf 2>/dev/null \
        | tr -d '[:space:]' || true)
    if [ -z "$ip" ] || ! [[ "$ip" =~ ^[0-9.]+$ ]]; then
        ip=$(curl -4 -s --max-time 3 https://api.ipify.org 2>/dev/null \
            | tr -d '[:space:]' || true)
    fi
    [ -z "$ip" ] && ip="(unknown)"

    banner "INSTALLATION COMPLETE"

    printf "\n"
    printf "  %sVersion%s        : %s%s%s\n"   "$C_BOLD" "$C_RESET" "$C_GREEN"  "$APP_VERSION" "$C_RESET"
    printf "  %sInstall dir%s  : %s%s%s\n"     "$C_BOLD" "$C_RESET" "$C_CYAN"   "$APP_DIR"     "$C_RESET"
    printf "  %sData dir%s     : %s%s%s\n"     "$C_BOLD" "$C_RESET" "$C_CYAN"   "$DATA_DIR"    "$C_RESET"
    printf "  %sLog file%s     : %s%s%s\n"     "$C_BOLD" "$C_RESET" "$C_GRAY"   "$LOG_FILE"    "$C_RESET"
    printf "  %sServer IP%s    : %s%s%s\n"     "$C_BOLD" "$C_RESET" "$C_YELLOW" "$ip"          "$C_RESET"
    printf "\n"

    printf "  %sAvailable commands:%s\n" "$C_BOLD" "$C_RESET"
    printf "    %s%-16s%s  Smart launcher (asks CLI vs TUI)\n" "$C_GREEN" "frp-manager"     "$C_RESET"
    printf "    %s%-16s%s  Classic CLI menu\n"                 "$C_GREEN" "frp-cli"         "$C_RESET"
    printf "    %s%-16s%s  Textual TUI (experimental)\n"       "$C_GREEN" "frp-tui"         "$C_RESET"
    printf "    %s%-16s%s  Clean project exporter\n"           "$C_GREEN" "frp-export"      "$C_RESET"
    printf "\n"

    printf "  %sQuick start:%s\n" "$C_BOLD" "$C_RESET"
    printf "    1) %ssudo frp-manager%s\n" "$C_YELLOW" "$C_RESET"
    printf "    2) Menu [1] to install/update FRP binary\n"
    printf "    3) Menu [2] to add nodes (Kharej servers)\n"
    printf "    4) Menu [3] Simple Route  OR  Menu [4] Balanced Route\n"
    printf "    5) Menu [6] to export config for a node\n"
    printf "\n"

    printf "  %sTip:%s Data, configs, and HAProxy cfg live in %s\n" "$C_BOLD" "$C_RESET" "$DATA_DIR"
    printf "  %sTip:%s Use %sfrp-export%s to package the project for another server.\n" "$C_BOLD" "$C_RESET" "$C_YELLOW" "$C_RESET"
    printf "\n"
}

# -----------------------------------------------------------------------------
#  Upgrade path
# -----------------------------------------------------------------------------
do_upgrade() {
    banner "UPGRADE MODE"
    detect_src_dir
    check_python
    copy_sources
    setup_venv
    create_entrypoints
    install_frp_export
    smoke_test
    print_summary
}

# -----------------------------------------------------------------------------
#  Uninstall
# -----------------------------------------------------------------------------
do_uninstall() {
    banner "UNINSTALL MODE"

    warn "This will remove:"
    substep "${APP_DIR}"
    substep "${BIN_LINK}, ${TUI_LINK}, ${CLI_LINK}, ${EXPORT_LINK}"
    substep "systemd units: frps@.service, frpc@.service, haproxy-frp-agg.service"
    printf "\n"

    read -rp "Remove everything including data/? [y/N] " ans
    ans="${ans:-N}"
    case "$ans" in
        [Yy]|[Yy][Ee][Ss])
            step "Stopping services"
            for unit in frps@.service frpc@.service haproxy-frp-agg.service; do
                if systemctl list-unit-files 2>/dev/null | grep -q "^${unit}"; then
                    systemctl disable --now "$unit" >>"$LOG_FILE" 2>&1 || true
                    substep "stopped ${unit}"
                fi
            done

            systemctl list-units --all --no-legend 'frps@*.service' 2>/dev/null \
                | awk '{print $1}' | while read -r u; do
                    [ -n "$u" ] && systemctl disable --now "$u" >>"$LOG_FILE" 2>&1 || true
                  done
            systemctl list-units --all --no-legend 'frpc@*.service' 2>/dev/null \
                | awk '{print $1}' | while read -r u; do
                    [ -n "$u" ] && systemctl disable --now "$u" >>"$LOG_FILE" 2>&1 || true
                  done

            step "Removing systemd units"
            rm -f /etc/systemd/system/frps@.service
            rm -f /etc/systemd/system/frpc@.service
            rm -f /etc/systemd/system/haproxy-frp-agg.service
            systemctl daemon-reload || true

            step "Removing binaries and data"
            rm -f "$BIN_LINK" "$TUI_LINK" "$CLI_LINK" "$EXPORT_LINK"
            rm -rf "$APP_DIR"

            ok "Uninstall complete."
            ;;
        *)
            warn "Cancelled. Nothing was removed."
            ;;
    esac
}

# -----------------------------------------------------------------------------
#  Error handler
# -----------------------------------------------------------------------------
on_error() {
    local code=$?
    err "Installer failed at line $1 (exit=$code)."
    err "Full log: ${LOG_FILE}"
    exit "$code"
}

# -----------------------------------------------------------------------------
#  Main
# -----------------------------------------------------------------------------
main() {
    : >"$LOG_FILE" 2>/dev/null || true

    show_logo
    printf "%s  Target: Ubuntu 22.04 / 24.04 (also Debian 12+)%s\n" "$C_DIM" "$C_RESET"
    printf "%s  Log   : %s%s\n\n" "$C_DIM" "$LOG_FILE" "$C_RESET"

    parse_args "$@"
    require_root "$@"
    detect_os
    detect_pkg_mgr

    case "$ACTION" in
        uninstall) do_uninstall; exit 0 ;;
        upgrade)   do_upgrade;   exit 0 ;;
    esac

    detect_src_dir
    check_python

    [ "$INSTALL_DEPS" = true ] && install_deps || warn "Skipping system dependencies."
    install_haproxy
    copy_sources
    setup_venv
    install_frp_binary
    create_entrypoints
    install_frp_export
    smoke_test
    print_summary
}

trap 'on_error $LINENO' ERR
main "$@"
