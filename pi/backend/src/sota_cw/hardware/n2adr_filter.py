"""
N2ADR Filter Board integration for Hermes-Lite 2.

Handles:
1. Low-Pass Filter (LPF) relay selection (160m to 10m).
2. 3 MHz High-Pass Filter (HPF) broadcast band rejection relay.
3. Relaiswort für die Open-Collector-Bits in C&C-Adresse 0x00 (DATA[23:17]).
   Der HL2 schickt dieses Byte selbst per I2C2 an das Filterboard (0x20).
4. SWR und Vorwärts-/Rückwärtsleistung aus der HL2-Telemetrie (EP6 RADDR 0x01/0x02).
5. Grenzwert-Prüfung für die SWR-Abschaltung (siehe HL2Control).

Das N2ADR-Board hat keinen 6-m-Tiefpass: Auf 6 m ist nur Empfang erlaubt.
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
    lpf_relay_bit: int  # Bit 0..5 des OC-Worts (C&C 0x00, DATA[22:17])
    enable_hpf: bool    # Bit 6 des OC-Worts (3-MHz-Hochpass)
    tx_allowed: bool = True


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
    # Kein 6-m-Filter auf dem N2ADR-Board: nur RX, TX gesperrt
    BandInfo("6m", 50_000_000, 54_000_000, lpf_relay_bit=5, enable_hpf=True, tx_allowed=False),
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

    def __init__(
        self,
        max_vswr_threshold: float = 3.0,
        power_cal_factor: float = 5.0,
        *,
        adc_full_scale: int = 4095,
        adc_vref: float = 3.3,
        detector_law: str = "linear",
        min_fwd_power_w: float = 0.05,
    ):
        """
        power_cal_factor: P = (U_det * power_cal_factor)^2 bei linearem Detektor.
        detector_law: "linear" (U_det ~ U_HF, P ~ U_det^2) oder "square" (U_det ~ P).
        Beide Größen müssen am Gerät mit Dummy-Load und Wattmeter kalibriert werden.
        """
        if detector_law not in ("linear", "square"):
            raise ValueError("detector_law must be 'linear' or 'square'")
        self.max_vswr_threshold = max_vswr_threshold
        self.power_cal_factor = power_cal_factor
        self.adc_full_scale = adc_full_scale
        self.adc_vref = adc_vref
        self.detector_law = detector_law
        self.min_fwd_power_w = min_fwd_power_w
        self.current_band: Optional[BandInfo] = None
        self.current_relay_word: int = 0
        self.last_measurement: Optional[SWRMeasurement] = None

    def raw_to_power_w(self, raw: int) -> float:
        v = (max(0, int(raw)) / self.adc_full_scale) * self.adc_vref
        if self.detector_law == "linear":
            return (v * self.power_cal_factor) ** 2
        return v * self.power_cal_factor ** 2

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
        elif freq_hz <= 30_000_000:
            return BandInfo("10m (Gen)", freq_hz, freq_hz, lpf_relay_bit=5, enable_hpf=True)
        else:
            return BandInfo("VHF (Gen)", freq_hz, freq_hz, lpf_relay_bit=5, enable_hpf=True, tx_allowed=False)

    def calculate_relay_word(self, freq_hz: int) -> int:
        """
        7-bit-Wort für die Open-Collector-Ausgänge (C&C 0x00, DATA[23:17]).
        
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
        Vorwärts-/Rückwärtsleistung und SWR aus den HL2-Rohwerten.

        Γ wird immer aus dem Leistungsverhältnis berechnet: |Γ| = sqrt(P_rev / P_fwd).
        Beim linearen Detektor ist das gleich U_rev/U_fwd, beim quadratischen
        sqrt(U_rev/U_fwd). So passen Leistungs- und SWR-Formel zusammen (G13).
        """
        p_fwd = self.raw_to_power_w(ain1_raw)
        p_rev = self.raw_to_power_w(ain2_raw)

        if p_fwd >= self.min_fwd_power_w:
            gamma = math.sqrt(min(1.0, p_rev / p_fwd))
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

        measurement = SWRMeasurement(
            fwd_power_w=round(p_fwd, 2),
            rev_power_w=round(p_rev, 2),
            vswr=vswr,
            return_loss_db=return_loss_db,
            is_safe=vswr <= self.max_vswr_threshold,
            ain1_raw=int(ain1_raw),
            ain2_raw=int(ain2_raw),
        )
        self.last_measurement = measurement
        return measurement
