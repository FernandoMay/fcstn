"""Generate procedural game map terrain from real brain frequencies."""

import numpy as np
import logging
from ..signal import BrainState

log = logging.getLogger('BCI.GameMap')


class GameMapGenerator:
    """Generate 2D terrain heightmaps for game worlds from brain state.

    Each frequency band controls a different layer of Perlin-like noise:
      - Delta: macro terrain (mountains, continents)
      - Theta: meso terrain (hills, valleys)
      - Alpha: micro terrain (details, rocks)
      - Beta: surface features (trees, structures)
      - Gamma: special features (rivers, resource nodes)
    """

    def __init__(self, size=256):
        self.size = size
        self._last_map = None
        log.info(f"GameMapGenerator: {size}x{size} maps")

    def generate(self, brain: BrainState) -> dict:
        """Generate a terrain map from brain state.

        Returns:
            dict with 'heightmap' (np.ndarray), 'biome', 'features', etc.
        """
        bp = brain.band_powers
        size = self.size
        X, Y = np.meshgrid(np.linspace(0, 4, size), np.linspace(0, 4, size))

        # Each band contributes at a different frequency
        # Delta → large features (0.5-2 cycles across map)
        delta_contribution = bp.get('delta', 0)
        delta_scale = 0.5 + delta_contribution * 1.5
        delta_terrain = self._noise(X * delta_scale, Y * delta_scale, seed=0)

        # Theta → medium features (2-5 cycles)
        theta_contribution = bp.get('theta', 0)
        theta_scale = 2 + theta_contribution * 3
        theta_terrain = self._noise(X * theta_scale, Y * theta_scale, seed=1)

        # Alpha → fine detail (5-10 cycles)
        alpha_contribution = bp.get('alpha', 0)
        alpha_scale = 5 + alpha_contribution * 5
        alpha_terrain = self._noise(X * alpha_scale, Y * alpha_scale, seed=2)

        # Beta → surface noise (10-20 cycles)
        beta_contribution = bp.get('beta', 0)
        beta_scale = 10 + beta_contribution * 10
        beta_terrain = self._noise(X * beta_scale, Y * beta_scale, seed=3)

        # Gamma → rare spikes (resource nodes)
        gamma_contribution = bp.get('gamma', 0)
        gamma_scale = 20 + gamma_contribution * 20
        gamma_terrain = self._noise(X * gamma_scale, Y * gamma_scale, seed=4)
        gamma_peaks = (gamma_terrain > 0.85).astype(float)

        # Blend layers based on brain state
        heightmap = (
            delta_terrain * (0.3 + delta_contribution * 0.4) +
            theta_terrain * (0.25 + theta_contribution * 0.3) +
            alpha_terrain * (0.2 + alpha_contribution * 0.2) +
            beta_terrain * (0.15 + beta_contribution * 0.1) +
            gamma_peaks * 0.1 * gamma_contribution
        )

        # Normalize
        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min() + 1e-10)

        # Apply fractal dimension as roughness
        fd = brain.fractal_complexity
        heightmap = np.power(heightmap, 1.0 / max(fd - 1.0, 0.1))

        # Determine biome from brain state
        if brain.load > 0.7:
            biome = 'chaos_wastes'
            color_palette = ['#1a0000', '#330000', '#660000', '#990000', '#cc3300']
        elif brain.attention > 0.7:
            biome = 'crystalline_desert'
            color_palette = ['#ffeedd', '#ffddbb', '#eebb99', '#ccaa77', '#aa8855']
        elif brain.engagement > 0.7:
            biome = 'bioluminescent_forest'
            color_palette = ['#001a00', '#003300', '#006633', '#009966', '#00ffcc']
        elif brain.valence > 0.7:
            biome = 'paradise_valley'
            color_palette = ['#004400', '#227722', '#44aa44', '#77dd77', '#aaffaa']
        elif brain.coherence > 0.7:
            biome = 'harmonic_plains'
            color_palette = ['#333366', '#444488', '#5555aa', '#6666cc', '#7777ff']
        else:
            biome = 'neutral_terrain'
            color_palette = ['#333333', '#555555', '#777777', '#999999', '#bbbbbb']

        # Generate features based on brain metrics
        features = []

        # Rivers from coherence
        if brain.coherence > 0.5:
            n_rivers = int(brain.coherence * 5)
            for _ in range(n_rivers):
                x = np.random.randint(0, size)
                y = np.random.randint(0, size)
                features.append({'type': 'river', 'x': x, 'y': y,
                                 'length': int(brain.engagement * size // 4)})

        # Resource nodes from gamma
        if gamma_contribution > 0.3:
            node_positions = np.argwhere(gamma_terrain > 0.85)
            for pos in node_positions[:5]:
                features.append({'type': 'resource_node', 'x': int(pos[1]),
                                 'y': int(pos[0]), 'value': gamma_contribution})

        # Settlements from theta
        theta_positions = np.argwhere(theta_terrain > 0.7)
        for pos in theta_positions[:3]:
            features.append({'type': 'settlement', 'x': int(pos[1]),
                             'y': int(pos[0]), 'size': int(brain.attention * 3 + 1)})

        result = {
            'heightmap': heightmap.tolist(),
            'biome': biome,
            'color_palette': color_palette,
            'features': features,
            'size': size,
            'fractal_dimension': round(fd, 3),
            'dominant_band': brain.dominant_band,
        }

        self._last_map = result
        return result

    def _noise(self, X, Y, seed=0):
        """Simple value noise approximation using sin/cos hash."""
        np.random.seed(seed)
        hash_x = np.sin(X * 12.9898 + Y * 78.233 + seed) * 43758.5453
        hash_y = np.sin(X * 33.6998 + Y * 91.137 + seed + 1) * 27118.1234
        noise = hash_x - np.floor(hash_x) + hash_y - np.floor(hash_y)
        return (noise - noise.min()) / (noise.max() - noise.min() + 1e-10)
