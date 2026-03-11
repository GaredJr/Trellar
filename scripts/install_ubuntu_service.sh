#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${APP_NAME:-trellar}"
APP_DIR="${APP_DIR:-$PWD}"
APP_USER="${APP_USER:-$USER}"
APP_GROUP="${APP_GROUP:-$APP_USER}"
VENV_DIR="${VENV_DIR:-${APP_DIR}/.venv}"
BIND_HOST="${BIND_HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-3}"
UNIT_PATH="/etc/systemd/system/${APP_NAME}.service"

if [[ ! -f "${APP_DIR}/app.py" ]]; then
  echo "Could not find app.py in APP_DIR=${APP_DIR}" >&2
  exit 1
fi

if [[ ! -f "${APP_DIR}/requirements.txt" ]]; then
  echo "Could not find requirements.txt in APP_DIR=${APP_DIR}" >&2
  exit 1
fi

echo "[1/5] Installing Python runtime packages..."
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip

echo "[2/5] Creating virtual environment in ${VENV_DIR}..."
python3 -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"

echo "[3/5] Writing ${UNIT_PATH}..."
TMP_SERVICE_FILE="$(mktemp)"
cat >"${TMP_SERVICE_FILE}" <<EOF
[Unit]
Description=${APP_NAME} Flask app (Gunicorn)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_GROUP}
WorkingDirectory=${APP_DIR}
EnvironmentFile=-${APP_DIR}/.env
Environment=PYTHONUNBUFFERED=1
ExecStart=${VENV_DIR}/bin/gunicorn --workers ${WORKERS} --bind ${BIND_HOST}:${PORT} --access-logfile - --error-logfile - app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo mv "${TMP_SERVICE_FILE}" "${UNIT_PATH}"
sudo chmod 644 "${UNIT_PATH}"

echo "[4/5] Enabling and starting ${APP_NAME}.service..."
sudo systemctl daemon-reload
sudo systemctl enable --now "${APP_NAME}.service"

echo "[5/5] Service status:"
sudo systemctl --no-pager --full status "${APP_NAME}.service" || true

echo
echo "Done."
echo "Check logs with: sudo journalctl -u ${APP_NAME}.service -f"
echo "Current bind address: http://${BIND_HOST}:${PORT}"
