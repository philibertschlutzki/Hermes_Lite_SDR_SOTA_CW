"""
N2ADR Filter Board integration for Hermes-Lite 2.

Handles:
1. Low-Pass Filter (LPF) relay selection (160m to 10m).
2. 3 MHz High-Pass Filter (HPF) broadcast band rejection relay.
3. OpenHPSDR C&C Register 0x08 relay control word calculation.
4. SWR and Forward/Reflected Power calculation from HL2 AIN1/AIN2 ADC telemetry.
5. High-SWR protection / interlock alerting.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BandInfo:
    name: str
    freq_min_hz: int
    freq_max_hz: int
    lpf_relay_bit: int  # Bit 0..5 in C&C reg 0x08
    enable_hpf: bool    # Bit 6 in C&C reg 0x08 (3MHz HPF)


# Amateur HF bands supported by HL2 + N2ADR filter board
HF_BANDS: list[BandInfo] = [
    BandInfo("160m", 1_800_000, 2_000_000, lpf_relay_bit=0, enable_hpf=False),
    BandInfo("80m", 3_500_000, 4_000_000, lpf_relay_bit=1, enable_hpf=True),
    BandInfo("60m", 5_250_000, 5_450_000, lpf_relay_bit=2, enable_hpf=True),
    BandInfo("40m", 7_000_000, 7_300_000, lpf_relay_bit=2, enable_hpf=True),
    BandInfo("30m", 10_100_000, 10_150_000, lpf_relay_bit=3, enable_hpf=True),
    BandInfo("20m", 14_000_000, 14_350_000, lpf_relay_bit=3, enable_hpf=True),
    BandInfo("17m", 18_068_000, 18_168_000, lpf_relay_bit=4, enable_hpf=True),
    BandInfo("15m", 21_000_000, 21_450_000, lpf_relay_bit=4, enable_hpf=True),
    BandInfo("12m", 24_890_000, 24_990_000, lpf_relay_bit=5, enable_hpf=True),
    BandInfo("10m", 28_000_000, 29_700_000, lpf_relay_bit=5, enable_hpf=True),
    BandInfo("6m", 50_000_000, 54_000_000, lpf_relay_bit=5, enable_hpf=True),
]


@dataclass
class SWRMeasurement:
    fwd_power_w: float
    rev_power_w: float
    vswr: float
    return_loss_db: float
    is_safe: bool
    ain1_raw: int
    ain2_raw: int


class N2ADRFilterBoard:
    """Controller for the N2ADR Low-Pass Filter board on Hermes-Lite 2."""

    def __init__(self, max_vswr_threshold: float = 3.0, power_cal_factor: float = 5.0):
        self.max_vswr_threshold = max_vswr_threshold
        # Calibration factor mapping ADC voltage to Watts for HL2 ~5W PA
        self.power_cal_factor = power_cal_factor
        self.current_band: Optional[BandInfo] = None
        self.current_relay_word: int = 0
        self.last_measurement: Optional[SWRMeasurement] = None

    def get_band_for_frequency(self, freq_hz: int) -> BandInfo:
        """Find the corresponding amateur band for a given frequency."""
        for band in HF_BANDS:
            if band.freq_min_hz <= freq_hz <= band.freq_max_hz:
                return band
        
        # Fallback for general coverage / cross-band listening:
        # Select closest LPF based on cutoff
        if freq_hz < 2_500_000:
            return BandInfo("160m (Gen)", freq_hz, freq_hz, lpf_relay_bit=0, enable_hpf=False)
        elif freq_hz < 4_500_000:
            return BandInfo("80m (Gen)", freq_hz, freq_hz, lpf_relay_bit=1, enable_hpf=True)
        elif freq_hz < 8_000_000:
            return BandInfo("40m (Gen)", freq_hz, freq_hz, lpf_relay_bit=2, enable_hpf=True)
        elif freq_hz < 15_000_000:
            return BandInfo("20m (Gen)", freq_hz, freq_hz, lpf_relay_bit=3, enable_hpf=True)
        elif freq_hz < 22_000_000:
            return BandInfo("15m (Gen)", freq_hz, freq_hz, lpf_relay_bit=4, enable_hpf=True)
        else:
            return BandInfo("10m (Gen)", freq_hz, freq_hz, lpf_relay_bit=5, enable_hpf=True)

    def calculate_relay_word(self, freq_hz: int) -> int:
        """
        Calculate the 7-bit control word for OpenHPSDR C&C Register 0x08.
        
        Bit 6: 3 MHz High-Pass Filter (1 = enabled, 0 = bypassed)
        Bits 0-5: 1-of-6 Low-Pass Filter relay selection
        """
        band = self.get_band_for_frequency(freq_hz)
        self.current_band = band
        
        word = (1 << band.lpf_relay_bit) & 0x3F
        if band.enable_hpf:
            word |= 0x40  # Bit 6 high
            
        self.current_relay_word = word
        return word

    def compute_swr_and_power(self, ain1_raw: int, ain2_raw: int) -> SWRMeasurement:
        """
        Compute Forward Power, Reflected Power and VSWR from HL2 ADC values.
        
        ain1_raw: ADC reading for Forward Power (12-bit, 0..4095)
        ain2_raw: ADC reading for Reverse Power (12-bit, 0..4095)
        """
        # Convert 12-bit ADC counts to normalized volts (0.0 to 3.3V)
        v_fwd = (ain1_raw / 4095.0) * 3.3
        v_rev = (ain2_raw / 4095.0) * 3.3

        # Square law detector power approximation: P = (V * cal)^2
        p_fwd = round((v_fwd * self.power_cal_factor) ** 2, 2)
        p_rev = round((v_rev * self.power_cal_factor) ** 2, 2)

        # Calculate VSWR
        if p_fwd > 0.05 and v_fwd > 0.01:
            gamma = min(0.999, v_rev / v_fwd)
            if gamma < 0.999:
                vswr = (1.0 + gamma) / (1.0 - gamma)
                vswr = round(max(1.0, min(99.0, vswr)), 2)
                return_loss_db = round(-20.0 * math.log10(max(0.001, gamma)), 1)
            else:
                vswr = 99.0
                return_loss_db = 0.0
        else:
            vswr = 1.0
            return_loss_db = 40.0
            p_fwd = 0.0
            p_rev = 0.0

        is_safe = vswr <= self.max_vswr_threshold

        measurement = SWRMeasurement(
            fwd_power_w=p_fwd,
            rev_power_w=p_rev,
            vswr=vswr,
            return_loss_db=return_loss_db,
            is_safe=is_safe,
            ain1_raw=ain1_raw,
            ain2_raw=ain2_raw,
        )
        self.last_measurement = measurement
        return measurement
