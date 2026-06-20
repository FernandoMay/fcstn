"""Generate dream/surreal visualization parameters from brain state.

Dream states are characterized by high theta and alpha activity.
This module generates visual parameters for surreal, dream-like imagery
using fractal interpolation and morphing.
"""

import numpy as np
import logging
from ..signal import BrainState

log = logging.getLogger('BCI.Dream')


class DreamGenerator:
    """Generate dream visualization parameters from brain frequencies.

    Dream parameters:
      - Morph speed → theta/alpha ratio
      - Surrealism level → delta activity (deep unconscious)
      - Color palette → valence (positive/negative dream tone)
      - Pattern complexity → fractal dimension
      - Emotional tone → band power distribution
      - Narrative fragments → coherence level
    """

    def __init__(self):
        self._dream_state = {
            'morph_speed': 0.5,
            'surrealism': 0.5,
            'vividness': 0.5,
            'lucidity': 0.0,
            'color_hue': 0.0,
            'pattern_density': 0.5,
            'luminosity': 0.5,
            'emotional_valence': 0.5,
        }
        self._scene = 0
        self._last_parameters = {}

    def update(self, brain: BrainState) -> dict:
        """Update dream visualization parameters from brain state.

        Returns dict of visualization parameters.
        """
        bp = brain.band_powers

        # Theta/Alpha ratio → morph speed (theta = dreams, alpha = quiet)
        theta_alpha = brain.alpha_theta_ratio  # higher = more alpha = less dream
        self._dream_state['morph_speed'] = np.clip(1.0 - theta_alpha / 3.0, 0.1, 1.0)

        # Delta → surrealism (delta = deep unconscious)
        delta_p = bp.get('delta', 0)
        total = sum(bp.values()) + 1e-10
        delta_ratio = delta_p / total
        self._dream_state['surrealism'] = np.clip(delta_ratio * 5, 0.1, 0.95)

        # Gamma → lucidity (gamma = conscious awareness during dream)
        gamma_p = bp.get('gamma', 0)
        gamma_ratio = gamma_p / total
        self._dream_state['lucidity'] = np.clip(gamma_ratio * 5, 0.0, 0.95)

        # Alpha → vividness
        alpha_p = bp.get('alpha', 0)
        alpha_ratio = alpha_p / total
        self._dream_state['vividness'] = np.clip(alpha_ratio * 4, 0.1, 0.95)

        # Valence → color hue
        self._dream_state['color_hue'] = brain.valence
        self._dream_state['emotional_valence'] = brain.valence

        # Fractal dimension → pattern density
        self._dream_state['pattern_density'] = np.clip(
            (brain.fractal_complexity - 1.5) / 2.0, 0.1, 0.95)

        # Load → luminosity (low load = serene bright, high load = intense dark)
        self._dream_state['luminosity'] = np.clip(1.0 - brain.load * 0.5, 0.3, 0.9)

        # Detect scene transitions based on state changes
        if brain.load > 0.7 or brain.attention > 0.85:
            self._scene += 1

        # Build dream parameters
        params = dict(self._dream_state)
        params['scene'] = self._scene
        params['fractal_dimension'] = brain.fractal_complexity
        params['dominant_band'] = brain.dominant_band
        params['alpha_theta_ratio'] = brain.alpha_theta_ratio
        params['coherence'] = brain.coherence

        # Scene type classification
        lucidity = params['lucidity']
        if brain.alpha_theta_ratio < 0.5 and brain.load < 0.3:
            params['dream_type'] = 'peaceful_dream'
        elif brain.load > 0.7:
            params['dream_type'] = 'nightmare'
        elif lucidity > 0.6:
            params['dream_type'] = 'lucid_dream'
        elif brain.gamma_beta_ratio > 2.0:
            params['dream_type'] = 'transcendent'
        else:
            params['dream_type'] = 'normal_dream'

        # Hypnagogic imagery parameters
        theta_p = bp.get('theta', 0)
        params['hypnagogic_intensity'] = np.clip(theta_p / total * 4, 0, 0.9)
        params['spiral_density'] = np.clip(gamma_ratio * 3, 0, 0.8)
        params['fractal_morph_rate'] = params['morph_speed'] * brain.fractal_speed

        # Fragment generation (dream narrative bits)
        coherence = brain.coherence
        fragment_count = int((1 - coherence) * 10) + 1
        fragments = []
        fragment_themes = [
            "floating architecture", "impossible geometry",
            "time dilation", "identity shift", "memory palace",
            "ancestral memory", "future self", "parallel reality",
            "ocean of light", "crystalline city", "cosmic library",
            "infinite staircase", "mirror world", "color symphony",
        ]
        for i in range(fragment_count):
            theme = fragment_themes[(i + self._scene) % len(fragment_themes)]
            fragments.append({
                'id': i,
                'theme': theme,
                'intensity': np.random.random() * (1 - coherence),
                'duration': np.random.random() * 5 + 2,
            })
        params['fragments'] = fragments

        self._last_parameters = params
        return params

    def get_parameters(self):
        return self._last_parameters
