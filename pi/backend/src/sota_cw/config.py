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
        default=1025, 
        description="Local UDP port for HL2 control (1025 avoids conflict with streamer)"
    )
    
    # Hardware Integration (N2ADR & IO Board)
    n2adr_enabled: bool = Field(default=True, description="Enable N2ADR Filter Board control")
    max_vswr_threshold: float = Field(default=3.0, description="Max safe VSWR before TX interlock trip")
    io_board_enabled: bool = Field(default=True, description="Enable HL2 IO Board (RP2040 Pico) support")
    io_reg_base: int = Field(default=200, description="IO board register base address for CW keyer")
    
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
        default="arecord -r 22050 -f S16_LE -t raw -c 1 -D default | multimon-ng -a MORSE_CW -t raw -",
        description="Fallback command if internal streamer is disabled (legacy mode)"
    )
    
    # Audio Streaming Configuration
    audio_sample_rate: int = Field(default=48000, description="Audio sample rate for streaming")
    
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
