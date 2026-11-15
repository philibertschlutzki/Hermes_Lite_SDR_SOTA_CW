#!/usr/bin/env bash
# ==============================================================================
# Master Installer: Hermes-Lite 2 SDR Headless SOTA & Digital Station
# Architecture: Raspberry Pi 4B (ARM64) + Android Tablet Client
# Operating Modes: CW (Pico Keyer), FT8, FT4, WSPR, JT9, JT65, FST4, PSK31, RTTY
# ==============================================================================
set -euo pipefail

PREFIX="/opt/sota-cw"
USER_NAME="${SUDO_USER:-pi}"

echo "=========================================================="
echo " Starting Installation of Hermes Lite 2 SDR Station Stack "
echo " Target Directory: ${PREFIX}"
echo "=========================================================="

echo "==> Step 1: Installing system packages and build tools..."
sudo apt update
sudo apt install -y \
    python3 python3-venv python3-pip \
    wsjtx fldigi hamlib-utils \
    pipewire pipewire-pulse alsa-utils xvfb \
    nginx rsync curl git chrony

echo "==> Step 2: Deploying codebase to ${PREFIX}..."
sudo mkdir -p "${PREFIX}"
sudo rsync -a --delete --exclude='.git' --exclude='.venv' ./ "${PREFIX}/"
sudo chown -R "${USER_NAME}:${USER_NAME}" "${PREFIX}"

echo "==> Step 3: Setting up Python virtual environment..."
cd "${PREFIX}/pi/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Step 4: Configuring PipeWire audio routing..."
bash "${PREFIX}/deploy/setup_pipewire_audio.sh"

echo "==> Step 5: Configuring SOTA GPS/RTC time-sync..."
bash "${PREFIX}/deploy/setup_sota_timesync.sh"

echo "==> Step 6: Installing systemd services..."
sudo cp "${PREFIX}/deploy/systemd/"*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sota-sdr-backend.service
sudo systemctl enable sota-wsjtx.service
sudo systemctl enable sota-fldigi.service

echo "==> Step 7: Configuring Nginx Web Reverse Proxy..."
sudo cp "${PREFIX}/deploy/nginx-site.conf" /etc/nginx/sites-available/sota-sdr.conf
sudo ln -sf /etc/nginx/sites-available/sota-sdr.conf /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "==> Step 8: Starting all SDR services..."
sudo systemctl start sota-sdr-backend.service || true

echo "=========================================================="
echo " Installation Complete! "
echo " Access the Tablet Web Cockpit at: http://<raspberry_pi_ip>/"
echo " Backend REST API Docs: http://<raspberry_pi_ip>:8000/docs"
echo "=========================================================="
