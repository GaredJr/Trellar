#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Usage: $0 <tunnel-id> <hostname> [origin-url]"
  echo "Example: $0 11111111-2222-3333-4444-555555555555 trellar.example.com http://localhost:8000"
  exit 1
fi

TUNNEL_ID="$1"
HOSTNAME="$2"
ORIGIN_URL="${3:-http://localhost:8000}"
CONFIG_DIR="${CONFIG_DIR:-/etc/cloudflared}"
CONFIG_PATH="${CONFIG_DIR}/config.yml"
CREDENTIALS_PATH="${CONFIG_DIR}/${TUNNEL_ID}.json"
LOCAL_CREDENTIALS_PATH="${HOME}/.cloudflared/${TUNNEL_ID}.json"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared is not installed." >&2
  echo "Install cloudflared first, then run this script again." >&2
  exit 1
fi

if [[ ! -f "${CREDENTIALS_PATH}" && ! -f "${LOCAL_CREDENTIALS_PATH}" ]]; then
  echo "Tunnel credentials not found for ${TUNNEL_ID}." >&2
  echo "Run these first:" >&2
  echo "  cloudflared tunnel login" >&2
  echo "  cloudflared tunnel create trellar" >&2
  exit 1
fi

echo "[1/4] Preparing ${CONFIG_DIR}..."
sudo mkdir -p "${CONFIG_DIR}"

if [[ ! -f "${CREDENTIALS_PATH}" ]]; then
  echo "[2/4] Copying credentials to ${CREDENTIALS_PATH}..."
  sudo cp "${LOCAL_CREDENTIALS_PATH}" "${CREDENTIALS_PATH}"
  sudo chmod 600 "${CREDENTIALS_PATH}"
else
  echo "[2/4] Credentials already exist at ${CREDENTIALS_PATH}."
fi

echo "[3/4] Writing ${CONFIG_PATH}..."
TMP_CONFIG_FILE="$(mktemp)"
cat >"${TMP_CONFIG_FILE}" <<EOF
tunnel: ${TUNNEL_ID}
credentials-file: ${CREDENTIALS_PATH}

ingress:
  - hostname: ${HOSTNAME}
    service: ${ORIGIN_URL}
  - service: http_status:404
EOF

sudo mv "${TMP_CONFIG_FILE}" "${CONFIG_PATH}"
sudo chmod 644 "${CONFIG_PATH}"

echo "[4/4] Configuring DNS and starting cloudflared service..."
cloudflared tunnel route dns "${TUNNEL_ID}" "${HOSTNAME}"
if systemctl list-unit-files cloudflared.service --no-legend 2>/dev/null | grep -q "^cloudflared\\.service"; then
  echo "cloudflared service already installed."
else
  sudo cloudflared service install
fi
sudo systemctl enable --now cloudflared
sudo systemctl restart cloudflared
sudo systemctl --no-pager --full status cloudflared || true

echo
echo "Done."
echo "Tunnel target: ${ORIGIN_URL}"
echo "Public hostname: https://${HOSTNAME}"
