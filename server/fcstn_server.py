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

from shared.logger import get_logger

logging.basicConfig(level=logging.INFO, format='%(asctime)s [FCSTN] %(message)s')
log = get_logger("ENGINE")


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
            "attention": round(self.attention, 4),
            "engagement": round(self.engagement, 4),
            "load": round(self.workload, 4),
            "workload": round(self.workload, 4),
            "valence": round(self.valence, 4),
            "coherence": round(self.coherence, 4),
            "fractal_dimension": round(self.fractal_dimension, 4),
            "fractal_dim": round(self.fractal_dimension, 4),
            "state_name": self.state_name,
            "phase": self.phase,
            "color": self.color,
            "complexity": round(self.complexity, 4),
            "instability": round(self.instability, 4),
            "timestamp": round(self.timestamp, 4),
            "narrative": self.narrative,
            "image_prompt": self.image_prompt,
        }


KEYWORDS_MAP = {
    "caos": {"load": 0.95, "attention": 0.90, "engagement": 0.85, "narrative": "Modulacion caotica de espacio-tiempo. Inyectando entropia fractal."},
    "colapso": {"load": 0.95, "attention": 0.95, "engagement": 0.70, "narrative": "Colapso inminente detectado. Espacio-tiempo comprimiendose de golpe."},
    "estres": {"load": 0.90, "attention": 0.85, "engagement": 0.60, "narrative": "Alerta de estres cognitivo. Elevando andamiaje geometrico protector."},
    "calma": {"load": 0.10, "attention": 0.25, "engagement": 0.30, "narrative": "Sintonizando ondas delta/alfa. Geometria fractal estable y relajada."},
    "relajar": {"load": 0.08, "attention": 0.20, "engagement": 0.25, "narrative": "Descompresion cognitiva activa. Ralentizando evolucion temporal."},
    "paz": {"load": 0.15, "attention": 0.30, "engagement": 0.20, "narrative": "Estabilizacion simetrica. Resonancia cerebral en modo pacifico."},
    "viaje": {"load": 0.40, "attention": 0.75, "engagement": 0.85, "narrative": "Iniciando viaje espacio-temporal. Dimensiones fractales en expansion."},
    "aprender": {"load": 0.50, "attention": 0.85, "engagement": 0.80, "narrative": "Modo aprendizaje profundo. Mapeando sinapsis de conocimiento en tiempo real."},
    "curioso": {"load": 0.35, "attention": 0.70, "engagement": 0.90, "narrative": "Curiosidad intelectual activa. Explorando anomalias geometricas."},
    "mente": {"load": 0.30, "attention": 0.60, "engagement": 0.85, "narrative": "Mapeando redes neuronales humanas. Simbiosis bio-digital establecida."},
    "conexion": {"load": 0.25, "attention": 0.65, "engagement": 0.90, "narrative": "Conectividad total establecida. Transfiriendo senales cognitivas."},
    "foco": {"load": 0.30, "attention": 0.95, "engagement": 0.80, "narrative": "Atencion quirurgica activa. Precision fractal milimetrica."},
    "explosion": {"load": 0.95, "attention": 0.95, "engagement": 0.95, "valence": 0.90, "narrative": "EXPLOSION COGNITIVA - Todas las metricas al maximo. Teatro cuantico activado."},
    "todas maximas": {"load": 0.95, "attention": 0.95, "engagement": 0.95, "valence": 0.90, "coherence": 0.90, "narrative": "EXPLOSION COGNITIVA - Todas las metricas al maximo. Teatro cuantico activado."},
    "todas minimas": {"load": 0.05, "attention": 0.05, "engagement": 0.05, "valence": 0.10, "coherence": 0.10, "narrative": "Reposo total cognitivo. Sistema en standby."},
    "reposo": {"load": 0.05, "attention": 0.05, "engagement": 0.05, "valence": 0.10, "coherence": 0.10, "narrative": "Reposo total cognitivo. Sistema en standby."},
    "creativo": {"load": 0.30, "attention": 0.60, "engagement": 0.80, "valence": 0.95, "narrative": "Creatividad desatada. Valencia maxima. Nuevas geometrias emergiendo."},
    "equilibrio": {"load": 0.30, "attention": 0.50, "engagement": 0.50, "valence": 0.50, "coherence": 0.85, "narrative": "Coherencia neural establecida. Armonia fractal equilibrada."},
    "atencion": {"load": 0.30, "attention": 0.90, "engagement": 0.70, "narrative": "Alta atencion detectada. Precision y enfoque maximo."},
    "alta atencion": {"load": 0.30, "attention": 0.90, "engagement": 0.70, "narrative": "Alta atencion detectada. Precision y enfoque maximo."},
    "carga maxima": {"load": 0.90, "attention": 0.80, "engagement": 0.75, "narrative": "Carga maxima activada. Sobrecarga controlada del sistema."},
    "carga baja": {"load": 0.05, "attention": 0.30, "engagement": 0.35, "narrative": "Carga baja. Sistema en modo descanso profundo."},
    "alta valencia": {"load": 0.25, "attention": 0.55, "engagement": 0.70, "valence": 0.90, "narrative": "Valencia emocional elevada. Experiencia positiva amplificada."},
    "coherencia alta": {"load": 0.25, "attention": 0.50, "engagement": 0.50, "coherence": 0.85, "narrative": "Coherencia neural optima. Sincronizacion hemisferica total."},
    "agresivo": {"load": 0.85, "attention": 0.95, "engagement": 0.90, "narrative": "Respuesta agresiva de la IA. Sobrecargando de luz y energia el render."},
}


class FCSTNEngine:
    def __init__(self):
        self.state = CognitiveState()
        self._idle_counter = 0
        self.time_step = 0
        self.history = []
        self.clients = set()
        log.info("Engine initialized", {"initial_state": self.state.state_name})

    def process_input(self, text: str, time_taken: float) -> CognitiveState:
        self.time_step += 1
        self._idle_counter = 0
        text_lower = text.lower() if text else ""
        log.info("Processing input", {"step": self.time_step, "text": text, "time_taken": time_taken})

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

        if matched_keyword:
            log.info("Keyword matched", {"keyword": matched_keyword, "values": {k: v for k, v in override.items() if k != "narrative"}})
        else:
            speed_factor = max(0, min(1, 1.0 - (time_taken / 10.0)))
            text_complexity = min(1.0, len(text) / 100.0) if text else 0.3
            prev = {"attention": self.state.attention, "engagement": self.state.engagement, "workload": self.state.workload}
            self.state.attention = self.state.attention * 0.6 + (speed_factor * 0.6 + text_complexity * 0.4) * 0.4
            self.state.engagement = self.state.engagement * 0.6 + (0.5 + (speed_factor - 0.5) * 0.4 + text_complexity * 0.4) * 0.4
            self.state.workload = self.state.workload * 0.6 + (speed_factor * 0.5 + text_complexity * 0.5) * 0.4

            self.state.attention = max(0.05, min(0.95, self.state.attention))
            self.state.engagement = max(0.05, min(0.95, self.state.engagement))
            self.state.workload = max(0.05, min(0.95, self.state.workload))
            log.debug("Free text processed", {"prev": prev, "now": {"attention": self.state.attention, "engagement": self.state.engagement, "workload": self.state.workload}, "speed_factor": speed_factor, "complexity": text_complexity})

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

        prev_name = self.state.state_name
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

        if prev_name != self.state.state_name:
            log.info("State transition", {"from": prev_name, "to": self.state.state_name, "attention": round(self.state.attention, 2), "engagement": round(self.state.engagement, 2)})

    def _generate_narrative(self):
        templates = {
            "focused": f"Enfoque profundo sintonizado. Elevando recursion a {self.state.fractal_dimension:.2f}.",
            "stressed": f"Carga de trabajo elevada. Modulando geometria en {self.state.fractal_dimension:.2f} para andamiaje de alivio.",
            "fatigued": f"Fatiga cerebral detectada. Reduciendo complejidad matematica para descanso cognitivo.",
            "engaged": f"Ecosistema en sintonia. Retroalimentacion espacio-temporal estabilizada.",
            "curious": f"Sonda de curiosidad activa. Expandiendo fronteras del render fractal.",
            "resting": f"Monitoreo normal del espacio cognitivo. Atencion y flujo constantes.",
        }
        return templates.get(self.state.state_name, "Ecosistema estable.")

    def set_manual(self, attention=None, engagement=None, load=None, valence=None, coherence=None, phase=None):
        params = {}
        if attention is not None:
            self.state.attention = max(0.05, min(0.95, attention))
            params["attention"] = attention
        if engagement is not None:
            self.state.engagement = max(0.05, min(0.95, engagement))
            params["engagement"] = engagement
        if load is not None:
            self.state.workload = max(0.05, min(0.95, load))
            params["load"] = load
        if valence is not None:
            self.state.valence = max(0.05, min(0.95, valence))
            params["valence"] = valence
        if coherence is not None:
            self.state.coherence = max(0.05, min(0.95, coherence))
            params["coherence"] = coherence
        if phase is not None:
            self.state.phase = phase
            params["phase"] = phase

        log.info("Manual set", params)
        self._derive_state()
        manual_narratives = {
            "focused": "Modo ENFOQUE manual activado. Estabilizando vector cognitivo de precision.",
            "stressed": "Modo sobrecarga estres forzado. Activando simulacion caotica.",
            "fatigued": "Fatiga simulada activa. Bajando ritmos de procesamiento.",
            "engaged": "Ajuste manual: Interaccion y sintonia en nivel optimo.",
            "curious": "Estimulo cognitivo: Modo exploracion activa.",
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
            if self._idle_counter % 200 == 0:
                log.debug("Idle drift", {"counter": self._idle_counter, "state": self.state.state_name})


engine = FCSTNEngine()


async def broadcast_state():
    cycle = 0
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
            if cycle % 200 == 0:
                log.debug("Broadcast", {"clients": len(engine.clients), "state": engine.state.state_name})
        cycle += 1
        await asyncio.sleep(0.05)


async def handler(websocket):
    engine.clients.add(websocket)
    cid = f"ws-{id(websocket):x}"
    log.info("Client connected", {"client": cid, "total": len(engine.clients)})
    start = time.time()
    msg_count = 0
    try:
        await websocket.send(json.dumps({"type": "state", "data": engine.state.to_dict()}))
        async for message in websocket:
            msg_count += 1
            try:
                data = json.loads(message)
                msg_type = data.get("type", "")
                if msg_type == "input":
                    log.info("Input received", {"client": cid, "text": data.get("text", "")})
                    engine.process_input(data.get("text", ""), float(data.get("time_taken", 3.0)))
                elif msg_type == "voice":
                    text = data.get("text", "")
                    log.info("Voice command", {"client": cid, "text": text})
                    engine.process_input(text, 1.0)
                elif msg_type in ("control", "set"):
                    log.info("Control message", {"client": cid, "data": {k: data[k] for k in ("attention","engagement","load","valence","coherence","phase") if k in data}})
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
                else:
                    log.debug("Unknown message type", {"client": cid, "type": msg_type})
            except json.JSONDecodeError:
                log.warn("Invalid JSON from client", {"client": cid})
    except websockets.exceptions.ConnectionClosed:
        log.info("Client disconnected", {"client": cid, "duration_s": round(time.time() - start, 1), "messages": msg_count})
    except Exception as e:
        log.error("Handler error", {"client": cid, "error": str(e)})
    finally:
        engine.clients.discard(websocket)
        log.info("Client cleaned up", {"client": cid, "remaining": len(engine.clients)})


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
