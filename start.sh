#!/usr/bin/env bash
# ============================================================
#  Sigmoidian Discord Bot — Mac / Linux startup script
#  Usage:
#    ./start.sh          (reads PORT from .env, default 8080)
#    PORT=9090 ./start.sh
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Colours ──────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log()  { echo -e "${CYAN}[sigmoidian]${RESET} $*"; }
ok()   { echo -e "${GREEN}[sigmoidian] ✅${RESET} $*"; }
warn() { echo -e "${YELLOW}[sigmoidian] ⚠️ ${RESET} $*"; }
err()  { echo -e "${RED}[sigmoidian] ❌${RESET} $*"; }

echo -e "${BOLD}"
echo "  ╔══════════════════════════════════╗"
echo "  ║   🎮  Sigmoidian Discord Bot     ║"
echo "  ╚══════════════════════════════════╝"
echo -e "${RESET}"

# ── Read PORT from .env (env var takes precedence) ───────────
if [ -f ".env" ]; then
    file_port=$(grep -E "^PORT\s*=" .env 2>/dev/null | head -1 | cut -d'=' -f2- | tr -d ' "'"'" || true)
    [ -n "$file_port" ] && PORT="${PORT:-$file_port}"
fi
PORT="${PORT:-8080}"

log "Port    : ${BOLD}$PORT${RESET}"
log "Python  : $(python3 --version 2>&1)"
echo ""

# ── Check / free the port ────────────────────────────────────
log "Checking port $PORT..."

free_port() {
    local pids
    # lsof is available on macOS; fall back to ss/fuser on Linux
    if command -v lsof &>/dev/null; then
        pids=$(lsof -ti tcp:"$PORT" 2>/dev/null || true)
    elif command -v ss &>/dev/null; then
        pids=$(ss -lptn "sport = :$PORT" 2>/dev/null \
               | grep -oP 'pid=\K[0-9]+' || true)
    elif command -v fuser &>/dev/null; then
        pids=$(fuser "${PORT}/tcp" 2>/dev/null || true)
    fi

    if [ -n "$pids" ]; then
        warn "Port $PORT is in use by PID(s): $pids — killing..."
        # shellcheck disable=SC2086
        kill -9 $pids 2>/dev/null || true
        sleep 1
        ok "Port $PORT freed."
    else
        ok "Port $PORT is free."
    fi
}

free_port

# ── Virtual environment ──────────────────────────────────────
echo ""
if [ ! -d "venv" ]; then
    log "Creating virtual environment..."
    python3 -m venv venv
    ok "venv created."
fi

log "Activating venv..."
# shellcheck source=/dev/null
source venv/bin/activate
ok "venv active  →  $(python --version)"

# ── Install / sync requirements ──────────────────────────────
echo ""
log "Checking requirements..."
pip install -r requirements.txt -q --disable-pip-version-check
ok "Dependencies up to date."

# ── Token check (non-fatal warning) ─────────────────────────
echo ""
token_val=""
if [ -f ".env" ]; then
    token_val=$(grep -E "^DISCORD_TOKEN\s*=" .env 2>/dev/null | head -1 \
                | cut -d'=' -f2- | tr -d ' "'"'" || true)
fi

if [ -z "$token_val" ] || [ "$token_val" = "your_bot_token_here" ]; then
    warn "DISCORD_TOKEN is not set in .env"
    warn "Bot will start in local-only mode."
    warn "Open http://localhost:${PORT}/ for setup instructions."
else
    ok "Discord token found."
fi

# ── Launch ───────────────────────────────────────────────────
echo ""
log "Starting bot  →  http://localhost:${PORT}/"
log "Press Ctrl+C to stop."
echo ""

exec python bot.py
