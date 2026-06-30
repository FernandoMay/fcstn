"""Neural DNA Profile Generator.

Generates a deterministic neural fingerprint from a user ID,
which defines a unique infinite journey through the Mandelbrot set.
"""
import hashlib, math, random, time
from typing import List, Tuple

class NeuralProfile:
    """A user's neural DNA — deterministic Mandelbrot journey + palette."""

    def __init__(self, user_id: str = "anonymous"):
        h = hashlib.sha256(user_id.encode()).hexdigest()
        self.seed = int(h[:12], 16)
        self.user_id = user_id
        self.dna = h[:16]
        self._rng = random.Random(self.seed)

        # Palette personalization — shift all hues by this offset
        self.hue_shift = self._rng.random() * 360

        # Deterministic waypoints through the Mandelbrot set
        # Each waypoint: (cx, cy, zoom, label)
        self.waypoints = self._generate_waypoints()

        # Neural network nodes for overlay
        self.neural_nodes = self._generate_nodes()

    def _generate_waypoints(self) -> List[Tuple[float, float, float, str]]:
        """Generate a deterministic path through the Mandelbrot set."""
        base_waypoints = [
            (-0.5, 0.0, 1.0, "ORIGIN"),
            (-0.75, 0.1, 2.0, "DENDRIRE_1"),
            (-0.7269, 0.1889, 4.0, "SYNAPSE_A"),
            (-0.7435, 0.1314, 8.0, "AXON_BETA"),
            (-1.0, 0.0, 3.0, "SEAHORSE"),
            (-0.8, 0.156, 6.0, "CORTEX_III"),
            (-0.7453, 0.1127, 12.0, "NUCLEUS"),
            (-0.16, 1.04, 4.0, "LIMBIC"),
            (0.25, 0.0, 2.0, "FRONTIER"),
            (-0.5, 0.5, 3.0, "NEURAL_RIDGE"),
        ]
        r = self._rng
        r.shuffle(base_waypoints)
        # Jitter each waypoint by the seed
        waypoints = []
        for i, (cx, cy, zoom, label) in enumerate(base_waypoints):
            offset = r.uniform(-0.02, 0.02)
            waypoints.append((
                cx + offset * r.random(),
                cy + offset * r.random(),
                zoom + r.uniform(-1, 1),
                f"{label}_{self.dna[i % len(self.dna)]}"
            ))
        return waypoints

    def _generate_nodes(self) -> List[dict]:
        """Generate neural network overlay nodes."""
        nodes = []
        r = self._rng
        for i in range(24):
            nodes.append({
                "id": f"N{i:02d}",
                "x": r.uniform(0.05, 0.95),
                "y": r.uniform(0.05, 0.95),
                "r": r.uniform(3, 8),
                "connections": [
                    r.randint(0, 23)
                    for _ in range(r.randint(2, 5))
                    if r.random() > 0.5
                ],
            })
        return nodes

    def get_journey_params(self, step: float) -> dict:
        """Get Mandelbrot render params at a given journey step.
        Steps loop through waypoints infinitely with smooth interpolation.
        """
        n = len(self.waypoints)
        idx = int(step) % n
        frac = step - math.floor(step / n) * n
        next_idx = (int(frac) + 1) % n
        t = frac - math.floor(frac)

        w0 = self.waypoints[idx]
        w1 = self.waypoints[next_idx]

        return {
            "cx": w0[0] + (w1[0] - w0[0]) * t,
            "cy": w0[1] + (w1[1] - w0[1]) * t,
            "zoom": w0[2] + (w1[2] - w0[2]) * t,
            "label": w0[3],
            "step": step,
            "hue_shift": self.hue_shift,
        }


