"""Real-time EEG signal processing: filtering, band power extraction, artifact rejection."""

import numpy as np
from scipy import signal as sp_signal
from scipy.fft import fft, fftfreq
import logging
from collections import deque
from dataclasses import dataclass, field

log = logging.getLogger('BCI.Signal')

# Standard frequency bands
BANDS = {
    'delta': (0.5, 4),
    'theta': (4, 8),
    'alpha': (8, 13),
    'beta': (13, 30),
    'gamma': (30, 50),
}

BAND_NAMES = ['delta', 'theta', 'alpha', 'beta', 'gamma']


@dataclass
class BrainState:
    """Real-time cognitive state derived from actual EEG."""
    band_powers: dict = field(default_factory=lambda: {b: 0.0 for b in BAND_NAMES})
    alpha_theta_ratio: float = 1.0
    beta_alpha_ratio: float = 1.0
    delta_theta_ratio: float = 1.0
    gamma_beta_ratio: float = 1.0
    attention: float = 0.5
    engagement: float = 0.5
    load: float = 0.3
    valence: float = 0.5
    coherence: float = 0.5
    fractal_speed: float = 1.0
    fractal_complexity: float = 2.5
    dominant_band: str = 'alpha'
    asymmetry: float = 0.0  # left-right frontal asymmetry
    hr: float = 70.0  # heart rate from PPG if available
    blink_rate: float = 0.0
    timestamp: float = 0.0

    def to_dict(self):
        return {
            'attention': round(self.attention, 4),
            'engagement': round(self.engagement, 4),
            'load': round(self.load, 4),
            'valence': round(self.valence, 4),
            'coherence': round(self.coherence, 4),
            'fractal_dimension': round(self.fractal_complexity, 4),
            'state_name': self.dominant_band,
            'phase': self.dominant_band,
            'color': self._color(),
            'narrative': '',
            'band_powers': {k: round(v, 6) for k, v in self.band_powers.items()},
            'alpha_theta_ratio': round(self.alpha_theta_ratio, 4),
            'beta_alpha_ratio': round(self.beta_alpha_ratio, 4),
        }

    def _color(self):
        palette = {
            'delta': '#4488FF', 'theta': '#00FF88',
            'alpha': '#00F0FF', 'beta': '#FF0055',
            'gamma': '#FF4400'
        }
        return palette.get(self.dominant_band, '#9933FF')


class SignalProcessor:
    """Real-time EEG signal processor with overlapping FFT windows."""

    def __init__(self, sampling_rate=256, n_channels=4, window_seconds=2):
        self.fs = sampling_rate
        self.n_channels = n_channels
        self.window_size = int(sampling_rate * window_seconds)
        self.hop_size = self.window_size // 4  # 75% overlap
        self._buffer = np.zeros((n_channels, self.window_size))
        self._write_idx = 0
        self._total = 0
        self.state = BrainState()
        self.state.timestamp = 0

        # Precompute filter coefficients for each band
        self._filters = {}
        for name, (lo, hi) in BANDS.items():
            if lo <= 0:
                lo = 0.1
            nyq = self.fs / 2
            if hi >= nyq:
                hi = nyq - 0.5
            order = 4
            sos = sp_signal.butter(order, [lo / nyq, hi / nyq], btype='band', output='sos')
            self._filters[name] = sos

        # Smoothing
        self._smoothed_powers = {b: 0.0 for b in BAND_NAMES}
        self._smooth_factor = 0.3

        # Blink detection
        self._blink_buffer = deque(maxlen=int(sampling_rate * 2))
        self._last_blink_time = 0

        log.info(f"SignalProcessor: {n_channels}ch @ {self.fs}Hz, {window_seconds}s window")

    def feed(self, samples):
        """Feed new EEG samples. samples: (n_channels, n_samples)"""
        n = samples.shape[1]
        if self._write_idx + n >= self.window_size:
            # Process this window
            space = self.window_size - self._write_idx
            self._buffer[:, self._write_idx:self._write_idx + space] = samples[:, :space]
            self._process_window(self._buffer.copy())
            # Reset with remainder
            remainder = n - space
            if remainder > 0:
                self._buffer[:, :remainder] = samples[:, space:]
                self._write_idx = remainder
            else:
                self._write_idx = 0
        else:
            self._buffer[:, self._write_idx:self._write_idx + n] = samples
            self._write_idx += n

        self._total += n
        self._detect_blinks(samples)

    def _process_window(self, window):
        """Process a full window of EEG data."""
        t0 = time.time()
        n = window.shape[1]
        state = BrainState()
        state.timestamp = time.time()

        # Apply Hanning window to reduce spectral leakage
        win = np.hanning(n)
        window_win = window * win[np.newaxis, :]

        # Compute band powers via FFT
        for ch in range(self.n_channels):
            yf = fft(window_win[ch, :])
            xf = fftfreq(n, 1 / self.fs)
            pos_mask = xf >= 0
            xf = xf[pos_mask]
            mag = np.abs(yf[pos_mask]) / n
            mag = mag ** 2  # power

            for band_name, (lo, hi) in BANDS.items():
                band_mask = (xf >= lo) & (xf < hi)
                power = mag[band_mask].sum() if band_mask.any() else 1e-12
                self._smoothed_powers[band_name] = (
                    self._smooth_factor * power +
                    (1 - self._smooth_factor) * self._smoothed_powers[band_name]
                )

        # Average powers across channels
        state.band_powers = dict(self._smoothed_powers)

        # Compute ratios
        eps = 1e-10
        p = state.band_powers
        state.alpha_theta_ratio = p.get('alpha', eps) / (p.get('theta', eps) + eps)
        state.beta_alpha_ratio = p.get('beta', eps) / (p.get('alpha', eps) + eps)
        state.delta_theta_ratio = p.get('delta', eps) / (p.get('theta', eps) + eps)
        state.gamma_beta_ratio = p.get('gamma', eps) / (p.get('beta', eps) + eps)

        # Derive cognitive metrics from real EEG bands
        # Alpha/Theta ratio: higher = relaxed, lower = drowsy/focused
        # Beta/Alpha ratio: higher = active/engaged
        # Gamma/Beta: higher = complex processing
        # Delta: higher = deep sleep / fatigue

        at = np.clip(state.alpha_theta_ratio, 0, 5)
        ba = np.clip(state.beta_alpha_ratio, 0, 5)
        gb = np.clip(state.gamma_beta_ratio, 0, 5)
        dt = np.clip(state.delta_theta_ratio, 0, 5)
        delta_p = p.get('delta', 0)
        theta_p = p.get('theta', 0)
        alpha_p = p.get('alpha', 0)
        beta_p = p.get('beta', 0)
        gamma_p = p.get('gamma', 0)

        # Attention: Beta power relative to Theta+Alpha
        state.attention = np.clip(beta_p / max(theta_p + alpha_p, eps) * 2, 0.05, 0.95)

        # Engagement: Beta/Alpha ratio normalized
        state.engagement = np.clip(ba / 3.0, 0.05, 0.95)

        # Load: Delta + high Beta / total
        total = delta_p + theta_p + alpha_p + beta_p + gamma_p + eps
        state.load = np.clip((delta_p * 0.5 + beta_p * 0.8) / total * 2, 0.05, 0.95)

        # Valence: frontal asymmetry (left-right alpha difference)
        state.asymmetry = 0.0
        if self.n_channels >= 4:
            left_alpha = 0  # AF7
            right_alpha = 0  # AF8
            try:
                left_mask = (xf >= 8) & (xf < 13)
                right_mask = (xf >= 8) & (xf < 13)
                yf_left = fft(window_win[1] * win)  # AF7
                yf_right = fft(window_win[2] * win)  # AF8
                mag_left = np.abs(yf_left[left_mask]).sum() if left_mask.any() else eps
                mag_right = np.abs(yf_right[right_mask]).sum() if right_mask.any() else eps
                state.asymmetry = np.log(mag_left / max(mag_right, eps))
                state.valence = np.clip((state.asymmetry + 2) / 4, 0.05, 0.95)
            except:
                state.valence = 0.5
        else:
            state.valence = 0.5

        # Coherence: phase synchrony between frontal channels (AF7, AF8 if available)
        state.coherence = 0.5
        if self.n_channels >= 3:
            try:
                yf_af7 = fft(window_win[1] * win)
                yf_af8 = fft(window_win[2] * win)
                alpha_mask_xf = (xf >= 8) & (xf < 13)
                coherence = np.abs(
                    np.mean(yf_af7[alpha_mask_xf] * np.conj(yf_af8[alpha_mask_xf]))
                ) / (np.sqrt(np.mean(np.abs(yf_af7[alpha_mask_xf])**2) *
                             np.mean(np.abs(yf_af8[alpha_mask_xf])**2)) + eps)
                state.coherence = np.clip(coherence, 0.05, 0.95)
            except:
                state.coherence = 0.5

        # Fractal complexity derived from spectral slope (1/f)
        try:
            yf_all = fft(window_win[0] * win)
            psd = np.abs(yf_all[pos_mask]) ** 2
            freqs = xf[xf > 1]
            psd_freq = psd[xf > 1]
            if len(freqs) > 10 and np.all(psd_freq > 0):
                log_psd = np.log(psd_freq + eps)
                log_freq = np.log(freqs + eps)
                slope, _ = np.polyfit(log_freq, log_psd, 1)
                state.fractal_complexity = np.clip(2.0 - slope, 1.5, 3.5)
        except:
            state.fractal_complexity = 2.5

        # Dominant band
        max_band = max(BAND_NAMES, key=lambda b: state.band_powers.get(b, 0))
        state.dominant_band = max_band

        # Fractal speed from alpha peak frequency
        try:
            alpha_peak_mask = (xf >= 8) & (xf <= 13)
            if alpha_peak_mask.any():
                alpha_psd = np.abs(yf[alpha_peak_mask])
                peak_idx = np.argmax(alpha_psd)
                peak_freq = xf[alpha_peak_mask][peak_idx]
                state.fractal_speed = np.clip(peak_freq / 10.0, 0.5, 2.0)
        except:
            state.fractal_speed = 1.0

        self.state = state

    def _detect_blinks(self, samples):
        """Simple blink detection from frontal channel."""
        if self.n_channels >= 2:
            frontal = samples[1]  # AF7
            self._blink_buffer.extend(frontal)
            if len(self._blink_buffer) >= self.fs // 4:
                arr = np.array(list(self._blink_buffer)[-self.fs//4:])
                peak = np.max(np.abs(arr))
                if peak > 0.8 and time.time() - self._last_blink_time > 0.3:
                    self._last_blink_time = time.time()
                    self.state.blink_rate = 0.8 * self.state.blink_rate + 0.2 * (60.0 / max(time.time() - self._last_blink_time + 0.1, 0.5))

    def get_state(self):
        return self.state


import time
