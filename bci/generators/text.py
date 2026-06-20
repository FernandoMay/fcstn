"""Generate coherent narrative text from real brain state."""

from ..signal import BrainState, BAND_NAMES

PREFIXES = [
    "Tu mente ahora mismo:", "Siento que piensas en:",
    "El eco de tu actividad neural:", "Frecuencias detectadas:",
    "Tu consciencia navega:", "Perfil cognitivo:",
]

ATTENTION_PHRASES = {
    'high': ["enfoque quirúrgico", "concentración láser", "hiperatención",
             "precisión mental", "vigilia absoluta"],
    'mid': ["atención moderada", "consciencia estable", "presencia atenta"],
    'low': ["mente divagando", "ensoñación despierta", "sueño ligero"],
}

ENGAGEMENT_PHRASES = {
    'high': ["compromiso total", "inmersión profunda", "flujo creativo",
             "entrega absoluta al momento presente"],
    'mid': ["interés estable", "curiosidad tranquila", "observación activa"],
    'low': ["desconexión suave", "retirada interior", "ensimismamiento"],
}

LOAD_PHRASES = {
    'high': ["sobrecarga cognitiva", "estrés mental elevado",
             "sistema al límite", "fatiga inminente"],
    'mid': ["carga normal", "procesamiento estable", "ritmo sostenible"],
    'low': ["mente en reposo", "relajación profunda", "estado basal"],
}

VALENCE_PHRASES = {
    'high': ["bienestar y placer", "armonía emocional", "experiencia positiva",
             "alegría y satisfacción"],
    'low': ["malestar o tensión", "estado emocional bajo", "incomodidad"],
}

BAND_METAPHORS = {
    'delta': ["latidos del subconsciente", "océano primordial",
              "sueño profundo del alma"],
    'theta': ["río de ensueño", "portal de creatividad",
              "memoria ancestral fluyendo"],
    'alpha': ["calma serena", "puente entre mundos",
              "espejo del presente"],
    'beta': ["mente activa", "procesador central",
             "red de atención despierta"],
    'gamma': ["chispa divina", "sincronía superior",
              "destello de consciencia cósmica"],
}


class TextGenerator:
    """Generate poetic/descriptive text from brain state."""

    def __init__(self):
        self._last = ""

    def generate(self, brain: BrainState) -> str:
        import random, time
        prefix = random.choice(PREFIXES)

        # Attention description
        if brain.attention > 0.7:
            attn = random.choice(ATTENTION_PHRASES['high'])
        elif brain.attention > 0.4:
            attn = random.choice(ATTENTION_PHRASES['mid'])
        else:
            attn = random.choice(ATTENTION_PHRASES['low'])

        # Engagement
        if brain.engagement > 0.7:
            eng = random.choice(ENGAGEMENT_PHRASES['high'])
        elif brain.engagement > 0.4:
            eng = random.choice(ENGAGEMENT_PHRASES['mid'])
        else:
            eng = random.choice(ENGAGEMENT_PHRASES['low'])

        # Load
        if brain.load > 0.7:
            ld = random.choice(LOAD_PHRASES['high'])
        elif brain.load > 0.4:
            ld = random.choice(LOAD_PHRASES['mid'])
        else:
            ld = random.choice(LOAD_PHRASES['low'])

        # Valence
        if brain.valence > 0.6:
            val = random.choice(VALENCE_PHRASES['high'])
        else:
            val = random.choice(VALENCE_PHRASES['low'])

        # Dominant band metaphor
        dom_metaphor = random.choice(BAND_METAPHORS.get(brain.dominant_band, BAND_METAPHORS['alpha']))

        # Band distribution narrative
        bp = brain.band_powers
        total = sum(bp.values()) + 1e-10
        band_pcts = {k: v / total * 100 for k, v in bp.items()}
        top_bands = sorted(band_pcts, key=band_pcts.get, reverse=True)[:3]
        band_dist = f"predominan {top_bands[0]} ({band_pcts[top_bands[0]]:.0f}%), {top_bands[1]} ({band_pcts[top_bands[1]]:.0f}%)"

        # Build narrative
        narrative = (
            f"{prefix} {attn}, {eng}. "
            f"Carga mental: {ld}. "
            f"Estado emocional: {val}. "
            f"Ritmo cerebral: {dom_metaphor} - {band_dist}."
        )

        # Add fractal dimension insight
        fd = brain.fractal_complexity
        if fd > 3.0:
            narrative += " Tu fractal interior alcanza complejidad hiperdimensional."
        elif fd > 2.5:
            narrative += " La geometría de tu pensamiento es rica y detallada."
        elif fd < 2.0:
            narrative += " Tu mente dibuja formas simples y serenas."

        # Add coherence insight
        if brain.coherence > 0.8:
            narrative += " Hay sincronía total entre hemisferios."
        elif brain.coherence < 0.3:
            narrative += " Tus hemisferios procesan de forma independiente."

        if brain.asymmetry > 0.5:
            narrative += " Mayor actividad en hemisferio izquierdo (lógica)."
        elif brain.asymmetry < -0.5:
            narrative += " Mayor actividad en hemisferio derecho (intuición)."

        narrative += f" [fractal: {fd:.2f}, ratio a/th: {brain.alpha_theta_ratio:.2f}]"

        self._last = narrative
        return narrative
