#!/usr/bin/env bash
set -euo pipefail

# Minimal installer (paths can be adapted)

PREFIX="/opt/sota-cw"

echo "Installing to ${PREFIX}"

sudo mkdir -p "${PREFIX}"
sudo rsync -a --delete ./ "${PREFIX}/"

echo "Creating venv"
cd "${PREFIX}/pi/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

echo "Installing systemd service"
sudo cp "${PREFIX}/deploy/sota-cw-backend.service" /etc/systemd/system/sota-cw-backend.service
sudo systemctl daemon-reload
sudo systemctl enable --now sota-cw-backend.service

echo "nginx config: copy deploy/nginx-site.conf to /etc/nginx/sites-available/ and enable it"
