"""Map brain frequency ratios to a Mandelbrot/fractal path navigation.

The brain's electrical symphony (delta/theta/alpha/beta/gamma) drives
continuous navigation through the Mandelbrot set, creating a unique
psycho-fractal journey that reflects the user's cognitive state.
"""

import numpy as np
import logging
from dataclasses import dataclass, field
from .signal import BrainState

log = logging.getLogger('BCI.FractalMapper')

F = np.float64


@dataclass
class FractalPath:
    """Current position and trajectory on the fractal manifold."""
    # Mandelbrot space coordinates
    center_x: float = -0.5
    center_y: float = 0.0
    zoom: float = 1.0
    rotation: float = 0.0
    # Navigation state
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    zoom_velocity: float = 0.0
    # Julia seed (if navigating Julia set instead)
    julia_cx: float = -0.7
    julia_cy: float = 0.27015
    use_julia: bool = False
    # Historical path
    trail: list = field(default_factory=list)
    max_trail: int = 100

    def to_dict(self):
        return {
            'center_x': round(self.center_x, 6),
            'center_y': round(self.center_y, 6),
            'zoom': round(self.zoom, 6),
            'rotation': round(self.rotation, 4),
            'julia_cx': round(self.julia_cx, 6),
            'julia_cy': round(self.julia_cy, 6),
            'use_julia': self.use_julia,
        }


class FractalMapper:
    """Map real-time brain frequencies to Mandelbrot navigation."""

    # Known interesting Mandelbrot locations (x, y, zoom)
    LANDMARKS = [
        (-0.5, 0.0, 1.0),           # Main cardioid
        (-0.75, 0.0, 2.5),          # Main bulb
        (-0.155, 0.662, 50.0),      # Seahorse valley
        (-0.748, 0.092, 100.0),     # Triple spiral
        (-0.168, 0.664, 100.0),     # Seahorse valley deep
        (-1.255, 0.063, 200.0),     # Elephant valley
        (-0.7436, 0.1139, 500.0),   # Deep spiral
        (-0.19, 0.655, 500.0),      # Seahorse spiral
        (-0.7485, 0.0925, 1000.0),  # Deep triple spiral
        (-0.166, 0.657, 1000.0),    # Seahorse deep
        (-1.748, 0.0, 500.0),       # Far left tip
        (0.28, 0.0, 50.0),          # Right bulb
    ]

    def __init__(self):
        self.path = FractalPath()
        self._current_landmark = 0
        self._exploration_mode = 'free'  # 'free', 'guided', 'dream'
        self._target_x = self.path.center_x
        self._target_y = self.path.center_y
        self._target_zoom = self.path.zoom

    def update(self, brain: BrainState, dt: float = 0.05):
        """Update fractal navigation parameters from brain state.

        Mapping rules:
          - Theta/Alpha ratio → zoom direction (deeper with focus)
          - Beta/Alpha ratio → horizontal velocity
          - Gamma/Beta ratio → vertical velocity
          - Alpha/Theta ratio → rotation
          - Fractal complexity → rotation speed
          - Delta power → zoom speed modulation
          - Valence → exploration direction preference
          - Coherence → Julia/Mandelbrot toggle
        """
        bp = brain.band_powers
        at = brain.alpha_theta_ratio
        ba = brain.beta_alpha_ratio
        gb = brain.gamma_beta_ratio
        dt_ratio = brain.delta_theta_ratio
        eps = 1e-10

        if self._exploration_mode == 'free':
            # Zoom: driven by attention (beta/(theta+alpha))
            # Higher attention → zoom deeper
            zoom_target = np.clip(1.0 + brain.attention * 5.0, 0.1, 1e6)

            # Pan: driven by frequency ratios
            pan_x = np.clip((ba - 1.5) * 0.1, -0.02, 0.02)
            pan_y = np.clip((gb - 1.5) * 0.05, -0.01, 0.01)

            # Theta/Delta → move toward interesting features
            explore_x = np.clip((dt_ratio - 1.0) * 0.005, -0.01, 0.01)
            explore_y = np.clip((at - 1.0) * 0.005, -0.01, 0.01)

            # Apply velocities with smoothing
            smooth = 0.1  # low-pass filter
            self.path.velocity_x = (1 - smooth) * self.path.velocity_x + smooth * (pan_x + explore_x)
            self.path.velocity_y = (1 - smooth) * self.path.velocity_y + smooth * (pan_y + explore_y)
            self.path.zoom_velocity = (1 - smooth) * self.path.zoom_velocity + smooth * (zoom_target - self.path.zoom)

            self.path.center_x += self.path.velocity_x * dt * brain.fractal_speed
            self.path.center_y += self.path.velocity_y * dt * brain.fractal_speed
            self.path.zoom += self.path.zoom_velocity * dt * 0.5

            # Clamp zoom
            self.path.zoom = np.clip(self.path.zoom, 0.01, 1e8)

            # Rotation from alpha peak
            self.path.rotation += (at - 1.0) * 0.5 * dt

        elif self._exploration_mode == 'guided':
            # Move toward landmarks based on brain state
            lx, ly, lz = self.LANDMARKS[self._current_landmark]
            dx = lx - self.path.center_x
            dy = ly - self.path.center_y
            dz = lz - self.path.zoom
            speed = 0.02 * brain.attention
            self.path.center_x += dx * speed
            self.path.center_y += dy * speed
            self.path.zoom += dz * speed

            if abs(dx) < 0.001 and abs(dy) < 0.001 and abs(dz) < 1:
                self._current_landmark = (self._current_landmark + 1) % len(self.LANDMARKS)
                log.info(f"Reached landmark {self._current_landmark}")

        elif self._exploration_mode == 'dream':
            # Drift randomly, modulated by brain waves
            drift_x = np.sin(brain.timestamp * brain.fractal_speed) * 0.02 * brain.engagement
            drift_y = np.cos(brain.timestamp * brain.fractal_speed * 0.7) * 0.02 * brain.valence
            self.path.center_x += drift_x * dt
            self.path.center_y += drift_y * dt
            self.path.zoom += (brain.load - 0.5) * brain.fractal_speed * dt * 10
            self.path.zoom = np.clip(self.path.zoom, 0.1, 1e6)

        # Toggle Julia set when coherence is very high
        self.path.use_julia = brain.coherence > 0.8
        if self.path.use_julia:
            # Julia seed drifts with brain state
            self.path.julia_cx += (bp.get('theta', 0) - 0.5) * dt * 0.1
            self.path.julia_cy += (bp.get('gamma', 0) - 0.5) * dt * 0.1

        # Store trail
        self.path.trail.append((self.path.center_x, self.path.center_y, self.path.zoom))
        if len(self.path.trail) > self.path.max_trail:
            self.path.trail.pop(0)

    def set_mode(self, mode):
        if mode in ('free', 'guided', 'dream'):
            self._exploration_mode = mode
            log.info(f"Exploration mode: {mode}")

    def get_path(self):
        return self.path
