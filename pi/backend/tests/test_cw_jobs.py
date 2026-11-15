"""
Unit tests for CW Job Manager (Pico-Keyer über HL2-I2C2, 8-bit-Register).
"""
import pytest
from unittest.mock import Mock

from sota_cw.cw_jobs import CWJobManager, CWJob, submit_job, abort_job, sanitize_text, TxNotAllowed
from sota_cw.ioboard import (
    CWStatus, CW_CMD_ABORT, CW_CMD_CLEAR, CW_CMD_START, CW_STATUS_IDLE, CW_STATUS_RUNNING,
    REG_OFF_FIFO_DATA, REG_OFF_KEY_DIRECT,
)


@pytest.fixture
def mock_io_board():
    io = Mock()
    io.reg_base = 200
    io.last_text_len = 0
    io.write_reg = Mock()
    io.read_cw_status = Mock(return_value=CWStatus(
        cmd=0, status=CW_STATUS_IDLE, wpm=20, ptt_lead_ms=80, ptt_tail_ms=120,
        text_len=0, progress=0, error_code=0))
    return io


@pytest.fixture
def mock_hl2_control():
    hl2 = Mock()
    hl2.set_cw_envelope = Mock()
    hl2.tx_allowed = Mock(return_value=(True, ""))
    return hl2


@pytest.fixture
def cw_manager(mock_io_board, mock_hl2_control):
    m = CWJobManager(mock_io_board, hl2=mock_hl2_control)
    m.HEARTBEAT_INTERVAL_S = 0.01
    return m


def writes(io):
    return [(c.args[0], c.args[1]) for c in io.write_reg.call_args_list]


class TestSanitize:
    def test_upper_and_filter(self):
        assert sanitize_text("cq de hb9xyz\n k") == "CQ DE HB9XYZ K"
        assert sanitize_text("ä#€test") == "TEST"

    def test_length_limit(self):
        assert len(sanitize_text("E" * 400)) == 255


class TestSubmitJob:
    def test_register_sequence(self, mock_io_board):
        submit_job(mock_io_board, CWJob(text="TEST", wpm=25, ptt_lead_ms=80, ptt_tail_ms=120))
        w = writes(mock_io_board)
        assert w[0] == (200, CW_CMD_CLEAR)
        assert (202, 25) in w
        assert (203, 80) in w and (204, 120) in w
        fifo = [v for r, v in w if r == 200 + REG_OFF_FIFO_DATA]
        assert bytes(fifo) == b"TEST"
        assert w[-1] == (200, CW_CMD_START)

    def test_all_values_8bit_and_regs_below_256(self, mock_io_board):
        submit_job(mock_io_board, CWJob(text="A" * 300, wpm=99, ptt_lead_ms=1000, ptt_tail_ms=5000,
                                        weight_pct=100))
        for reg, val in writes(mock_io_board):
            assert 0 <= reg <= 255
            assert 0 <= val <= 255
        assert mock_io_board.last_text_len == 255

    def test_abort(self, mock_io_board):
        abort_job(mock_io_board)
        mock_io_board.write_reg.assert_called_with(200, CW_CMD_ABORT)


class TestCWJobManager:
    def test_start_job_increments_sequence(self, cw_manager):
        id1 = cw_manager.start_job("TEST1", 20)
        id2 = cw_manager.start_job("TEST2", 20)
        assert id2 == id1 + 1

    def test_start_job_passes_envelope_to_hl2(self, cw_manager, mock_hl2_control):
        cw_manager.start_job("TEST", 20, env_rise_us=5000, env_fall_us=5000)
        kw = mock_hl2_control.set_cw_envelope.call_args.kwargs
        assert kw["rise_us"] == 5000 and kw["fall_us"] == 5000

    def test_tx_lockout(self, cw_manager, mock_hl2_control, mock_io_board):
        mock_hl2_control.tx_allowed.return_value = (False, "SWR-Schutz")
        with pytest.raises(TxNotAllowed):
            cw_manager.start_job("TEST", 20)
        mock_io_board.write_reg.assert_not_called()

    def test_is_busy_from_status(self, cw_manager, mock_io_board):
        assert cw_manager.is_busy() is False
        mock_io_board.read_cw_status.return_value = CWStatus(
            cmd=1, status=CW_STATUS_RUNNING, wpm=20, ptt_lead_ms=80, ptt_tail_ms=120,
            text_len=4, progress=2, error_code=0)
        assert cw_manager.is_busy() is True

    def test_is_busy_fallback_when_unreachable(self, cw_manager, mock_io_board):
        mock_io_board.read_cw_status.side_effect = ConnectionError("down")
        assert cw_manager.is_busy() is False

    def test_tune_key_direct(self, cw_manager, mock_io_board):
        cw_manager.tune(True)
        assert (200 + REG_OFF_KEY_DIRECT, 1) in writes(mock_io_board)
        cw_manager.tune(False)
        assert writes(mock_io_board)[-1] == (200 + REG_OFF_KEY_DIRECT, 0)

    def test_get_status(self, cw_manager, mock_io_board):
        mock_io_board.read_cw_status.return_value = CWStatus(
            cmd=1, status=1, wpm=20, ptt_lead_ms=80, ptt_tail_ms=120,
            text_len=4, progress=2, error_code=0, fifo_level=2)
        st = cw_manager.get_status()
        assert st["wpm"] == 20 and st["progress"] == 2 and st["fifo_level"] == 2
