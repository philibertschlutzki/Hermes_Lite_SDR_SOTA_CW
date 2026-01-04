"""
Unit tests for QSO Bot State Machine

Tests the deterministic state transitions and edge cases.
"""
import pytest
import time
from unittest.mock import Mock, MagicMock
from sota_cw.qso_bot import QSOBot, QSOState, BotConfig


@pytest.fixture
def mock_cw_manager():
    """Mock CW manager for testing."""
    manager = Mock()
    manager.is_busy.return_value = False
    manager.start_job.return_value = 1
    return manager


@pytest.fixture
def mock_cw_decoder():
    """Mock CW decoder for testing."""
    decoder = Mock()
    decoder.get_text.return_value = []
    decoder.clear_text.return_value = None
    return decoder


@pytest.fixture
def bot_config():
    """Default bot configuration."""
    return BotConfig(
        my_call="TEST0",
        my_ref="XX/XX-001",
        wpm=20,
        cq_interval=5,
        max_loops=3
    )


@pytest.fixture
def qso_bot(mock_cw_manager, mock_cw_decoder, bot_config):
    """QSO bot instance for testing."""
    bot = QSOBot(mock_cw_manager, mock_cw_decoder, bot_config)
    # Don't actually start the thread for unit tests
    return bot


class TestQSOBotStateTransitions:
    """Test state machine transitions."""
    
    def test_initial_state(self, qso_bot):
        """Bot should start in IDLE state."""
        assert qso_bot.state == QSOState.IDLE
        assert not qso_bot.running
        assert qso_bot.current_partner_call is None
    
    def test_trigger_cq_from_idle(self, qso_bot):
        """Triggering CQ should transition from IDLE to SENDING_CQ."""
        qso_bot.trigger_cq()
        assert qso_bot.state == QSOState.SENDING_CQ
        assert qso_bot.cq_loop_count == 0
    
    def test_cq_loop_count_reset(self, qso_bot):
        """CQ loop count should reset when trigger_cq called."""
        qso_bot.cq_loop_count = 5
        qso_bot.trigger_cq()
        assert qso_bot.cq_loop_count == 0
    
    def test_extract_callsign_valid(self, qso_bot):
        """Should extract valid amateur radio callsigns."""
        text = "DE W1ABC W1ABC K"
        call = qso_bot._extract_callsign(text)
        assert call == "W1ABC"
    
    def test_extract_callsign_hb9(self, qso_bot):
        """Should extract HB9 prefix callsigns."""
        text = "HB9XYZ QRZ"
        call = qso_bot._extract_callsign(text)
        assert call == "HB9XYZ"
    
    def test_extract_callsign_ignore_keywords(self, qso_bot):
        """Should ignore CW keywords."""
        text = "CQ SOTA TEST DE"
        call = qso_bot._extract_callsign(text)
        assert call is None
    
    def test_extract_callsign_ignore_own(self, qso_bot):
        """Should ignore own callsign."""
        qso_bot.config.my_call = "TEST0"
        text = "TEST0 TEST0 K"
        call = qso_bot._extract_callsign(text)
        assert call is None
    
    def test_extract_callsign_mixed(self, qso_bot):
        """Should find callsign among keywords."""
        qso_bot.config.my_call = "TEST0"
        text = "CQ DE G3ABC G3ABC K"
        call = qso_bot._extract_callsign(text)
        assert call == "G3ABC"


class TestQSOBotEdgeCases:
    """Test edge cases and error handling."""
    
    def test_multiple_cq_triggers(self, qso_bot):
        """Multiple trigger_cq calls should reset state properly."""
        qso_bot.trigger_cq()
        assert qso_bot.state == QSOState.SENDING_CQ
        
        qso_bot.trigger_cq()
        assert qso_bot.state == QSOState.SENDING_CQ
        assert qso_bot.cq_loop_count == 0
    
    def test_state_change_timing(self, qso_bot):
        """State changes should update timestamp."""
        initial_time = qso_bot.last_state_change
        time.sleep(0.01)
        qso_bot._change_state(QSOState.SENDING_CQ)
        assert qso_bot.last_state_change > initial_time


class TestBotConfiguration:
    """Test bot configuration."""
    
    def test_default_config(self, bot_config):
        """Default config should have sensible values."""
        assert bot_config.my_call == "TEST0"
        assert bot_config.wpm == 20
        assert bot_config.cq_interval == 5
        assert bot_config.max_loops == 3
    
    def test_config_update(self, qso_bot):
        """Should be able to update bot config."""
        qso_bot.config.my_call = "NEW0"
        qso_bot.config.wpm = 25
        assert qso_bot.config.my_call == "NEW0"
        assert qso_bot.config.wpm == 25
