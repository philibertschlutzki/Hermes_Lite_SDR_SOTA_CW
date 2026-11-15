"""
Unit tests for N2ADR Filter Board and HL2 IO Board hardware integration.
"""
import pytest
from unittest.mock import Mock

from sota_cw.hardware.n2adr_filter import N2ADRFilterBoard, HF_BANDS
from sota_cw.hardware.hl2_io_board import HL2IOBoard, ATUState


class TestN2ADRFilterBoard:
    def test_band_selection(self):
        board = N2ADRFilterBoard()
        
        # 160m band: LPF 0, HPF disabled (Bit 6 = 0)
        band_160 = board.get_band_for_frequency(1_850_000)
        assert band_160.name == "160m"
        assert band_160.lpf_relay_bit == 0
        assert not band_160.enable_hpf
        word_160 = board.calculate_relay_word(1_850_000)
        assert word_160 == 0x01  # Bit 0 only

        # 40m band: LPF 2, HPF enabled (Bit 6 = 1)
        band_40 = board.get_band_for_frequency(7_030_000)
        assert band_40.name == "40m"
        assert band_40.lpf_relay_bit == 2
        assert band_40.enable_hpf
        word_40 = board.calculate_relay_word(7_030_000)
        assert word_40 == (1 << 2) | 0x40  # Relay 2 + HPF

        # 20m band: LPF 3, HPF enabled
        word_20 = board.calculate_relay_word(14_074_000)
        assert word_20 == (1 << 3) | 0x40

        # 10m band: LPF 5, HPF enabled
        word_10 = board.calculate_relay_word(28_074_000)
        assert word_10 == (1 << 5) | 0x40

    def test_swr_and_power_calculation(self):
        board = N2ADRFilterBoard(max_vswr_threshold=3.0)

        # Matched load (AIN1 high, AIN2 low)
        # ain1_raw = 2000, ain2_raw = 0
        meas = board.compute_swr_and_power(ain1_raw=2000, ain2_raw=0)
        assert meas.fwd_power_w > 0.0
        assert meas.rev_power_w == 0.0
        assert meas.vswr == 1.0
        assert meas.is_safe is True

        # SWR 3:1 load (V_rev = 0.5 * V_fwd => gamma = 0.5 => VSWR = 1.5 / 0.5 = 3.0)
        meas_3 = board.compute_swr_and_power(ain1_raw=2000, ain2_raw=1000)
        assert meas_3.vswr == pytest.approx(3.0, rel=0.05)
        assert meas_3.is_safe is True

        # High SWR trip (V_rev = 0.8 * V_fwd => gamma = 0.8 => VSWR = 1.8 / 0.2 = 9.0)
        meas_high = board.compute_swr_and_power(ain1_raw=2000, ain2_raw=1600)
        assert meas_high.vswr > 3.0
        assert meas_high.is_safe is False


class TestHL2IOBoard:
    def test_frequency_encoding(self):
        mock_client = Mock()
        io = HL2IOBoard(mock_client)

        freq = 14_074_000  # 0x00D6C110
        io.set_tx_frequency(freq)

        # Check register writes
        # 5 bytes written, ending with trigger write to reg 4
        calls = mock_client.ext_write_u16.call_args_list
        assert len(calls) == 5
        # Reg 0..3: high bytes
        # Reg 4: LSB trigger
        assert calls[4].kwargs["eaddr"] == 4
        assert calls[4].kwargs["value"] == (freq & 0xFF)

    def test_atu_state_machine(self):
        mock_client = Mock()
        io = HL2IOBoard(mock_client)

        # Trigger Tune
        io.start_atu_tune()
        mock_client.ext_write_u16.assert_called_with(eaddr=7, value=1)
        assert io.atu_in_progress is True

        # Trigger Bypass
        io.bypass_atu()
        mock_client.ext_write_u16.assert_called_with(eaddr=7, value=2)
        assert io.atu_in_progress is False
