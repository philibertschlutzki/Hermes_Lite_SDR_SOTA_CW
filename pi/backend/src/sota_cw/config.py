import os

# HL2 Configuration
HL2_IP = os.getenv("SOTA_CW_HL2_IP", "192.168.1.50")
HL2_PORT = int(os.getenv("SOTA_CW_HL2_PORT", "1024"))

# IO Board Configuration
IO_REG_BASE = int(os.getenv("SOTA_CW_IO_REG_BASE", "200"))

# CW Decoder Configuration
# Command to pipe audio into multimon-ng.
# Adjust 'arecord' parameters to match your specific audio loopback/device from the SDR receiver.
# Example for PulseAudio monitor: "parec --format=s16le --rate=22050 --channels=1 | multimon-ng -a MORSE_CW -t raw -"
# Example for ALSA default: "arecord -r 22050 -f S16_LE -t raw -c 1 | multimon-ng -a MORSE_CW -t raw -"
CW_DECODER_CMD = os.getenv(
    "SOTA_CW_DECODER_CMD", 
    "arecord -r 22050 -f S16_LE -t raw -c 1 -D default | multimon-ng -a MORSE_CW -t raw -"
)
