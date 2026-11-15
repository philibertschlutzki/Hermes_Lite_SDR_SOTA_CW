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


class TestBandLockout:
    def test_6m_rx_only(self):
        board = N2ADRFilterBoard()
        assert board.get_band_for_frequency(50_100_000).tx_allowed is False
        assert board.get_band_for_frequency(14_060_000).tx_allowed is True

    def test_square_law_detector(self):
        board = N2ADRFilterBoard(detector_law="square")
        # Quadratischer Detektor: U_rev/U_fwd = 0.25 -> Γ = 0.5 -> SWR 3
        meas = board.compute_swr_and_power(ain1_raw=2000, ain2_raw=500)
        assert meas.vswr == pytest.approx(3.0, rel=0.05)


class TestHL2IOBoard:
    def test_frequency_encoding(self):
        mock_client = Mock()
        io = HL2IOBoard(mock_client)

        freq = 14_074_000  # 0x00D6C090
        io.set_tx_frequency(freq)

        calls = mock_client.i2c_write.call_args_list
        assert len(calls) == 5
        regs = [c.kwargs["reg"] for c in calls]
        data = [c.kwargs["data"] for c in calls]
        assert regs == [0, 1, 2, 3, 4]          # Register 4 (LSB) zuletzt = Übernahme
        assert data == [0x00, 0x00, 0xD6, 0xC0, 0x90]
        assert all(c.kwargs["i2c_addr"] == 0x1D for c in calls)
        assert all(c.kwargs["bus"] == 2 for c in calls)

    def test_atu_state_machine(self):
        mock_client = Mock()
        io = HL2IOBoard(mock_client)

        io.start_atu_tune()
        mock_client.i2c_write.assert_called_with(i2c_addr=0x1D, reg=7, data=1, bus=2)
        assert io.atu_in_progress is True

        io.bypass_atu()
        mock_client.i2c_write.assert_called_with(i2c_addr=0x1D, reg=7, data=2, bus=2)
        assert io.atu_in_progress is False

    def test_registers_are_8bit(self):
        io = HL2IOBoard(Mock())
        with pytest.raises(ValueError):
            io.write_reg(256, 0)
        with pytest.raises(ValueError):
            io.write_reg(200, 300)

    def test_status_from_4byte_reads(self):
        client = Mock()
        reads = {5: bytes([0, 0x01, 0, 0]), 9: bytes([2, 7, 0, 0]), 212: bytes([3, 0, 1, 0xC5])}
        client.i2c_read.side_effect = lambda **kw: reads[kw["reg"]]
        st = HL2IOBoard(client).get_status()
        assert st.reachable and st.keyer_present
        assert st.firmware_version == 2 and st.firmware_minor == 7
        assert st.exttr_tx is False
