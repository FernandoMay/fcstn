"""Generate music/audio from real brain frequencies using sound synthesis.

Maps each frequency band to a different musical element:
  - Delta → bass drone / sub-bass pulse
  - Theta → pad / ambient texture
  - Alpha → melody / arpeggio
  - Beta → rhythm / percussion
  - Gamma → high-frequency shimmer / detail
"""

import numpy as np
import logging
import time
import threading
from ..signal import BrainState, BANDS

log = logging.getLogger('BCI.Music')

# Musical scale frequencies (equal temperament, A4=440Hz)
NOTES = {
    'C': 261.63, 'C#': 277.18, 'D': 293.66, 'D#': 311.13,
    'E': 329.63, 'F': 349.23, 'F#': 369.99, 'G': 392.00,
    'G#': 415.30, 'A': 440.00, 'A#': 466.16, 'B': 493.88,
}

PENTATONIC = ['C', 'D', 'E', 'G', 'A']
CHROMATIC = list(NOTES.keys())


class MusicGenerator:
    """Real-time brainwave music synthesis."""

    def __init__(self, sampling_rate=44100):
        self.fs = sampling_rate
        self._running = False
        self._thread = None
        self._brain = None
        self._current_notes = {}
        self._bpm = 60
        self._phase = 0.0

    def start(self):
        """Start audio output (requires sounddevice)."""
        try:
            import sounddevice as sd
            self._running = True
            self._thread = threading.Thread(target=self._audio_loop, args=(sd,), daemon=True)
            self._thread.start()
            log.info("Music generator started (audio output)")
        except Exception as e:
            log.warning(f"Audio output unavailable: {e}")

    def stop(self):
        self._running = False

    def update(self, brain: BrainState):
        self._brain = brain
        bp = brain.band_powers

        # BPM from alpha peak
        self._bpm = 50 + brain.fractal_speed * 60

        # Map band powers to musical parameters
        total = sum(bp.values()) + 1e-10

        # Delta → bass fundamental (C2-C3)
        delta_freq = 65.41 + brain.attention * 65.41  # C2 to C3
        self._current_notes['delta'] = {
            'freq': delta_freq,
            'amp': np.clip(bp.get('delta', 0) / total * 3, 0, 0.5),
            'wave': 'sine',
        }

        # Theta → pad (C3-C4) - pentatonic scale
        theta_note_idx = int(brain.engagement * 4)
        theta_note = PENTATONIC[theta_note_idx]
        theta_freq = NOTES[theta_note] * 1  # C4-C5 range
        self._current_notes['theta'] = {
            'freq': theta_freq * (1 + brain.load * 0.1),
            'amp': np.clip(bp.get('theta', 0) / total * 2, 0, 0.3),
            'wave': 'triangle',
        }

        # Alpha → melody (C4-C6)
        alpha_note_idx = int(brain.valence * 11)
        alpha_note = CHROMATIC[alpha_note_idx % 12]
        alpha_octave = 4 + alpha_note_idx // 12
        alpha_freq = NOTES[alpha_note] * (2 ** (alpha_octave - 4))
        self._current_notes['alpha'] = {
            'freq': alpha_freq,
            'amp': np.clip(bp.get('alpha', 0) / total * 2, 0, 0.2),
            'wave': 'square',
        }

        # Beta → rhythm (percussive click)
        self._current_notes['beta'] = {
            'freq': 1000,
            'amp': np.clip(bp.get('beta', 0) / total * 3, 0, 0.15),
            'wave': 'noise',
        }

        # Gamma → shimmer (high sine)
        self._current_notes['gamma'] = {
            'freq': 8000 + brain.fractal_complexity * 2000,
            'amp': np.clip(bp.get('gamma', 0) / total * 2, 0, 0.05),
            'wave': 'sine',
        }

    def _audio_loop(self, sd):
        """Audio output loop."""
        buffer_duration = 0.05
        block_size = int(self.fs * buffer_duration)

        def callback(outdata, frames, time_info, status):
            if status:
                log.warning(f"Audio status: {status}")
            t0 = self._phase
            out = np.zeros(frames)
            for note_name, params in self._current_notes.items():
                freq = params['freq']
                amp = params['amp']
                wave = params['wave']
                t = t0 + np.arange(frames) / self.fs

                if wave == 'sine':
                    sig = np.sin(2 * np.pi * freq * t)
                elif wave == 'triangle':
                    sig = 2 * np.abs(2 * (freq * t % 1) - 1) - 1
                elif wave == 'square':
                    sig = np.sign(np.sin(2 * np.pi * freq * t))
                elif wave == 'noise':
                    sig = np.random.randn(frames) * 0.3
                else:
                    sig = np.sin(2 * np.pi * freq * t)

                out += sig * amp

            # Beta rhythm (percussive)
            note_duration = 60.0 / self._bpm
            beat_pos = (t0 % note_duration) / note_duration
            beta = self._current_notes.get('beta', {}).get('amp', 0)
            if beat_pos < 0.05:
                out += (1 - beat_pos / 0.05) * beta * 0.5

            out = np.clip(out, -0.9, 0.9)
            outdata[:, 0] = out
            self._phase = t0 + frames / self.fs

        try:
            with sd.OutputStream(channels=1, callback=callback,
                                 blocksize=block_size,
                                 samplerate=self.fs):
                while self._running:
                    time.sleep(0.1)
        except Exception as e:
            log.error(f"Audio stream error: {e}")

    def render_to_file(self, brain: BrainState, duration=10, filepath='brain_music.wav'):
        """Render brain state to a WAV file."""
        from scipy.io.wavfile import write
        self.update(brain)
        n = int(self.fs * duration)
        t = np.arange(n) / self.fs
        audio = np.zeros(n)
        for note_name, params in self._current_notes.items():
            freq = params['freq']
            amp = params['amp']
            wave = params['wave']
            if wave == 'sine':
                sig = np.sin(2 * np.pi * freq * t)
            elif wave == 'triangle':
                sig = 2 * np.abs(2 * (freq * t % 1) - 1) - 1
            elif wave == 'square':
                sig = np.sign(np.sin(2 * np.pi * freq * t))
            elif wave == 'noise':
                sig = np.random.randn(n) * 0.3
            else:
                sig = np.sin(2 * np.pi * freq * t)
            audio += sig * amp
        audio = np.clip(audio, -0.9, 0.9)
        write(filepath, self.fs, (audio * 32767).astype(np.int16))
        log.info(f"Rendered {duration}s brain music to {filepath}")
