"""Hermes-Lite 2 / openHPSDR Protocol 1 framing (pure functions, no I/O).

Quellen:
- HL2 Protocol Wiki: https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol
- openHPSDR Protocol 1 (Metis/USB frame format)

Paketformat (UDP, Port 1024):

    Host -> HL2 (EP2):  EF FE 01 02 <seq u32 BE> <frame 512> <frame 512>
    HL2 -> Host (EP6):  EF FE 01 06 <seq u32 BE> <frame 512> <frame 512>

Jeder 512-Byte-Frame beginnt mit ``7F 7F 7F`` und C0..C4. Danach folgen
Samples:

- EP2: 63 x (L16, R16, I16, Q16), alle big-endian, signed.
- EP6: pro Sample N x (I24, Q24) + Mic16, big-endian, signed.
  Bei N=1 Empfänger 63 Samples pro Frame (8 Byte pro Sample).

C0 (Host -> HL2): Bit 7 = RQST, Bits 6:1 = Adresse, Bit 0 = MOX.
C1..C4 = DATA[31:0] (C1 = MSB).

C0 (HL2 -> Host, ACK=0): Bits 6:3 = RADDR[3:0], Bit 2 = Dot (CN4 Tip),
Bit 1 = Dash (immer 0), Bit 0 = PTT.
C0 (HL2 -> Host, ACK=1): Bits 6:1 = RADDR[5:0], Bit 0 = PTT.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

HL2_PORT = 1024

SYNC = b"\x7f\x7f\x7f"
FRAME_LEN = 512
SAMPLES_PER_FRAME_TX = 63
SAMPLES_PER_PACKET_TX = 2 * SAMPLES_PER_FRAME_TX  # 126

EP2_HEADER = b"\xef\xfe\x01\x02"
EP6_HEADER = b"\xef\xfe\x01\x06"
DISCOVERY_REQUEST = b"\xef\xfe\x02" + b"\x00" * 60

# --- C&C-Adressen (HL2 Wiki) -------------------------------------------------
ADDR_GENERAL = 0x00     # Samplerate, OC-Ausgänge, Anzahl RX, Duplex
ADDR_TX_NCO = 0x01
ADDR_RX1_NCO = 0x02
ADDR_TX_DRIVE = 0x09    # Drive-Level, PA, Tune
ADDR_CWX = 0x0F         # Bit 24: CWX enable (nicht genutzt, Keying läuft über Pico)
ADDR_CW_HANG = 0x10     # CW-Hang-Zeit
ADDR_PTT_HANG = 0x17    # PTT-Hang, TX-Puffer-Latenz
ADDR_WATCHDOG = 0x39
ADDR_I2C1 = 0x3C
ADDR_I2C2 = 0x3D
ADDR_ERROR = 0x3F

I2C_COOKIE_WRITE = 0x06
I2C_COOKIE_READ = 0x07

SAMPLE_RATES = {48000: 0b00, 96000: 0b01, 192000: 0b10, 384000: 0b11}


# --- Metis-Steuerpakete --------------------------------------------------------

def metis_start_packet(*, iq: bool = True, wideband: bool = False, disable_watchdog: bool = False) -> bytes:
    cmd = (0x01 if iq else 0) | (0x02 if wideband else 0) | (0x80 if disable_watchdog else 0)
    return b"\xef\xfe\x04" + bytes([cmd]) + b"\x00" * 60


def metis_stop_packet(*, disable_watchdog: bool = False) -> bytes:
    return b"\xef\xfe\x04" + bytes([0x80 if disable_watchdog else 0]) + b"\x00" * 60


# --- C&C-Datenworte ------------------------------------------------------------

def general_word(
    *,
    sample_rate: int = 48000,
    oc_bits: int = 0,
    n_receivers: int = 1,
    duplex: bool = True,
) -> int:
    """DATA-Wort für Adresse 0x00.

    [25:24] Samplerate, [23:17] Open-Collector-Ausgänge (N2ADR-Filter),
    [6:3] Anzahl Empfänger - 1, [2] Duplex.
    """
    if sample_rate not in SAMPLE_RATES:
        raise ValueError(f"unsupported sample rate {sample_rate}")
    if not 1 <= n_receivers <= 12:
        raise ValueError("n_receivers must be 1..12")
    word = SAMPLE_RATES[sample_rate] << 24
    word |= (oc_bits & 0x7F) << 17
    word |= ((n_receivers - 1) & 0x0F) << 3
    if duplex:
        word |= 1 << 2
    return word


def tx_drive_word(*, drive_level: int, pa_enable: bool = True, tune: bool = False) -> int:
    """DATA-Wort für Adresse 0x09. drive_level 0..15 ([31:28]), PA [19], Tune [20]."""
    lvl = max(0, min(15, int(drive_level)))
    word = (lvl << 4) << 24
    if pa_enable:
        word |= 1 << 19
    if tune:
        word |= 1 << 20
    return word


def cw_hang_word(hang_ms: int) -> int:
    """DATA-Wort für Adresse 0x10: Hang-Zeit [31:24] = ms[9:2], [17:16] = ms[1:0]."""
    ms = max(0, min(1023, int(hang_ms)))
    return ((ms >> 2) << 24) | ((ms & 0x3) << 16)


def ptt_hang_word(*, ptt_hang_ms: int = 12, tx_latency_ms: int = 20) -> int:
    """DATA-Wort für Adresse 0x17: [12:8] PTT-Hang, [6:0] TX-Latenz."""
    return ((int(ptt_hang_ms) & 0x1F) << 8) | (int(tx_latency_ms) & 0x7F)


def i2c_word(*, write: bool, i2c_addr: int, reg: int, data: int = 0, stop: bool = True) -> int:
    """DATA-Wort für Adresse 0x3C/0x3D (I2C1/I2C2).

    [31:24] Cookie (0x06 Write, 0x07 Read), [23] Stop, [22:16] I2C-Adresse,
    [15:8] Registernummer (8 bit), [7:0] Datenbyte.
    """
    if not 0 <= reg <= 0xFF:
        raise ValueError(f"I2C register {reg} out of range 0..255")
    if not 0 <= data <= 0xFF:
        raise ValueError(f"I2C data {data} out of range 0..255")
    cookie = I2C_COOKIE_WRITE if write else I2C_COOKIE_READ
    return (cookie << 24) | ((1 if stop else 0) << 23) | ((i2c_addr & 0x7F) << 16) | ((reg & 0xFF) << 8) | (data & 0xFF)


def c0_byte(*, addr: int, mox: bool, rqst: bool) -> int:
    return ((1 if rqst else 0) << 7) | ((addr & 0x3F) << 1) | (1 if mox else 0)


@dataclass(frozen=True)
class CCWrite:
    addr: int
    data: int
    rqst: bool = False


# --- EP2 (Host -> HL2) ----------------------------------------------------------

def _frame_ep2(cc: CCWrite, mox: bool, samples: bytes) -> bytes:
    hdr = SYNC + bytes([c0_byte(addr=cc.addr, mox=mox, rqst=cc.rqst)]) + struct.pack(">I", cc.data & 0xFFFFFFFF)
    frame = hdr + samples
    if len(frame) != FRAME_LEN:
        raise AssertionError(f"EP2 frame length {len(frame)} != 512")
    return frame


def tx_samples_to_bytes(iq: Optional[np.ndarray], audio: Optional[np.ndarray] = None) -> bytes:
    """126 TX-Samples (complex, |x|<=1) in 2 x 504 Byte Sampledaten umwandeln.

    Layout pro Sample: L16, R16, I16, Q16 (big-endian).
    """
    n = SAMPLES_PER_PACKET_TX
    buf = np.zeros((n, 4), dtype=">i2")
    if iq is not None:
        iq = np.asarray(iq)
        if len(iq) != n:
            raise ValueError(f"need {n} TX samples, got {len(iq)}")
        buf[:, 2] = np.clip(np.round(iq.real * 32767.0), -32767, 32767).astype(np.int16)
        buf[:, 3] = np.clip(np.round(iq.imag * 32767.0), -32767, 32767).astype(np.int16)
    if audio is not None:
        a = np.clip(np.round(np.asarray(audio) * 32767.0), -32767, 32767).astype(np.int16)
        buf[:, 0] = a
        buf[:, 1] = a
    return buf.tobytes()


def build_ep2_packet(seq: int, cc1: CCWrite, cc2: CCWrite, *, mox: bool, sample_bytes: Optional[bytes] = None) -> bytes:
    """Vollständiges 1032-Byte-EP2-Paket mit zwei C&C-Frames bauen."""
    if sample_bytes is None:
        sample_bytes = bytes(2 * SAMPLES_PER_FRAME_TX * 8)
    half = SAMPLES_PER_FRAME_TX * 8
    return (
        EP2_HEADER
        + struct.pack(">I", seq & 0xFFFFFFFF)
        + _frame_ep2(cc1, mox, sample_bytes[:half])
        + _frame_ep2(cc2, mox, sample_bytes[half:2 * half])
    )


# --- EP6 (HL2 -> Host) ----------------------------------------------------------

@dataclass
class RxFrameInfo:
    ack: bool
    raddr: int
    ptt: bool
    dot: bool
    data: int


@dataclass
class EP6Packet:
    seq: int
    frames: list[RxFrameInfo] = field(default_factory=list)
    iq: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.complex64))  # RX1, normiert auf +-1
    mic: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int16))


def parse_c0(c0: int, data: int) -> RxFrameInfo:
    ack = bool(c0 & 0x80)
    if ack:
        raddr = (c0 >> 1) & 0x3F
        return RxFrameInfo(ack=True, raddr=raddr, ptt=bool(c0 & 1), dot=False, data=data)
    raddr = (c0 >> 3) & 0x0F
    return RxFrameInfo(ack=False, raddr=raddr, ptt=bool(c0 & 1), dot=bool(c0 & 0x04), data=data)


def samples_per_frame_rx(n_receivers: int) -> int:
    return (FRAME_LEN - 8) // (6 * n_receivers + 2)


def _int24_be(raw: np.ndarray) -> np.ndarray:
    """(n, 3) uint8 -> int32, vorzeichenrichtig."""
    v = (raw[:, 0].astype(np.int32) << 16) | (raw[:, 1].astype(np.int32) << 8) | raw[:, 2].astype(np.int32)
    return np.where(v & 0x800000, v - 0x1000000, v)


def parse_rx_frame_samples(frame: bytes, n_receivers: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Samples eines 512-Byte-EP6-Frames: (iq RX1 complex64 normiert, mic int16)."""
    spf = samples_per_frame_rx(n_receivers)
    stride = 6 * n_receivers + 2
    body = np.frombuffer(frame, dtype=np.uint8, count=spf * stride, offset=8).reshape(spf, stride)
    i = _int24_be(body[:, 0:3])
    q = _int24_be(body[:, 3:6])
    mic_raw = body[:, 6 * n_receivers: 6 * n_receivers + 2]
    mic = ((mic_raw[:, 0].astype(np.int16) << 8) | mic_raw[:, 1].astype(np.int16)).astype(np.int16)
    scale = 1.0 / 8388608.0
    iq = (i.astype(np.float32) * scale + 1j * (q.astype(np.float32) * scale)).astype(np.complex64)
    return iq, mic


def parse_ep6_packet(pkt: bytes, n_receivers: int = 1) -> Optional[EP6Packet]:
    """EP6-Paket zerlegen. Gibt None zurück, wenn es kein gültiges EP6-Paket ist."""
    if len(pkt) < 8 + 2 * FRAME_LEN or not pkt.startswith(EP6_HEADER):
        return None
    seq = struct.unpack(">I", pkt[4:8])[0]
    out = EP6Packet(seq=seq)
    iqs = []
    mics = []
    for k in range(2):
        frame = pkt[8 + k * FRAME_LEN: 8 + (k + 1) * FRAME_LEN]
        if frame[:3] != SYNC:
            return None
        c0 = frame[3]
        data = struct.unpack(">I", frame[4:8])[0]
        out.frames.append(parse_c0(c0, data))
        iq, mic = parse_rx_frame_samples(frame, n_receivers)
        iqs.append(iq)
        mics.append(mic)
    out.iq = np.concatenate(iqs)
    out.mic = np.concatenate(mics)
    return out


def build_ep6_packet_for_test(
    seq: int,
    iq: np.ndarray,
    c0_c4: tuple[tuple[int, int], tuple[int, int]] = ((0, 0), (0, 0)),
) -> bytes:
    """Hilfsfunktion für Tests/Replay: EP6-Paket mit 1 Empfänger aus 126 Samples."""
    iq = np.asarray(iq)
    assert len(iq) == 126
    pkt = bytearray(EP6_HEADER + struct.pack(">I", seq))
    for k in range(2):
        c0, data = c0_c4[k]
        frame = bytearray(SYNC + bytes([c0]) + struct.pack(">I", data))
        for s in iq[k * 63:(k + 1) * 63]:
            for comp in (s.real, s.imag):
                v = int(round(float(comp) * 8388607)) & 0xFFFFFF
                frame += bytes([(v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF])
            frame += b"\x00\x00"
        frame += bytes(FRAME_LEN - len(frame))
        pkt += frame
    return bytes(pkt)


@dataclass
class Telemetry:
    """Aus EP6-C&C-Antworten (ACK=0) gesammelte Telemetrie."""
    ptt_in: bool = False
    key_in: bool = False
    adc_overload: bool = False
    tx_inhibited: bool = False
    firmware_version: int = 0
    temperature_raw: int = 0
    fwd_power_raw: int = 0
    rev_power_raw: int = 0
    pa_current_raw: int = 0
    fifo_count: int = 0
    updates: int = 0

    def update(self, info: RxFrameInfo) -> None:
        self.ptt_in = info.ptt
        if info.ack:
            return
        self.key_in = info.dot
        d = info.data
        if info.raddr == 0x00:
            self.tx_inhibited = not bool(d & (1 << 25))  # active low
            self.adc_overload = bool(d & (1 << 24))
            self.fifo_count = (d >> 8) & 0x7F
            self.firmware_version = d & 0xFF
        elif info.raddr == 0x01:
            self.temperature_raw = (d >> 16) & 0xFFFF
            self.fwd_power_raw = d & 0xFFFF
        elif info.raddr == 0x02:
            self.rev_power_raw = (d >> 16) & 0xFFFF
            self.pa_current_raw = d & 0xFFFF
        self.updates += 1
