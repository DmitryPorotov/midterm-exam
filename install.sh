#!/usr/bin/env bash
# Author: Dmitry Porotov
set -euo pipefail

# ---------------------------------------------------------------------------
# install.sh — full installation for status-dashboard on a fresh VM
# Usage: sudo ./install.sh
# ---------------------------------------------------------------------------

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Colors -----------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}→${NC} $*"; }
warn()    { echo -e "${YELLOW}⚠${NC}  $*"; }
die()     { echo -e "${RED}✗${NC}  $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Must run as root
# ---------------------------------------------------------------------------
if [[ "$EUID" -ne 0 ]]; then
    die "This script must be run as root. Try: sudo ./install.sh"
fi

# ---------------------------------------------------------------------------
# Load environment variables
# Priority: shell env > .env file > defaults
# ---------------------------------------------------------------------------
ENV_FILE="$REPO_DIR/.env"

while read -r line || [[ -n "$line" ]]; do
    # Skip comments and empty lines
    if [[ ! "$line" =~ ^# && "$line" =~ = ]]; then
        # Extract variable name (part before the first '=')
        var_name="${line%%=*}"
        
        # Only export if the variable is NOT already set in the shell
        if [[ -z "${!var_name:-}" ]]; then
        export "$line"
        fi
    fi
done < "$ENV_FILE"

PORT="${PORT:-5000}"
VERSION="${VERSION:-1.0.0}"

if [[ -z "${API_KEY:-}" ]]; then
    die "API_KEY is required. Set it in the environment, .env file, or via: API_KEY=secret sudo ./install.sh"
fi

CONTAINER_NAME="status-dashboard"
IMAGE_NAME="status-dashboard"
NGINX_CONF_SRC="$REPO_DIR/status-dashboard.conf"
NGINX_AVAILABLE="/etc/nginx/sites-available/status-dashboard.conf"
NGINX_ENABLED="/etc/nginx/sites-enabled/status-dashboard.conf"
NGINX_DEFAULT="/etc/nginx/sites-enabled/default"

# ---------------------------------------------------------------------------
# Build Docker image
# ---------------------------------------------------------------------------
info "Building Docker image '$IMAGE_NAME'..."
docker build -t "$IMAGE_NAME" "$REPO_DIR"

# ---------------------------------------------------------------------------
# Stop and remove any existing container (idempotent)
# ---------------------------------------------------------------------------
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    warn "Existing container '$CONTAINER_NAME' found — stopping and removing..."
    docker stop "$CONTAINER_NAME"
    docker rm "$CONTAINER_NAME"
fi

# ---------------------------------------------------------------------------
# Run the container
# ---------------------------------------------------------------------------
info "Starting container '$CONTAINER_NAME'..."
docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    -p "127.0.0.1:${PORT}:${PORT}" \
    -e "PORT=${PORT}" \
    -e "VERSION=${VERSION}" \
    -e "API_KEY=${API_KEY}" \
    "$IMAGE_NAME"

# ---------------------------------------------------------------------------
# Configure nginx
# ---------------------------------------------------------------------------
info "Installing nginx site config..."
cp "$NGINX_CONF_SRC" "$NGINX_AVAILABLE"

if [[ -L "$NGINX_DEFAULT" ]]; then
    info "Disabling default nginx site..."
    rm "$NGINX_DEFAULT"
fi

if [[ ! -L "$NGINX_ENABLED" ]]; then
    info "Enabling status-dashboard nginx site..."
    ln -s "$NGINX_AVAILABLE" "$NGINX_ENABLED"
fi

info "Validating nginx config..."
nginx -t

info "Enabling nginx at boot..."
systemctl enable --now nginx

info "Reloading nginx..."
systemctl reload nginx

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
VM_IP="$(hostname -I | awk '{print $1}')"
echo ""
echo -e "${GREEN}✓ Installation complete!${NC}"
echo -e "  Dashboard : ${GREEN}http://${VM_IP}/${NC}"
echo -e "  Status API: ${GREEN}http://${VM_IP}/api/v1/status${NC}"
echo -e "  Secret API: ${GREEN}http://${VM_IP}/api/v1/secret${NC} (requires X-API-Key header)"
echo ""
