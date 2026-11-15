"""Ende-zu-Ende über echtes UDP (Loopback): HL2Client -> Fake-HL2 -> Fake-Pico-Register.

Der Fake-HL2 versteht das Protocol-1-Framing, antwortet auf RQST mit ACK und
führt I2C2-Befehle (C&C 0x3D) gegen eine Registerbank aus, wie der Pico.
"""
import socket
import struct
import threading
import time

import numpy as np
import pytest

from sota_cw import hl2_protocol as p
from sota_cw.cw_jobs import CWJobManager
from sota_cw.hardware.hl2_io_board import HL2IOBoard
from sota_cw.hl2_client import HL2Client
from sota_cw.hl2_control import HL2Control
from sota_cw.ioboard import CW_CMD_START, CW_REG_BASE, REG_OFF_FIFO_DATA, KEYER_MAGIC


class FakeHL2(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.settimeout(0.05)
        self.port = self.sock.getsockname()[1]
        self.host = None
        self.streaming = False
        self.running = True
        self.regs = bytearray(256)
        self.regs[CW_REG_BASE + 15] = KEYER_MAGIC
        self.regs[CW_REG_BASE + 14] = 1
        self.fifo = []
        self.cc = {}
        self.pending_acks = []
        self.seq = 0
        self.fwd, self.rev = 0, 0
        self.ptt = False

    def _i2c(self, word):
        cookie = word >> 24
        addr = (word >> 16) & 0x7F
        reg = (word >> 8) & 0xFF
        data = word & 0xFF
        if addr != 0x1D:
            return word
        if cookie == 0x06:
            if reg == CW_REG_BASE + REG_OFF_FIFO_DATA:
                self.fifo.append(data)
            else:
                self.regs[reg] = data
            return word
        return int.from_bytes(bytes(self.regs[(reg + i) & 0xFF] for i in range(4)), "big")

    def handle(self, pkt):
        if pkt[:3] == b"\xef\xfe\x04":
            self.streaming = bool(pkt[3] & 1)
            return
        if not pkt.startswith(p.EP2_HEADER):
            return
        for k in range(2):
            f = pkt[8 + k * 512: 8 + (k + 1) * 512]
            assert f[:3] == p.SYNC
            c0 = f[3]
            addr = (c0 >> 1) & 0x3F
            data = struct.unpack(">I", f[4:8])[0]
            self.cc[addr] = data
            if addr == 0x3D:
                data = self._i2c(data)
            if c0 & 0x80:
                self.pending_acks.append((0x80 | (addr << 1) | int(self.ptt), data))

    def run(self):
        last = time.monotonic()
        while self.running:
            try:
                pkt, addr = self.sock.recvfrom(2048)
                self.host = addr
                self.handle(pkt)
            except socket.timeout:
                pass
            now = time.monotonic()
            if self.streaming and self.host and now - last > 0.0026:
                last = now
                frames = []
                for _ in range(2):
                    if self.pending_acks:
                        frames.append(self.pending_acks.pop(0))
                    else:
                        frames.append(((0x01 << 3) | int(self.ptt), self.fwd & 0xFFFF))
                        frames[-1] = frames[-1] if self.seq % 2 else ((0x02 << 3) | int(self.ptt), (self.rev << 16))
                pkt = p.build_ep6_packet_for_test(self.seq, np.zeros(126), (frames[0], frames[1]))
                self.seq += 1
                self.sock.sendto(pkt, self.host)


@pytest.fixture
def rig():
    hl2 = FakeHL2()
    hl2.start()
    client = HL2Client("127.0.0.1", hl2.port, interface_ip="127.0.0.1")
    io = HL2IOBoard(client)
    ctrl = HL2Control("127.0.0.1", hl2.port, client=client, io_board=io, trip_count=2)
    ctrl.start()
    yield hl2, client, io, ctrl
    ctrl.stop()
    hl2.running = False
    hl2.join(1)


def test_cw_job_reaches_pico_registers(rig):
    hl2, client, io, ctrl = rig
    mgr = CWJobManager(io, hl2=ctrl)
    mgr.start_job("cq sota de hb9xyz k", 22)
    assert bytes(hl2.fifo).decode() == "CQ SOTA DE HB9XYZ K"
    assert hl2.regs[CW_REG_BASE + 2] == 22
    assert hl2.regs[CW_REG_BASE] == CW_CMD_START
    assert io.probe_keyer() == (True, 1)
    mgr.abort_job()


def test_frequency_and_filters_reach_hl2(rig):
    hl2, client, io, ctrl = rig
    ctrl.set_frequency_hz(10_116_000)

    def io_freq():
        f = 0
        for r in range(5):
            f = (f << 8) | hl2.regs[r]
        return f

    deadline = time.monotonic() + 2
    while io_freq() != 10_116_000 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert hl2.cc[0x01] == 10_116_000 and hl2.cc[0x02] == 10_116_000
    assert (hl2.cc[0x00] >> 17) & 0x7F == 0x48
    assert io_freq() == 10_116_000


def test_swr_trip_aborts_keyer(rig):
    hl2, client, io, ctrl = rig
    mgr = CWJobManager(io, hl2=ctrl)
    ctrl.add_trip_callback(lambda r: mgr.abort_job())
    mgr.start_job("TEST", 20)
    hl2.ptt = True
    hl2.fwd, hl2.rev = 2000, 1800
    deadline = time.monotonic() + 2
    while not ctrl.swr_tripped and time.monotonic() < deadline:
        time.sleep(0.01)
    assert ctrl.swr_tripped
    time.sleep(0.2)
    assert hl2.regs[CW_REG_BASE] == 2  # ABORT im Pico
    assert (hl2.cc[0x09] >> 28) == 0   # Drive 0
