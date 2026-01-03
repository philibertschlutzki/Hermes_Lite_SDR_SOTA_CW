import os

# HL2 Configuration
HL2_IP = os.getenv("SOTA_CW_HL2_IP", "192.168.1.50")
HL2_PORT = int(os.getenv("SOTA_CW_HL2_PORT", "1024"))

# IO Board Configuration
IO_REG_BASE = int(os.getenv("SOTA_CW_IO_REG_BASE", "200"))

# CW Decoder Configuration
# Enable internal python-based streamer (no external pipe command needed)
USE_INTERNAL_STREAMER = os.getenv("SOTA_CW_USE_INTERNAL_STREAMER", "true").lower() == "true"

# Fallback command if internal streamer is disabled (legacy mode)
# Example for ALSA default: "arecord -r 22050 -f S16_LE -t raw -c 1 | multimon-ng -a MORSE_CW -t raw -"
CW_DECODER_CMD_LEGACY = os.getenv(
    "SOTA_CW_DECODER_CMD", 
    "arecord -r 22050 -f S16_LE -t raw -c 1 -D default | multimon-ng -a MORSE_CW -t raw -"
)

# Multimon-ng command for internal streamer (reads from stdin)
CW_DECODER_CMD_INTERNAL = ["multimon-ng", "-a", "MORSE_CW", "-t", "raw", "-"]
