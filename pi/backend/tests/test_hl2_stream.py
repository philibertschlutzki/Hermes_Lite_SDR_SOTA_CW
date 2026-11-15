"""
Unit tests for HL2 Stream DSP

Tests DSP functions with synthetic IQ vectors.
"""
import pytest
import numpy as np
from sota_cw.hl2_stream import FIRFilter


class TestFIRFilter:
    """Test FIR filter DSP."""
    
    def test_filter_creation(self):
        """FIR filter should be created with correct parameters."""
        fir = FIRFilter(cutoff_hz=1000, sample_rate=48000, num_taps=101)
        assert len(fir.taps) == 101
        assert len(fir.state) == 100
    
    def test_filter_taps_normalized(self):
        """Filter taps should sum to approximately 1.0."""
        fir = FIRFilter(cutoff_hz=1000, sample_rate=48000, num_taps=101)
        assert abs(np.sum(fir.taps) - 1.0) < 0.01
    
    def test_filter_dc_pass(self):
        """DC signal (all ones) should pass through lowpass filter."""
        fir = FIRFilter(cutoff_hz=1000, sample_rate=48000, num_taps=51)
        dc_signal = np.ones(100, dtype=np.complex64)
        filtered = fir.filter(dc_signal)
        # DC should be preserved in steady state (check last samples)
        # First samples have transient response
        assert np.abs(np.mean(filtered[-20:]) - 1.0) < 0.01
    
    def test_filter_high_freq_reject(self):
        """High frequency signal should be attenuated."""
        fir = FIRFilter(cutoff_hz=1000, sample_rate=48000, num_taps=101)
        # Create high frequency signal (10 kHz)
        t = np.arange(100) / 48000.0
        high_freq = np.exp(2j * np.pi * 10000 * t).astype(np.complex64)
        filtered = fir.filter(high_freq)
        # High freq should be attenuated significantly
        input_power = np.mean(np.abs(high_freq)**2)
        output_power = np.mean(np.abs(filtered)**2)
        attenuation_db = 10 * np.log10(output_power / input_power)
        assert attenuation_db < -10  # At least 10 dB attenuation
    
    def test_filter_passband_preserve(self):
        """Signal in passband should be preserved."""
        fir = FIRFilter(cutoff_hz=1000, sample_rate=48000, num_taps=51)
        # Create signal at 500 Hz (in passband)
        t = np.arange(200) / 48000.0
        signal = np.exp(2j * np.pi * 500 * t).astype(np.complex64)
        filtered = fir.filter(signal)
        # Signal should be preserved (with some edge effects)
        # Check middle portion to avoid edge effects
        input_power = np.mean(np.abs(signal[50:150])**2)
        output_power = np.mean(np.abs(filtered[50:150])**2)
        attenuation_db = 10 * np.log10(output_power / input_power)
        assert attenuation_db > -3  # Less than 3 dB attenuation
    
    def test_filter_state_continuity(self):
        """Filter should maintain state across chunks."""
        fir = FIRFilter(cutoff_hz=1000, sample_rate=48000, num_taps=51)
        # Process two chunks
        chunk1 = np.ones(50, dtype=np.complex64)
        chunk2 = np.ones(50, dtype=np.complex64)
        
        out1 = fir.filter(chunk1)
        out2 = fir.filter(chunk2)
        
        # Output should be continuous (no discontinuity)
        # Last sample of out1 and first sample of out2 should be similar
        assert np.abs(out1[-1] - out2[0]) < 0.5


class TestSyntheticIQ:
    """Test with synthetic IQ signals."""
    
    def test_cw_tone_detection(self):
        """Should detect CW tone in IQ stream."""
        # Create synthetic CW tone at 600 Hz
        sample_rate = 48000
        duration = 0.1  # 100ms
        cw_pitch = 600
        
        t = np.arange(int(sample_rate * duration)) / sample_rate
        iq = np.exp(2j * np.pi * cw_pitch * t).astype(np.complex64)
        
        # Filter around CW pitch
        fir = FIRFilter(cutoff_hz=1000, sample_rate=sample_rate, num_taps=101)
        filtered = fir.filter(iq)
        
        # Check that signal passes through
        # (In real demod, would extract envelope and detect keying)
        output_power = np.mean(np.abs(filtered)**2)
        assert output_power > 0.5  # Signal present
    
    def test_noise_rejection(self):
        """Should reject noise outside filter passband."""
        sample_rate = 48000
        # White noise
        noise = (np.random.randn(1000) + 1j * np.random.randn(1000)).astype(np.complex64)
        noise = noise / np.sqrt(2)  # Normalize
        
        fir = FIRFilter(cutoff_hz=500, sample_rate=sample_rate, num_taps=101)
        filtered = fir.filter(noise)
        
        # Filtered noise should have less power (bandwidth reduction)
        input_power = np.mean(np.abs(noise)**2)
        output_power = np.mean(np.abs(filtered)**2)
        
        # Power should be reduced due to bandwidth limitation
        assert output_power < input_power


class TestDemodAndModulator:
    def test_usb_demod_passes_upper_sideband(self):
        from sota_cw.dsp import Demodulator
        fs = 48000
        t = np.arange(4800) / fs
        usb = np.exp(2j * np.pi * 1000 * t).astype(np.complex64) * 0.1
        lsb = np.exp(-2j * np.pi * 1000 * t).astype(np.complex64) * 0.1
        d = Demodulator("USB", agc=False)
        p_usb = np.mean(d.process(usb)[1000:] ** 2)
        d = Demodulator("USB", agc=False)
        p_lsb = np.mean(d.process(lsb)[1000:] ** 2)
        assert 10 * np.log10(p_usb / p_lsb) > 30

    def test_cw_demod_tone_at_pitch(self):
        from sota_cw.dsp import Demodulator
        iq = np.full(9600, 0.1 + 0j, dtype=np.complex64)  # Träger auf der Dial-Frequenz
        audio = Demodulator("CWU", cw_pitch_hz=600, agc=False).process(iq)[2000:]
        spec = np.abs(np.fft.rfft(audio))
        f = np.fft.rfftfreq(len(audio), 1 / 48000)
        assert abs(f[np.argmax(spec)] - 600) < 10

    def test_ssb_modulator_single_sideband(self):
        from sota_cw.dsp import SSBModulator
        t = np.arange(9600) / 48000
        audio = 0.5 * np.sin(2 * np.pi * 1500 * t)
        iq = SSBModulator(sideband="USB").process(audio)[1000:]
        spec = np.abs(np.fft.fft(iq))
        f = np.fft.fftfreq(len(iq), 1 / 48000)
        pos = spec[np.argmin(np.abs(f - 1500))]
        neg = spec[np.argmin(np.abs(f + 1500))]
        assert 20 * np.log10(pos / neg) > 30
        assert np.max(np.abs(iq)) <= 1.0

    def test_resampler_rate(self):
        from sota_cw.dsp import Resampler
        r = Resampler(48000, 22050)
        total = sum(len(r.process(np.zeros(1260))) for _ in range(100))
        assert abs(total - 126000 * 22050 / 48000) < 3
