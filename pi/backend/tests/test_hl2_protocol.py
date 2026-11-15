"""Tests für Protocol-1-Framing, HL2Client-Scheduler, I2C und SWR-Schutz."""
import struct
import threading

import numpy as np
import pytest

from sota_cw import hl2_protocol as p
from sota_cw.hl2_client import HL2Client
from sota_cw.hl2_control import HL2Control
from sota_cw.ioboard import IOBoard


class FakeSocket:
    def __init__(self):
        self.sent = []

    def sendto(self, data, addr):
        self.sent.append(bytes(data))

    def recvfrom(self, n):
        import socket
        raise socket.timeout()

    def settimeout(self, t):
        pass


def frames(pkt):
    """(c0, data) der beiden EP2-Frames."""
    out = []
    for k in range(2):
        f = pkt[8 + k * 512: 8 + (k + 1) * 512]
        assert f[:3] == b"\x7f\x7f\x7f"
        out.append((f[3], struct.unpack(">I", f[4:8])[0]))
    return out


class TestFraming:
    def test_ep2_layout(self):
        pkt = p.build_ep2_packet(5, p.CCWrite(0x00, 0x12345678), p.CCWrite(0x01, 7_030_000), mox=True)
        assert len(pkt) == 1032
        assert pkt[:4] == b"\xef\xfe\x01\x02"
        assert struct.unpack(">I", pkt[4:8])[0] == 5
        (c0a, da), (c0b, db) = frames(pkt)
        assert c0a == 0x01 and da == 0x12345678     # Adresse 0, MOX
        assert c0b == (0x01 << 1) | 1 and db == 7_030_000

    def test_general_word(self):
        w = p.general_word(oc_bits=0x44, n_receivers=1, duplex=True)
        assert (w >> 17) & 0x7F == 0x44
        assert (w >> 24) & 0x3 == 0     # 48 kHz
        assert w & 0x4                   # Duplex
        assert (w >> 3) & 0xF == 0       # 1 Empfänger

    def test_i2c_word(self):
        w = p.i2c_word(write=True, i2c_addr=0x1D, reg=210, data=ord("K"))
        assert w >> 24 == 0x06
        assert (w >> 23) & 1 == 1
        assert (w >> 16) & 0x7F == 0x1D
        assert (w >> 8) & 0xFF == 210
        assert w & 0xFF == ord("K")
        with pytest.raises(ValueError):
            p.i2c_word(write=True, i2c_addr=0x1D, reg=270, data=0)

    def test_ep6_24bit_iq_roundtrip(self):
        n = np.arange(126)
        iq = (0.5 * np.exp(2j * np.pi * n / 32)).astype(np.complex64)
        iq[0] = -0.999 - 0.25j
        pkt = p.build_ep6_packet_for_test(9, iq)
        ep6 = p.parse_ep6_packet(pkt)
        assert ep6 is not None and ep6.seq == 9
        assert len(ep6.iq) == 126
        assert np.max(np.abs(ep6.iq - iq)) < 1e-6   # 24 bit Auflösung

    def test_telemetry_parsing(self):
        t = p.Telemetry()
        # RADDR 1 (C0 = 1<<3), PTT=1, Dot=1; temp 0x0123, fwd 0x0456
        t.update(p.parse_c0((0x01 << 3) | 0x05, (0x0123 << 16) | 0x0456))
        assert t.ptt_in and t.key_in
        assert t.temperature_raw == 0x0123 and t.fwd_power_raw == 0x0456
        t.update(p.parse_c0(0x02 << 3, (0x0200 << 16) | 0x0010))
        assert t.rev_power_raw == 0x0200 and t.pa_current_raw == 0x0010


def make_client():
    sock = FakeSocket()
    c = HL2Client("192.0.2.1", sock=sock, keepalive_s=10)
    return c, sock


class TestClient:
    def test_persistent_registers_cycle(self):
        c, sock = make_client()
        seen = set()
        for _ in range(6):
            for c0, _d in frames(c.build_next_packet()):
                seen.add((c0 >> 1) & 0x3F)
        assert {0x00, 0x01, 0x02, 0x09, 0x10, 0x17} <= seen

    def test_ptt_only_sets_mox_bit(self):
        c, _ = make_client()
        c.set_register(0x00, p.general_word(oc_bits=0x48))
        before = c.get_register(0x00)
        c.set_mox(True)
        for _ in range(4):
            for c0, d in frames(c.build_next_packet()):
                assert c0 & 1 == 1
                if (c0 >> 1) & 0x3F == 0:
                    assert d == before        # G3: Wort 0x00 bleibt erhalten

    def test_i2c_write_with_ack(self):
        c, sock = make_client()
        c._running = True
        result = {}

        def worker():
            c.i2c_write(i2c_addr=0x1D, reg=210, data=0x41)
            result["ok"] = True

        th = threading.Thread(target=worker)
        th.start()
        # Warten, bis ein RQST-Frame gesendet wurde, dann ACK simulieren
        reqs = []
        for _ in range(500):
            reqs = [(c0, d) for pkt in list(sock.sent) for c0, d in frames(pkt) if c0 & 0x80]
            if reqs:
                break
            threading.Event().wait(0.001)
        assert reqs, "kein RQST-Frame gesendet"
        c0, d = reqs[0]
        assert (c0 >> 1) & 0x3F == 0x3D
        assert d == p.i2c_word(write=True, i2c_addr=0x1D, reg=210, data=0x41)
        ack_c0 = 0x80 | (0x3D << 1)
        c.handle_packet(p.build_ep6_packet_for_test(1, np.zeros(126), ((ack_c0, d), (0, 0))))
        th.join(1)
        assert result.get("ok")

    def test_request_fails_fast_when_stopped(self):
        c, _ = make_client()
        with pytest.raises(ConnectionError):
            c.i2c_read(i2c_addr=0x1D, reg=200)

    def test_tx_samples_when_mox(self):
        c, _ = make_client()
        c.set_tx_source(lambda n: np.full(n, 0.5 + 0j, dtype=np.complex64))
        c.set_mox(True)
        pkt = c.build_next_packet()
        sample = pkt[8 + 8: 8 + 16]  # erstes Sample des ersten Frames
        l, r, i, q = struct.unpack(">hhhh", sample)
        assert i == 16384 and q == 0


class TestControl:
    def test_frequency_sets_oc_bits_in_addr0(self):
        c, _ = make_client()
        hl2 = HL2Control("192.0.2.1", 1024, client=c)
        hl2.set_frequency_hz(14_060_000)
        w = c.get_register(0x00)
        assert (w >> 17) & 0x7F == 0x48       # 20 m LPF + HPF
        assert c.get_register(0x01) == 14_060_000
        assert c.get_register(0x02) == 14_060_000

    def test_6m_tx_blocked(self):
        c, _ = make_client()
        hl2 = HL2Control("192.0.2.1", 1024, client=c)
        hl2.set_frequency_hz(50_100_000)
        with pytest.raises(PermissionError):
            hl2.set_ptt(True)

    def test_swr_trip(self):
        c, _ = make_client()
        hl2 = HL2Control("192.0.2.1", 1024, client=c, trip_count=2)
        tripped = []
        hl2.add_trip_callback(tripped.append)
        hl2.set_ptt(True)
        t = c.telemetry
        t.fwd_power_raw, t.rev_power_raw = 2000, 1600   # SWR 9
        hl2._on_telemetry(t)
        assert not hl2.swr_tripped
        hl2._on_telemetry(t)
        assert hl2.swr_tripped and tripped
        assert c.mox is False
        assert (c.get_register(0x09) >> 28) == 0      # Drive auf 0
        with pytest.raises(PermissionError):
            hl2.set_ptt(True)
        hl2.reset_swr_trip()
        hl2.set_ptt(True)

    def test_swr_trip_on_cn4_keying_without_mox(self):
        """CW über den Pico setzt kein MOX; der Schutz greift über das PTT-Bit des HL2."""
        c, _ = make_client()
        hl2 = HL2Control("192.0.2.1", 1024, client=c, trip_count=1)
        t = c.telemetry
        t.ptt_in = True
        t.fwd_power_raw, t.rev_power_raw = 2000, 1800
        hl2._on_telemetry(t)
        assert hl2.swr_tripped


class TestIOBoard:
    def test_read_cw_status_three_reads(self):
        class T:
            def i2c_read(self, *, i2c_addr, reg, bus=2):
                return bytes([reg - 200, reg - 199, reg - 198, reg - 197])

            def i2c_write(self, **kw):
                pass

        st = IOBoard(T()).read_cw_status()
        assert st.cmd == 0 and st.wpm == 2 and st.ptt_tail_ms == 4 and st.error_code == 7
        assert st.progress == 8 and st.fifo_level == 9
