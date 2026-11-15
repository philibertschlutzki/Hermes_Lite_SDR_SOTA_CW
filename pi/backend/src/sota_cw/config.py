"""
Centralized configuration using Pydantic Settings.
Single source of truth for all configuration parameters.
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_prefix="SOTA_CW_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # HL2 Network Configuration
    hl2_ip: str = Field(default="192.168.1.50", description="HL2 IP address")
    hl2_port: int = Field(default=1024, description="HL2 UDP port")
    hl2_local_port: int = Field(
        default=0,
        description="Lokaler UDP-Port des einzigen HL2-Sockets (0 = beliebig)"
    )
    hl2_drive_level: int = Field(default=15, ge=0, le=15, description="TX-Drive-Level 0..15 (C&C 0x09)")
    hl2_cw_hang_ms: int = Field(default=250, ge=0, le=1023, description="CW-Hang-Zeit des HL2 (C&C 0x10)")
    hl2_custom_gateware_envelope: bool = Field(
        default=False,
        description="Eigene Gateware mit Envelope-Registern 0x18/0x19 (Standard-Gateware: False)",
    )
    
    # Hardware Integration (N2ADR & IO Board)
    n2adr_enabled: bool = Field(default=True, description="Enable N2ADR Filter Board control")
    max_vswr_threshold: float = Field(default=3.0, description="Max safe VSWR before TX interlock trip")
    swr_trip_count: int = Field(default=3, ge=1, description="Messungen über Grenzwert in Folge bis zur Abschaltung")
    power_cal_factor: float = Field(default=5.0, description="Kalibrierfaktor Leistung (am Gerät bestimmen)")
    power_detector_law: str = Field(default="linear", description="linear oder square")
    io_board_enabled: bool = Field(default=True, description="Enable HL2 IO Board (RP2040 Pico) support")
    io_reg_base: int = Field(default=200, ge=0, le=240, description="Erstes CW-Keyer-Register im Pico (8 bit)")
    cw_watchdog_s: int = Field(default=3, ge=1, le=30, description="Pico lässt die Taste los, wenn so lange kein Heartbeat kommt")
    
    # Hamlib CAT Server Configuration
    cat_server_enabled: bool = Field(default=True, description="Enable built-in Hamlib rigctld CAT server")
    cat_server_host: str = Field(default="127.0.0.1", description="CAT server bind host")
    cat_server_port: int = Field(default=4532, description="CAT server TCP port (default rigctld 4532)")

    # Digital Modes Configuration
    wsjtx_enabled: bool = Field(default=True, description="Enable WSJT-X UDP client")
    wsjtx_host: str = Field(default="127.0.0.1", description="WSJT-X UDP host")
    wsjtx_port: int = Field(default=2237, description="WSJT-X UDP port")

    fldigi_enabled: bool = Field(default=True, description="Enable fldigi XML-RPC client (PSK31/RTTY)")
    fldigi_host: str = Field(default="127.0.0.1", description="fldigi XML-RPC host")
    fldigi_port: int = Field(default=7362, description="fldigi XML-RPC port")
    
    # CW TX Envelope Shaping (HL2-side amplitude control)
    # Defaults are intentionally non-zero to enable click-reduction out of the box
    cw_env_rise_us: int = Field(default=3000, ge=0, le=20000, description="CW envelope rise time (µs)")
    cw_env_fall_us: int = Field(default=3000, ge=0, le=20000, description="CW envelope fall time (µs)")
    cw_env_shape: int = Field(default=0, ge=0, le=10, description="CW envelope shape index")
    cw_env_max_amp_q15: int = Field(default=32767, ge=0, le=32767, description="CW envelope max amplitude (Q15)")
    
    # CW Decoder Configuration
    use_internal_streamer: bool = Field(
        default=True, 
        description="Use internal Python-based streamer (no external pipe command needed)"
    )
    
    cw_decoder_cmd_legacy: str = Field(
        default="parec --device=SDR_RX_Sink.monitor --rate=22050 --channels=1 --format=s16le | multimon-ng -a MORSE_CW -t raw -",
        description="Fallback command if internal streamer is disabled (legacy mode)"
    )
    
    # Audio Streaming Configuration
    audio_sample_rate: int = Field(default=48000, description="Audio sample rate for streaming")
    cw_pitch_hz: int = Field(default=600, ge=300, le=1000, description="CW-Mithörton")
    pipewire_enabled: bool = Field(default=True, description="RX/TX-Audio über PipeWire (pacat/parec)")
    rx_audio_sink_cmd: str = Field(
        default="pacat --playback --device=SDR_RX_Sink --rate=48000 --channels=1 --format=s16le --latency-msec=60",
        description="Prozess, der RX-Audio (s16le, 48 kHz, mono) von stdin nach SDR_RX_Sink spielt",
    )
    tx_audio_source_cmd: str = Field(
        default="parec --device=Digital_TX_Sink.monitor --rate=48000 --channels=1 --format=s16le --latency-msec=20",
        description="Prozess, der TX-Audio der Modems (s16le, 48 kHz, mono) auf stdout liefert",
    )
    tx_audio_gain: float = Field(default=1.0, ge=0.0, le=4.0, description="Verstärkung TX-Audio vor dem Modulator")

    # Zugriffsschutz
    api_token: str = Field(default="", description="Wenn gesetzt: Token für alle API-Aufrufe (Header X-API-Token oder ?token=)")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host address")
    api_port: int = Field(default=8000, description="API port")
    api_reload: bool = Field(default=False, description="Enable API auto-reload (dev only)")


# Global settings instance - single source of truth
settings = Settings()

# Backwards compatibility: expose legacy names for existing code
HL2_IP = settings.hl2_ip
HL2_PORT = settings.hl2_port
HL2_LOCAL_PORT = settings.hl2_local_port
IO_REG_BASE = settings.io_reg_base
CW_ENV_RISE_US = settings.cw_env_rise_us
CW_ENV_FALL_US = settings.cw_env_fall_us
CW_ENV_SHAPE = settings.cw_env_shape
CW_ENV_MAX_AMP_Q15 = settings.cw_env_max_amp_q15
USE_INTERNAL_STREAMER = settings.use_internal_streamer
CW_DECODER_CMD_LEGACY = settings.cw_decoder_cmd_legacy

# Multimon-ng command for internal streamer (reads from stdin)
CW_DECODER_CMD_INTERNAL = ["multimon-ng", "-a", "MORSE_CW", "-t", "raw", "-"]
