"""Real-time brain activity visualization using matplotlib."""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import threading
import time
from .signal import BrainState, BAND_NAMES


class BrainVisualizer:
    """Live brain activity dashboard with multiple panels."""

    def __init__(self, update_interval=0.1):
        self.update_interval = update_interval
        self._brain = None
        self._running = False
        self._fig = None
        self._band_history = {b: [] for b in BAND_NAMES}
        self._max_history = 200

    def update(self, brain: BrainState):
        self._brain = brain
        for band in BAND_NAMES:
            val = brain.band_powers.get(band, 0)
            self._band_history[band].append(val)
            if len(self._band_history[band]) > self._max_history:
                self._band_history[band].pop(0)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._running = False
        if self._fig:
            plt.close(self._fig)

    def _run(self):
        plt.style.use('dark_background')
        self._fig = plt.figure(figsize=(14, 8), facecolor='black')
        gs = self._fig.add_gridspec(3, 4, hspace=0.4, wspace=0.3)

        ax_bands = self._fig.add_subplot(gs[0, :2])
        ax_cog = self._fig.add_subplot(gs[0, 2:])
        ax_trend = self._fig.add_subplot(gs[1, :])
        ax_fractal = self._fig.add_subplot(gs[2, 0])
        ax_ratios = self._fig.add_subplot(gs[2, 1])
        ax_status = self._fig.add_subplot(gs[2, 2:])

        def animate(frame):
            if self._brain is None:
                return

            brain = self._brain
            bp = brain.band_powers

            # 1. Band power bar chart
            ax_bands.clear()
            ax_bands.set_facecolor('#0a0a0a')
            bands_vals = [bp.get(b, 0) for b in BAND_NAMES]
            colors = ['#4488FF', '#00FF88', '#00F0FF', '#FF0055', '#FF4400']
            bars = ax_bands.bar(BAND_NAMES, bands_vals, color=colors, alpha=0.8)
            ax_bands.set_title('Frequency Bands', color='white', fontsize=10)
            ax_bands.set_ylim(0, max(bands_vals) * 1.5 if max(bands_vals) > 0 else 1)
            for bar, val in zip(bars, bands_vals):
                ax_bands.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                            f'{val:.3f}', ha='center', va='bottom', color='white', fontsize=8)
            ax_bands.tick_params(colors='gray')

            # 2. Cognitive metrics gauge
            ax_cog.clear()
            ax_cog.set_facecolor('#0a0a0a')
            metrics = [
                ('Attention', brain.attention, '#00F0FF'),
                ('Engagement', brain.engagement, '#00FF88'),
                ('Load', brain.load, '#FF4400'),
                ('Valence', brain.valence, '#FFD700'),
                ('Coherence', brain.coherence, '#9933FF'),
            ]
            y_pos = range(len(metrics))
            vals = [m[1] for m in metrics]
            cols = [m[2] for m in metrics]
            bars = ax_cog.barh(list(y_pos), vals, color=cols, alpha=0.8)
            ax_cog.set_yticks(list(y_pos))
            ax_cog.set_yticklabels([m[0] for m in metrics], color='white', fontsize=9)
            ax_cog.set_xlim(0, 1)
            ax_cog.set_title('Cognitive State', color='white', fontsize=10)
            for bar, val in zip(bars, vals):
                ax_cog.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                          f'{val:.2f}', va='center', color=cols[list(vals).index(val)], fontsize=8)

            # 3. Band power trend
            ax_trend.clear()
            ax_trend.set_facecolor('#0a0a0a')
            for i, band in enumerate(BAND_NAMES):
                hist = self._band_history[band]
                if len(hist) > 1:
                    ax_trend.plot(hist, color=colors[i], label=band, alpha=0.7, linewidth=1)
            ax_trend.set_title('Band Power Trend (last 200 windows)', color='white', fontsize=10)
            ax_trend.legend(loc='upper right', fontsize=7, labelcolor='white')
            ax_trend.tick_params(colors='gray')

            # 4. Fractal dimension
            ax_fractal.clear()
            ax_fractal.set_facecolor('#0a0a0a')
            ax_fractal.text(0.5, 0.7, f'{brain.fractal_complexity:.3f}', ha='center', va='center',
                          fontsize=32, color='#00F0FF', fontweight='bold')
            ax_fractal.text(0.5, 0.3, 'Fractal\nDimension', ha='center', va='center',
                          fontsize=10, color='gray')
            ax_fractal.set_xlim(0, 1)
            ax_fractal.set_ylim(0, 1)

            # 5. Ratios
            ax_ratios.clear()
            ax_ratios.set_facecolor('#0a0a0a')
            ratios = [
                ('Alpha/Theta', brain.alpha_theta_ratio),
                ('Beta/Alpha', brain.beta_alpha_ratio),
                ('Delta/Theta', brain.delta_theta_ratio),
                ('Gamma/Beta', brain.gamma_beta_ratio),
            ]
            for i, (name, val) in enumerate(ratios):
                ax_ratios.text(0.5, 0.75 - i * 0.18, f'{name}: {val:.2f}', ha='center',
                             fontsize=9, color='white')
            ax_ratios.set_xlim(0, 1)
            ax_ratios.set_ylim(0, 1)
            ax_ratios.set_title('Frequency Ratios', color='white', fontsize=10)

            # 6. Status summary
            ax_status.clear()
            ax_status.set_facecolor('#0a0a0a')
            lines = [
                f'DOMINANT: {brain.dominant_band.upper()}',
                f'ASYMMETRY: {brain.asymmetry:+.3f}',
                f'BLINKS/MIN: {brain.blink_rate:.1f}',
                f'RATIO a/th: {brain.alpha_theta_ratio:.2f}',
                f'FRACTAL: {brain.fractal_complexity:.2f}',
            ]
            for i, line in enumerate(lines):
                ax_status.text(0.5, 0.8 - i * 0.15, line, ha='center', fontsize=9, color='#00F0FF')
            ax_status.set_xlim(0, 1)
            ax_status.set_ylim(0, 1)
            ax_status.set_title('Live Status', color='white', fontsize=10)

        ani = FuncAnimation(self._fig, animate, interval=self.update_interval * 1000, cache_frame_data=False)
        plt.show()
