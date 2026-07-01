"""Neural Frequency Profile — maps brain-wave frequencies to Mandelbrot coordinates.

Each frequency bin from FFT analysis maps to a specific region in the Mandelbrot set.
The user's neural activity determines their unique infinite journey through the fractal.
"""
import hashlib, math, random
from typing import List, Tuple

# Frequency bands and their Mandelbrot mapping
# Each band maps (cx, cy, zoom) with an amplitude scalar
FREQ_BANDS = [
    {"name": "delta",  "min": 0.5,  "max": 4,   "cx": -1.5,  "cy":  0.0,  "zoom": 0.5,  "weight": 0.5},
    {"name": "theta",  "min": 4,    "max": 8,   "cx": -1.0,  "cy":  0.3,  "zoom": 1.0,  "weight": 0.6},
    {"name": "alpha",  "min": 8,    "max": 13,  "cx": -0.5,  "cy":  0.0,  "zoom": 2.0,  "weight": 1.0},
    {"name": "beta",   "min": 13,   "max": 30,  "cx": -0.75, "cy":  0.15, "zoom": 4.0,  "weight": 0.8},
    {"name": "gamma",  "min": 30,   "max": 50,  "cx": -0.16, "cy":  1.04, "zoom": 6.0,  "weight": 0.4},
]

# Well-known Mandelbrot regions for finer mapping
MANDELBROT_REGIONS = [
    {"cx": -0.5,    "cy":  0.0,    "zoom": 1.0,   "label": "ORIGIN"},
    {"cx": -0.75,   "cy":  0.1,    "zoom": 2.0,   "label": "MAIN_CARDIOID"},
    {"cx": -0.7269, "cy":  0.1889, "zoom": 4.0,   "label": "SYNAPSE"},
    {"cx": -0.7435, "cy":  0.1314, "zoom": 8.0,   "label": "AXON"},
    {"cx": -1.0,    "cy":  0.0,    "zoom": 3.0,   "label": "SEAHORSE"},
    {"cx": -0.8,    "cy":  0.156,  "zoom": 6.0,   "label": "CORTEX"},
    {"cx": -0.7453, "cy":  0.1127, "zoom": 12.0,  "label": "NUCLEUS"},
    {"cx": -0.16,   "cy":  1.04,   "zoom": 4.0,   "label": "LIMBIC"},
    {"cx":  0.25,   "cy":  0.0,    "zoom": 2.0,   "label": "FRONTIER"},
    {"cx": -0.5,    "cy":  0.5,    "zoom": 3.0,   "label": "NEURAL_RIDGE"},
]

class NeuralProfile:
    """Maps a user's neural frequencies to a Mandelbrot journey."""

    def __init__(self, user_id: str = "anonymous"):
        h = hashlib.sha256(user_id.encode()).hexdigest()
        self.seed = int(h[:12], 16)
        self.user_id = user_id
        self.dna = h[:16]
        self._rng = random.Random(self.seed)

        # Personal hue shift from DNA
        self.hue_shift = self._rng.random() * 360

        # Shuffle region order per user (deterministic)
        self._region_order = MANDELBROT_REGIONS.copy()
        self._rng.shuffle(self._region_order)

    def freq_to_journey(self, frequencies: dict) -> dict:
        """Map a frequency spectrum to Mandelbrot coordinates.

        Args:
            frequencies: dict of band_name -> amplitude (0-1)
                e.g. {"delta": 0.3, "theta": 0.5, "alpha": 0.8, "beta": 0.6, "gamma": 0.2}

        Returns:
            dict with cx, cy, zoom, label, and spectrum breakdown
        """
        cx = 0.0
        cy = 0.0
        zoom = 1.0
        total_weight = 0.0

        for band in FREQ_BANDS:
            amp = frequencies.get(band["name"], 0.0)
            w = band["weight"] * amp
            cx += band["cx"] * w
            cy += band["cy"] * w
            zoom += (band["zoom"] - 1.0) * w
            total_weight += w

        if total_weight > 0:
            cx /= total_weight
            cy /= total_weight
            zoom = max(0.5, zoom / total_weight)

        # Find nearest labeled region for reference
        nearest = min(self._region_order,
            key=lambda r: (r["cx"] - cx)**2 + (r["cy"] - cy)**2)
        label = nearest["label"]

        return {
            "cx": round(cx, 6),
            "cy": round(cy, 6),
            "zoom": round(zoom, 4),
            "label": label,
            "hue_shift": self.hue_shift,
            "spectrum": {b["name"]: round(frequencies.get(b["name"], 0), 4) for b in FREQ_BANDS},
        }

    def cognitive_to_frequencies(self, cognitive_state: dict) -> dict:
        """Map cognitive state metrics to frequency band amplitudes.

        Converts the real-time cognitive metrics into synthetic EEG-like
        frequency band powers for the Mandelbrot mapping.
        """
        attn = cognitive_state.get("attention", 0.5)
        eng = cognitive_state.get("engagement", 0.5)
        load = cognitive_state.get("load", cognitive_state.get("workload", 0.3))
        val = cognitive_state.get("valence", 0.5)
        coh = cognitive_state.get("coherence", 0.5)

        return {
            "delta":  max(0, 1.0 - attn * 1.2),          # high when unfocused
            "theta":  max(0, 1.0 - eng * 1.2),            # high when relaxed
            "alpha":  attn * (1.0 - load * 0.5),           # high when focused
            "beta":   eng * (0.5 + val * 0.5),             # high when engaged
            "gamma":  load * coh,                           # high in complex tasks
        }

    def neural_nodes(self, width=1.0, height=1.0) -> list:
        """Generate neural network overlay nodes from seed."""
        rng = random.Random(self.seed)
        nodes = []
        for i in range(24):
            nodes.append({
                "id": f"N{i:02d}",
                "x": round(rng.uniform(0.05, 0.95) * width / width, 3),
                "y": round(rng.uniform(0.05, 0.95) * height / height, 3),
                "r": round(rng.uniform(3, 8), 1),
                "connections": [
                    rng.randint(0, 23)
                    for _ in range(rng.randint(2, 5))
                    if rng.random() > 0.5
                ],
            })
        return nodes
