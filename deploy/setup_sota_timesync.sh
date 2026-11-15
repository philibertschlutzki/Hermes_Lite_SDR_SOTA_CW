#!/usr/bin/env bash
# ==============================================================================
# SOTA-Zeitsynchronisation ohne Internet (chrony + USB-GPS, optional PPS und DS3231)
#
# Ziel: Systemzeit auf besser als ±0,5 s, damit WSJT-X (FT8/FT4 brauchen ±1 s)
# zuverlässig dekodiert.
#
# - USB-GPS ohne PPS: NMEA über gpsd (SHM 0) ist die wählbare Zeitquelle.
#   Genauigkeit typ. 50..200 ms; der Offset hängt vom Empfänger ab und lässt
#   sich mit SOTA_GPS_OFFSET anpassen (siehe docs/05_troubleshooting.md).
# - GPS mit PPS (optional): SHM 1 wird bevorzugt, sobald gpsd PPS liefert.
# - DS3231-RTC (optional, I2C am Pi): hält die Zeit bis zum ersten GPS-Fix.
#
# Umgebungsvariablen:
#   SOTA_GPS_OFFSET=0.150   NMEA-Verzögerung in Sekunden
#   SOTA_ENABLE_RTC=1       DS3231 einrichten (Standard: 1)
# ==============================================================================
set -euo pipefail

GPS_OFFSET="${SOTA_GPS_OFFSET:-0.150}"
ENABLE_RTC="${SOTA_ENABLE_RTC:-1}"

echo "==> Installing chrony, gpsd ..."
sudo apt update
sudo apt install -y chrony gpsd gpsd-clients pps-tools i2c-tools

CHRONY_CONF="/etc/chrony/chrony.conf"
SOTA_CONF="/etc/chrony/conf.d/sota-gps.conf"
sudo mkdir -p /etc/chrony/conf.d

# Frühere Version dieses Skripts hat direkt in chrony.conf geschrieben (GPS mit noselect)
if grep -q "refclock SHM 0 refid GPS" "${CHRONY_CONF}"; then
  echo "==> Entferne alte SOTA-Refclock-Zeilen aus ${CHRONY_CONF}"
  sudo sed -i '/# SOTA GPS NMEA & PPS Reference Clock/d;/refclock SHM 0 refid GPS/d;/refclock SHM 1 refid PPS/d;/^makestep 0.1 3$/d' "${CHRONY_CONF}"
fi
grep -q "^confdir /etc/chrony/conf.d" "${CHRONY_CONF}" || echo "confdir /etc/chrony/conf.d" | sudo tee -a "${CHRONY_CONF}" > /dev/null

echo "==> Schreibe ${SOTA_CONF}"
sudo tee "${SOTA_CONF}" > /dev/null << EOF2
# SOTA: GPS-NMEA ist wählbar (kein noselect), damit ein USB-GPS ohne PPS reicht.
refclock SHM 0 refid NMEA precision 1e-1 offset ${GPS_OFFSET} delay 0.2 poll 3 trust
# PPS (nur wenn vorhanden) wird bevorzugt; lock an NMEA für die Sekundenzuordnung.
refclock SHM 1 refid PPS precision 1e-7 lock NMEA prefer
# Ohne Internet: große Sprünge jederzeit erlauben (Pi ohne RTC startet mit falscher Zeit)
makestep 1 -1
# Systemzeit regelmäßig in die RTC schreiben
rtcsync
# Lokale Clients (Tablet) dürfen die Zeit vom Pi holen
allow 192.168.0.0/16
allow 10.0.0.0/8
local stratum 10
EOF2

echo "==> gpsd konfigurieren"
sudo tee /etc/default/gpsd > /dev/null << 'EOF2'
START_DAEMON="true"
USBAUTO="true"
DEVICES="/dev/ttyUSB0 /dev/ttyACM0"
GPSD_OPTIONS="-n"
EOF2

if [[ "${ENABLE_RTC}" == "1" ]]; then
  echo "==> DS3231-RTC einrichten (I2C am Pi: SDA GPIO2, SCL GPIO3)"
  BOOTCFG="/boot/firmware/config.txt"
  [[ -f "${BOOTCFG}" ]] || BOOTCFG="/boot/config.txt"
  grep -q "^dtparam=i2c_arm=on" "${BOOTCFG}" || echo "dtparam=i2c_arm=on" | sudo tee -a "${BOOTCFG}" > /dev/null
  grep -q "^dtoverlay=i2c-rtc,ds3231" "${BOOTCFG}" || echo "dtoverlay=i2c-rtc,ds3231" | sudo tee -a "${BOOTCFG}" > /dev/null
  # fake-hwclock würde die RTC-Zeit beim Booten überschreiben
  if dpkg -s fake-hwclock >/dev/null 2>&1; then
    sudo apt purge -y fake-hwclock
  fi
  echo "    Nach dem Neustart prüfen: sudo hwclock -r"
fi

sudo systemctl restart gpsd || true
sudo systemctl restart chrony

echo "==> Zeit-Sync konfiguriert. Prüfen mit: chronyc sources -v ; chronyc tracking"
