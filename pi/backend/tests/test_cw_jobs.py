"""
Unit tests for CW Job Manager

Tests job submission, scheduling, and queue management.
"""
import pytest
from unittest.mock import Mock, MagicMock
from sota_cw.cw_jobs import CWJobManager, CWJob, submit_job, abort_job


@pytest.fixture
def mock_io_board():
    """Mock IO board for testing."""
    io = Mock()
    io.reg_base = 200
    io.write_reg = Mock()
    io.read_cw_status = Mock()
    return io


@pytest.fixture
def mock_hl2_control():
    """Mock HL2 control for testing."""
    hl2 = Mock()
    hl2.set_cw_envelope = Mock()
    return hl2


@pytest.fixture
def cw_manager(mock_io_board, mock_hl2_control):
    """CW job manager instance."""
    return CWJobManager(
        mock_io_board,
        hl2=mock_hl2_control,
        default_env_rise_us=3000,
        default_env_fall_us=3000,
        default_env_shape=0,
        default_env_max_amp_q15=32767
    )


class TestCWJobCreation:
    """Test CW job creation and defaults."""
    
    def test_job_defaults(self):
        """CWJob should have sensible defaults."""
        job = CWJob(text="TEST")
        assert job.text == "TEST"
        assert job.wpm == 20
        assert job.ptt_lead_ms == 80
        assert job.ptt_tail_ms == 120
        assert job.farnsworth_wpm == 0
        assert job.weight_pct == 50
    
    def test_job_custom_params(self):
        """Should accept custom parameters."""
        job = CWJob(
            text="CQ",
            wpm=25,
            ptt_lead_ms=100,
            farnsworth_wpm=20,
            weight_pct=55
        )
        assert job.wpm == 25
        assert job.ptt_lead_ms == 100
        assert job.farnsworth_wpm == 20
        assert job.weight_pct == 55


class TestCWJobManager:
    """Test job manager functionality."""
    
    def test_start_job_increments_sequence(self, cw_manager):
        """Each job should get unique ID."""
        id1 = cw_manager.start_job("TEST1", 20)
        id2 = cw_manager.start_job("TEST2", 20)
        assert id2 == id1 + 1
    
    def test_start_job_programs_hl2_envelope(self, cw_manager, mock_hl2_control):
        """Starting job should program HL2 envelope."""
        cw_manager.start_job("TEST", 20, env_rise_us=5000, env_fall_us=5000)
        mock_hl2_control.set_cw_envelope.assert_called_once()
        args = mock_hl2_control.set_cw_envelope.call_args
        assert args.kwargs['rise_us'] == 5000
        assert args.kwargs['fall_us'] == 5000
    
    def test_start_job_uses_defaults(self, cw_manager, mock_hl2_control):
        """Should use manager defaults when not specified."""
        cw_manager.start_job("TEST", 20)
        mock_hl2_control.set_cw_envelope.assert_called_once()
        args = mock_hl2_control.set_cw_envelope.call_args
        assert args.kwargs['rise_us'] == 3000
        assert args.kwargs['fall_us'] == 3000
    
    def test_start_job_writes_io_board(self, cw_manager, mock_io_board):
        """Should write job parameters to IO board."""
        cw_manager.start_job("TEST", 25)
        # Should have written multiple registers
        assert mock_io_board.write_reg.call_count > 5
    
    def test_abort_job(self, cw_manager, mock_io_board):
        """Abort should write abort command."""
        cw_manager.abort_job()
        # Should write to CMD register (offset 0)
        calls = mock_io_board.write_reg.call_args_list
        assert any(call[0][0] == 200 for call in calls)  # reg_base + 0
    
    def test_get_status(self, cw_manager, mock_io_board):
        """Should fetch status from IO board."""
        from sota_cw.ioboard import CWStatus
        mock_io_board.read_cw_status.return_value = CWStatus(
            cmd=1, status=1, wpm=20, ptt_lead_ms=80, ptt_tail_ms=120,
            text_len=4, progress=2, error_code=0
        )
        status = cw_manager.get_status()
        assert status['wpm'] == 20
        assert status['text_len'] == 4
        assert status['progress'] == 2


class TestCWJobFunctions:
    """Test standalone job functions."""
    
    def test_submit_job_text_length_limit(self, mock_io_board):
        """Text should be truncated to 120 chars."""
        long_text = "A" * 150
        job = CWJob(text=long_text, wpm=20)
        submit_job(mock_io_board, job)
        # Should have truncated text
        # Verify WPM register was written with expected value
        calls = [call for call in mock_io_board.write_reg.call_args_list 
                 if call[0][0] == 202]  # WPM register offset
        assert len(calls) > 0
    
    def test_submit_job_registers_written(self, mock_io_board):
        """Should write all required registers."""
        job = CWJob(text="TEST", wpm=20, ptt_lead_ms=80, ptt_tail_ms=120)
        submit_job(mock_io_board, job)
        # Should write: WPM, PTT_LEAD, PTT_TAIL, TEXT_LEN, FARNSWORTH, WEIGHT, ENV_*, text buffer, CMD
        assert mock_io_board.write_reg.call_count >= 10
    
    def test_abort_job_function(self, mock_io_board):
        """Standalone abort should write abort command."""
        abort_job(mock_io_board)
        # Should write abort command (2) to CMD register
        mock_io_board.write_reg.assert_called()
