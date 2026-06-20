"""FCSTN Live Demo Server - Cognitive Engine with WebSocket broadcast ++ voice + Flutter support."""

import asyncio
import json
import websockets
import logging
import random
import time
import threading
import math
from dataclasses import dataclass, field, asdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s [FCSTN] %(message)s')
log = logging.getLogger('FCSTN')


@dataclass
class CognitiveState:
    attention: float = 0.5
    engagement: float = 0.5
    workload: float = 0.3
    load: float = 0.3
    valence: float = 0.5
    coherence: float = 0.5
    fractal_dimension: float = 2.5
    fractal_dim: float = 2.5
    state_name: str = "resting"
    phase: str = "resting"
    color: str = "#00F0FF"
    complexity: float = 0.5
    instability: float = 0.3
    timestamp: float = field(default_factory=time.time)
    narrative: str = "Red sintonizada. Ecosistema cognitivo estable."
    image_prompt: str = "fractal neuro-digital nexus, symmetrical geometry, network lattice"

    def to_dict(self):
        return {
            "attention": self.attention,
            "engagement": self.engagement,
            "load": self.workload,
            "workload": self.workload,
            "valence": self.valence,
            "coherence": self.coherence,
            "fractal_dimension": self.fractal_dimension,
            "fractal_dim": self.fractal_dimension,
            "state_name": self.state_name,
            "phase": self.phase,
            "color": self.color,
            "complexity": self.complexity,
            "instability": self.instability,
            "timestamp": self.timestamp,
            "narrative": self.narrative,
            "image_prompt": self.image_prompt,
        }


KEYWORDS_MAP = {
    "caos": {"load": 0.95, "attention": 0.90, "engagement": 0.85, "narrative": "Modulación caótica de espacio-tiempo. Inyectando entropía fractal."},
    "colapso": {"load": 0.95, "attention": 0.95, "engagement": 0.70, "narrative": "Colapso inminente detectado. Espacio-tiempo comprimiéndose de golpe."},
    "estrés": {"load": 0.90, "attention": 0.85, "engagement": 0.60, "narrative": "Alerta de estrés cognitivo. Elevando andamiaje geométrico protector."},
    "calma": {"load": 0.10, "attention": 0.25, "engagement": 0.30, "narrative": "Sintonizando ondas delta/alfa. Geometría fractal estable y relajada."},
    "relajar": {"load": 0.08, "attention": 0.20, "engagement": 0.25, "narrative": "Descompresión cognitiva activa. Ralentizando evolución temporal."},
    "paz": {"load": 0.15, "attention": 0.30, "engagement": 0.20, "narrative": "Estabilización simétrica. Resonancia cerebral en modo pacífico."},
    "viaje": {"load": 0.40, "attention": 0.75, "engagement": 0.85, "narrative": "Iniciando viaje espacio-temporal. Dimensiones fractales en expansión."},
    "aprender": {"load": 0.50, "attention": 0.85, "engagement": 0.80, "narrative": "Modo aprendizaje profundo. Mapeando sinapsis de conocimiento en tiempo real."},
    "curioso": {"load": 0.35, "attention": 0.70, "engagement": 0.90, "narrative": "Curiosidad intelectual activa. Explorando anomalías geométricas."},
    "mente": {"load": 0.30, "attention": 0.60, "engagement": 0.85, "narrative": "Mapeando redes neuronales humanas. Simbiosis bio-digital establecida."},
    "conexión": {"load": 0.25, "attention": 0.65, "engagement": 0.90, "narrative": "Conectividad total establecida. Transfiriendo señales cognitivas."},
    "foco": {"load": 0.30, "attention": 0.95, "engagement": 0.80, "narrative": "Atención quirúrgica activa. Precisión fractal milimétrica."},
    "explosion": {"load": 0.95, "attention": 0.95, "engagement": 0.95, "valence": 0.90, "narrative": "EXPLOSIÓN COGNITIVA - Todas las métricas al máximo. Teatro cuántico activado."},
    "todas maximas": {"load": 0.95, "attention": 0.95, "engagement": 0.95, "valence": 0.90, "coherence": 0.90, "narrative": "EXPLOSIÓN COGNITIVA - Todas las métricas al máximo. Teatro cuántico activado."},
    "todas minimas": {"load": 0.05, "attention": 0.05, "engagement": 0.05, "valence": 0.10, "coherence": 0.10, "narrative": "Reposo total cognitivo. Sistema en standby."},
    "reposo": {"load": 0.05, "attention": 0.05, "engagement": 0.05, "valence": 0.10, "coherence": 0.10, "narrative": "Reposo total cognitivo. Sistema en standby."},
    "creativo": {"load": 0.30, "attention": 0.60, "engagement": 0.80, "valence": 0.95, "narrative": "Creatividad desatada. Valencia máxima. Nuevas geometrías emergiendo."},
    "equilibrio": {"load": 0.30, "attention": 0.50, "engagement": 0.50, "valence": 0.50, "coherence": 0.85, "narrative": "Coherencia neural establecida. Armonía fractal equilibrada."},
    "atencion": {"load": 0.30, "attention": 0.90, "engagement": 0.70, "narrative": "Alta atención detectada. Precisión y enfoque máximo."},
    "alta atencion": {"load": 0.30, "attention": 0.90, "engagement": 0.70, "narrative": "Alta atención detectada. Precisión y enfoque máximo."},
    "carga maxima": {"load": 0.90, "attention": 0.80, "engagement": 0.75, "narrative": "Carga máxima activada. Sobrecarga controlada del sistema."},
    "carga baja": {"load": 0.05, "attention": 0.30, "engagement": 0.35, "narrative": "Carga baja. Sistema en modo descanso profundo."},
    "alta valencia": {"load": 0.25, "attention": 0.55, "engagement": 0.70, "valence": 0.90, "narrative": "Valencia emocional elevada. Experiencia positiva amplificada."},
    "coherencia alta": {"load": 0.25, "attention": 0.50, "engagement": 0.50, "coherence": 0.85, "narrative": "✦ Coherencia neural óptima. Sincronización hemisférica total."},
    "agresivo": {"load": 0.85, "attention": 0.95, "engagement": 0.90, "narrative": "Respuesta agresiva de la IA. Sobrecargando de luz y energía el render."},
}


class FCSTNEngine:
    def __init__(self):
        self.state = CognitiveState()
        self._idle_counter = 0
        self.time_step = 0
        self.history = []
        self.clients = set()

    def process_input(self, text: str, time_taken: float) -> CognitiveState:
        self.time_step += 1
        self._idle_counter = 0
        text_lower = text.lower() if text else ""

        matched_keyword = None
        for kw, override in KEYWORDS_MAP.items():
            if kw in text_lower:
                matched_keyword = kw
                if "load" in override:
                    self.state.workload = override["load"]
                if "attention" in override:
                    self.state.attention = override["attention"]
                if "engagement" in override:
                    self.state.engagement = override["engagement"]
                if "valence" in override:
                    self.state.valence = override["valence"]
                if "coherence" in override:
                    self.state.coherence = override["coherence"]
                if "narrative" in override:
                    self.state.narrative = override["narrative"]
                break

        if not matched_keyword:
            speed_factor = max(0, min(1, 1.0 - (time_taken / 10.0)))
            text_complexity = min(1.0, len(text) / 100.0) if text else 0.3
            self.state.attention = self.state.attention * 0.6 + (speed_factor * 0.6 + text_complexity * 0.4) * 0.4
            self.state.engagement = self.state.engagement * 0.6 + (0.5 + (speed_factor - 0.5) * 0.4 + text_complexity * 0.4) * 0.4
            self.state.workload = self.state.workload * 0.6 + (speed_factor * 0.5 + text_complexity * 0.5) * 0.4

            self.state.attention = max(0.05, min(0.95, self.state.attention))
            self.state.engagement = max(0.05, min(0.95, self.state.engagement))
            self.state.workload = max(0.05, min(0.95, self.state.workload))

        self._derive_state()

        if not matched_keyword:
            self.state.narrative = self._generate_narrative()

        prompt_styles = {
            "focused": "highly detailed hyper-complex mandelbrot 3d fractal, glowing laser grids, cybernetic neural synapse network, crimson and cyan glow",
            "stressed": "chaotic unstable fractal geometry, red and orange energy sparks, exploding neural patterns, high friction glitch art",
            "fatigued": "soft minimalist geometry, smooth calm fluid gradients, soft blue ambient light, zen mandela shapes",
            "engaged": "interconnected neural network matrix, glowing purple and teal nodes, beautiful digital harmony, sleek tech line art",
            "curious": "exploratory deep space fractal zoom, biological neon plant fractal, green emerald bio-luminescence",
            "resting": "symmetrical clean mathematical 3d rendering, violet neon lattice lines, balanced composition",
        }
        self.state.image_prompt = prompt_styles.get(self.state.state_name, prompt_styles["resting"])
        if text:
            self.state.image_prompt += f", inspired by '{text[:50]}'"

        self.state.timestamp = time.time()
        self.history.append(self.state.to_dict())
        if len(self.history) > 200:
            self.history.pop(0)

        log.info(f"State: {self.state.state_name.upper()} | "
                 f"Attn: {self.state.attention:.2f} | "
                 f"Eng: {self.state.engagement:.2f} | "
                 f"Load: {self.state.workload:.2f} | "
                 f"Dim: {self.state.fractal_dimension:.2f} | "
                 f"Text: '{text}'")

        return self.state

    def _derive_state(self):
        self.state.fractal_dimension = 2.0 + (self.state.attention * 0.6 + self.state.engagement * 0.4)
        self.state.fractal_dim = self.state.fractal_dimension
        self.state.complexity = (self.state.attention + self.state.engagement) / 2.0
        self.state.instability = self.state.workload

        if self.state.attention > 0.7 and self.state.engagement > 0.6:
            self.state.state_name = "focused"
            self.state.phase = "focused"
            self.state.color = "#FF0055"
        elif self.state.workload > 0.7:
            self.state.state_name = "stressed"
            self.state.phase = "stressed"
            self.state.color = "#FF4400"
        elif self.state.attention < 0.3 and self.state.engagement < 0.3:
            self.state.state_name = "fatigued"
            self.state.phase = "fatigued"
            self.state.color = "#4488FF"
        elif self.state.engagement > 0.5:
            self.state.state_name = "engaged"
            self.state.phase = "engaged"
            self.state.color = "#00F0FF"
        elif self.state.attention > 0.5:
            self.state.state_name = "curious"
            self.state.phase = "curious"
            self.state.color = "#00FF88"
        else:
            self.state.state_name = "resting"
            self.state.phase = "resting"
            self.state.color = "#9933FF"

    def _generate_narrative(self):
        templates = {
            "focused": f"Enfoque profundo sintonizado. Elevando recursión a {self.state.fractal_dimension:.2f}.",
            "stressed": f"Carga de trabajo elevada. Modulando geometría en {self.state.fractal_dimension:.2f} para andamiaje de alivio.",
            "fatigued": f"Fatiga cerebral detectada. Reduciendo complejidad matemática para descanso cognitivo.",
            "engaged": f"Ecosistema en sintonía. Retroalimentación espacio-temporal estabilizada.",
            "curious": f"Sonda de curiosidad activa. Expandiendo fronteras del render fractal.",
            "resting": f"Monitoreo normal del espacio cognitivo. Atención y flujo constantes.",
        }
        return templates.get(self.state.state_name, "Ecosistema estable.")

    def set_manual(self, attention=None, engagement=None, load=None, valence=None, coherence=None, phase=None):
        if attention is not None:
            self.state.attention = max(0.05, min(0.95, attention))
        if engagement is not None:
            self.state.engagement = max(0.05, min(0.95, engagement))
        if load is not None:
            self.state.workload = max(0.05, min(0.95, load))
        if valence is not None:
            self.state.valence = max(0.05, min(0.95, valence))
        if coherence is not None:
            self.state.coherence = max(0.05, min(0.95, coherence))
        if phase is not None:
            self.state.phase = phase

        self._derive_state()
        manual_narratives = {
            "focused": "Modo ENFOQUE manual activado. Estabilizando vector cognitivo de precisión.",
            "stressed": "Modo sobrecarga estrés forzado. Activando simulación caótica.",
            "fatigued": "Fatiga simulada activa. Bajando ritmos de procesamiento.",
            "engaged": "Ajuste manual: Interacción y sintonía en nivel óptimo.",
            "curious": "Estímulo cognitivo: Modo exploración activa.",
            "resting": "Restableciendo red a estado de equilibrio basal.",
        }
        self.state.narrative = manual_narratives.get(self.state.state_name, "Control manual activo.")
        self.state.timestamp = time.time()
        return self.state

    def idle_drift(self):
        self._idle_counter += 1
        if self._idle_counter > 100:
            t = math.sin(self._idle_counter * 0.01) * 0.02
            self.state.attention = max(0.05, min(0.95, self.state.attention + t * 0.1))
            self.state.engagement = max(0.05, min(0.95, self.state.engagement + t * 0.05))
            self.state.workload = max(0.05, min(0.95, self.state.workload + t * 0.08))
            self._derive_state()


engine = FCSTNEngine()


async def broadcast_state():
    while True:
        engine.idle_drift()
        if engine.clients:
            msg = json.dumps({"type": "state", "data": engine.state.to_dict()})
            closed = set()
            for client in engine.clients:
                try:
                    await client.send(msg)
                except websockets.exceptions.ConnectionClosed:
                    closed.add(client)
            engine.clients -= closed
        await asyncio.sleep(0.05)


async def handler(websocket):
    engine.clients.add(websocket)
    log.info(f"Client connected. Total: {len(engine.clients)}")
    try:
        await websocket.send(json.dumps({"type": "state", "data": engine.state.to_dict()}))
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type", "")
                if msg_type == "input":
                    engine.process_input(data.get("text", ""), float(data.get("time_taken", 3.0)))
                elif msg_type == "voice":
                    engine.process_input(data.get("text", ""), 1.0)
                elif msg_type in ("control", "set"):
                    engine.set_manual(
                        attention=data.get("attention"),
                        engagement=data.get("engagement"),
                        load=data.get("load"),
                        valence=data.get("valence"),
                        coherence=data.get("coherence"),
                        phase=data.get("phase"),
                    )
                elif msg_type == "ping":
                    await websocket.send(json.dumps({"type": "pong"}))
                elif msg_type == "get_state":
                    await websocket.send(json.dumps({"type": "state", "data": engine.state.to_dict()}))
            except json.JSONDecodeError:
                pass
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        log.warning(f"Handler error: {e}")
    finally:
        engine.clients.discard(websocket)
        log.info(f"Client disconnected. Total: {len(engine.clients)}")


async def main():
    log.info("=" * 50)
    log.info("FCSTN Live Demo Server v2.0")
    log.info("WebSocket: ws://localhost:8765")
    log.info("Flutter App + Unity + Web Dashboard ready")
    log.info("=" * 50)
    async with websockets.serve(handler, "localhost", 8765):
        await broadcast_state()


if __name__ == "__main__":
    asyncio.run(main())
