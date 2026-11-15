"""
Unit tests for Digital Modems (WSJT-X, fldigi, Hamlib CAT).
"""
import pytest
import struct
from unittest.mock import Mock

from sota_cw.modems.wsjtx_client import (
    WSJTXClient,
    WSJTXDecode,
    WSJTX_MAGIC,
    WSJTX_SCHEMA_VERSION,
    MSG_STATUS,
    MSG_DECODE,
)
from sota_cw.modems.fldigi_client import FldigiClient
from sota_cw.hardware.cat_server import HamlibCatServer


class TestWSJTXClient:
    def test_decode_parsing(self):
        client = WSJTXClient()

        # Build a synthetic WSJT-X Decode packet
        buf = bytearray()
        buf.extend(struct.pack(">I", WSJTX_MAGIC))
        buf.extend(struct.pack(">I", WSJTX_SCHEMA_VERSION))
        buf.extend(struct.pack(">I", MSG_DECODE))

        # Id: "WSJT-X"
        client_id = "WSJT-X".encode("utf-8")
        buf.extend(struct.pack(">I", len(client_id)))
        buf.extend(client_id)

        # New decode (bool)
        buf.extend(struct.pack(">?", True))
        # Time ms (12:30:00 = 45,000,000 ms)
        buf.extend(struct.pack(">I", 45000000))
        # SNR (-12 dB)
        buf.extend(struct.pack(">i", -12))
        # Delta time (0.2 s)
        buf.extend(struct.pack(">d", 0.2))
        # Delta freq (1250 Hz)
        buf.extend(struct.pack(">I", 1250))

        # Mode "~" (FT8)
        mode = "~".encode("utf-8")
        buf.extend(struct.pack(">I", len(mode)))
        buf.extend(mode)

        # Message "CQ SOTA HB9SOTA JN47"
        msg = "CQ SOTA HB9SOTA JN47".encode("utf-8")
        buf.extend(struct.pack(">I", len(msg)))
        buf.extend(msg)

        # Parse packet
        client._parse_packet(bytes(buf))

        decodes = client.get_decodes()
        assert len(decodes) == 1
        d = decodes[0]
        assert d.snr_db == -12
        assert d.delta_freq_hz == 1250
        assert d.mode == "~"
        assert d.message == "CQ SOTA HB9SOTA JN47"
        assert d.callsign == "HB9SOTA"
        assert d.grid == "JN47"
        assert d.is_cq is True


class TestHamlibCatServer:
    def test_cat_command_processing(self):
        mock_hl2 = Mock()
        mock_hl2.frequency_hz = 14074000
        mock_hl2.mode = "USB"
        mock_hl2.is_transmitting = False

        cat = HamlibCatServer(hl2=mock_hl2)

        # Get frequency
        resp_f = cat._process_command("f")
        assert resp_f == "14074000\n"

        # Set frequency
        resp_set_f = cat._process_command("F 7030000")
        assert resp_set_f == "RPRT 0\n"
        mock_hl2.set_frequency_hz.assert_called_with(7030000)

        # Get mode
        resp_m = cat._process_command("m")
        assert "USB" in resp_m

        # Set PTT
        resp_ptt = cat._process_command("T 1")
        assert resp_ptt == "RPRT 0\n"
        mock_hl2.set_ptt.assert_called_with(True)
