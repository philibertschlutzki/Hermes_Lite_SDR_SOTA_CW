#!/usr/bin/env bash
# ==============================================================================
# SOTA Offline Time Synchronization Setup (Chrony + GPS / RTC)
# Ensures accurate system time (< 100 ms) for FT8/FT4 without cellular/internet.
# ==============================================================================
set -euo pipefail

echo "==> Installing Chrony and GPS utilities for SOTA timekeeping..."
sudo apt update
sudo apt install -y chrony gpsd gpsd-clients

# Configure Chrony with NMEA / PPS SHM driver from GPS
CHRONY_CONF="/etc/chrony/chrony.conf"

echo "==> Updating ${CHRONY_CONF} with GPS reference clock..."
if ! grep -q "refclock SHM 0" "${CHRONY_CONF}"; then
sudo tee -a "${CHRONY_CONF}" > /dev/null << 'EOF'

# SOTA GPS NMEA & PPS Reference Clock (USB GPS Dongle)
refclock SHM 0 refid GPS precision 1e-1 offset 0.125 delay 0.2 noselect
refclock SHM 1 refid PPS precision 1e-7 prefer
makestep 0.1 3
EOF
fi

# Configure gpsd default device
sudo tee /etc/default/gpsd > /dev/null << 'EOF'
START_DAEMON="true"
USBAUTO="true"
DEVICES="/dev/ttyUSB0 /dev/ttyACM0"
GPSD_OPTIONS="-n"
EOF

sudo systemctl restart chrony
sudo systemctl restart gpsd || true

echo "==> Chrony GPS time-sync configured."
echo "    Check status with: chronyc sources -v"
