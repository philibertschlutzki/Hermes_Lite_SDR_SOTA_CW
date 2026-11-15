#!/usr/bin/env bash
# ==============================================================================
# PipeWire Virtual Audio Loop Setup for Raspberry Pi 4B (Headless SDR)
# Configures persistent zero-latency virtual null sinks:
# 1. SDR_RX_Sink: HL2 demodulated audio -> WSJT-X, fldigi, and Tablet WebRTC
# 2. Digital_TX_Sink: WSJT-X and fldigi TX audio -> HL2 SSB modulator
# ==============================================================================
set -euo pipefail

echo "==> Configuring PipeWire Virtual Audio Nodes on Raspberry Pi 4B..."

# Ensure pipewire and pipewire-pulse packages are present
sudo apt update
sudo apt install -y pipewire pipewire-pulse pipewire-audio-client-libraries pulseaudio-utils

# Create PipeWire configuration directory for system-wide virtual sinks
CONFIG_DIR="/etc/pipewire/pipewire.conf.d"
sudo mkdir -p "${CONFIG_DIR}"

CONFIG_FILE="${CONFIG_DIR}/99-sdr-virtual-sinks.conf"

echo "==> Writing ${CONFIG_FILE}..."
sudo tee "${CONFIG_FILE}" > /dev/null << 'EOF'
context.objects = [
    {   factory = adapter
        args = {
            factory.name     = support.null-audio-sink
            node.name        = "SDR_RX_Sink"
            node.description = "HL2 SDR Receiver Audio (To Decoders & Tablet)"
            media.class      = "Audio/Sink"
            audio.position   = [ FL FR ]
            audio.rate       = 48000
        }
    }
    {   factory = adapter
        args = {
            factory.name     = support.null-audio-sink
            node.name        = "Digital_TX_Sink"
            node.description = "Digital Modems Audio (To HL2 Transmitter)"
            media.class      = "Audio/Sink"
            audio.position   = [ FL FR ]
            audio.rate       = 48000
        }
    }
]
EOF

# Headless: PipeWire des Benutzers ohne Login starten, damit die systemd-Dienste
# (Backend, WSJT-X, fldigi) die virtuellen Sinks finden.
SDR_USER="${SUDO_USER:-pi}"
sudo loginctl enable-linger "${SDR_USER}" || true

echo "==> Restarting PipeWire user services..."
systemctl --user restart pipewire pipewire-pulse || true

echo "==> PipeWire virtual audio sinks configured successfully."
echo "    Verify with: pw-cli list-objects | grep -E 'SDR_RX_Sink|Digital_TX_Sink'"
