"""Generate Stable Diffusion / image generation prompts from real brain state."""

from ..signal import BrainState

# Prompt templates per dominant brain band
PROMPT_TEMPLATES = {
    'delta': [
        "deep cosmic void, glowing neural embers, slow pulse of creation, {style}",
        "primordial ocean of consciousness, bioluminescent deep sea creatures, abyssal {style}",
        "dreamy misty landscape, ancient memory fragments floating in fog, {style}",
    ],
    'theta': [
        "flowing river of light, dreamlike iridescent waterfalls, mystical forest, {style}",
        "meditative mandala, rotating sacred geometry, golden ratio spiral, {style}",
        "floating islands in a twilight sky, ethereal aurora borealis, {style}",
    ],
    'alpha': [
        "serene fractal garden, calm zen sand patterns, harmonious neural lattice, {style}",
        "peaceful ocean waves at sunset, gentle bioluminescent tide, {style}",
        "balanced yin yang fractal, symmetrical sacred geometry, calm {style}",
    ],
    'beta': [
        "highly detailed cybernetic fractal, neon laser grid, racing light trails, {style}",
        "exploding quantum supernova, hyper-complex mandelbrot zoom, {style}",
        "neural synapse network firing, electric blue and crimson, intense {style}",
    ],
    'gamma': [
        "transcendent cosmic revelation, infinite dimensional portal, kaleidoscopic {style}",
        "universal consciousness visualized, interconnected fractal multiverse, {style}",
        "pure energy waveform, psychedelic quantum foam, reality unraveling {style}",
    ],
}

STYLES = [
    "digital art, octane render, unreal engine 5, cinematic lighting",
    "trending on artstation, greg rutkowski style, beeple inspired",
    "vaporwave synthwave, neon cyberpunk, blade runner aesthetics",
    "surrealist painting, salvador dali meets digital art",
    "beautiful 3d fractal, geometric abstraction, colorful",
    "dark ethereal fantasy, tim burton meets hr giger",
]


class ImagePromptGenerator:
    """Generate image generation prompts from brain state."""

    def __init__(self):
        self._last_prompt = ""
        self._change_threshold = 0.15  # min change to regenerate

    def generate(self, brain: BrainState) -> str:
        """Generate a prompt from current brain state."""
        dominant = brain.dominant_band
        templates = PROMPT_TEMPLATES.get(dominant, PROMPT_TEMPLATES['alpha'])

        # Pick template based on engagement (active vs calm)
        idx = int(brain.engagement * (len(templates) - 1))
        idx = max(0, min(idx, len(templates) - 1))
        template = templates[idx]

        # Pick style based on valence (positive vs negative)
        style_idx = int(brain.valence * (len(STYLES) - 1))
        style = STYLES[max(0, min(style_idx, len(STYLES) - 1))]

        prompt = template.format(style=style)

        # Add complexity detail based on fractal dimension
        fd = brain.fractal_complexity
        if fd > 3.0:
            prompt += ", hyper-detailed, intricate, 8k"
        elif fd > 2.5:
            prompt += ", detailed, intricate"
        elif fd < 2.0:
            prompt += ", minimalist, simple, smooth gradients"

        # Add attention modifiers
        if brain.attention > 0.8:
            prompt += ", sharp focus, crisp, high contrast"
        elif brain.attention < 0.3:
            prompt += ", soft focus, dreamy, blurred edges"

        # Add load modifiers
        if brain.load > 0.7:
            prompt += ", chaotic, intense, explosive energy"
        elif brain.load < 0.3:
            prompt += ", calm, peaceful, serene ambient"

        self._last_prompt = prompt
        return prompt

    @property
    def last_prompt(self):
        return self._last_prompt
