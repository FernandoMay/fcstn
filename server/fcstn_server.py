"""
FCSTN Live Demo Server - Cognitive Engine with WebSocket broadcast
Connects 3D visualizer, Unity, and controller clients in real-time.
"""

import asyncio
import json
import websockets
import logging
import random
import time
import threading
from dataclasses import dataclass, field, asdict

# Try to import speech recognition
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s [FCSTN] %(message)s')
log = logging.getLogger('FCSTN')


@dataclass
class CognitiveState:
    attention: float = 0.5
    engagement: float = 0.5
    workload: float = 0.3
    fractal_dim: float = 2.5
    state_name: str = "neutral"
    color: str = "#9933FF"
    complexity: float = 0.5
    instability: float = 0.3
    timestamp: float = field(default_factory=time.time)
    narrative: str = "Red sintonizada. Ecosistema cognitivo estable."
    image_prompt: str = "fractal neuro-digital nexus, symmetrical geometry, network lattice"

    def to_dict(self):
        return asdict(self)


# Scientific keywords mapping to drive cognitive changes
KEYWORDS_MAP = {
    "caos": {"attention": 0.90, "engagement": 0.85, "workload": 0.90, "narrative": "Modulación caótica de espacio-tiempo. Inyectando entropía fractal."},
    "colapso": {"attention": 0.95, "engagement": 0.70, "workload": 0.95, "narrative": "Colapso inminente detectado. Espacio-tiempo comprimiéndose de golpe."},
    "estrés": {"attention": 0.85, "engagement": 0.60, "workload": 0.90, "narrative": "Alerta de estrés cognitivo. Elevando andamiaje geométrico protector."},
    "calma": {"attention": 0.25, "engagement": 0.30, "workload": 0.10, "narrative": "Sintonizando ondas delta/alfa. Geometría fractal estable y relajada."},
    "relajar": {"attention": 0.20, "engagement": 0.25, "workload": 0.08, "narrative": "Descompresión cognitiva activa. Ralentizando evolución temporal."},
    "paz": {"attention": 0.30, "engagement": 0.20, "workload": 0.15, "narrative": "Estabilización simétrica. Resonancia cerebral en modo pacífico."},
    "viaje": {"attention": 0.75, "engagement": 0.85, "workload": 0.40, "narrative": "Iniciando viaje espacio-temporal. Dimensiones fractales en expansión."},
    "aprender": {"attention": 0.85, "engagement": 0.80, "workload": 0.50, "narrative": "Modo aprendizaje profundo. Mapeando sinapsis de conocimiento en tiempo real."},
    "curioso": {"attention": 0.70, "engagement": 0.90, "workload": 0.35, "narrative": "Curiosidad intelectual activa. Explorando anomalías geométricas."},
    "mente": {"attention": 0.60, "engagement": 0.85, "workload": 0.30, "narrative": "Mapeando redes neuronales humanas. Simbiosis bio-digital establecida."},
    "conexión": {"attention": 0.65, "engagement": 0.90, "workload": 0.25, "narrative": "Conectividad total establecida. Transfiriendo señales cognitivas."},
    "agresivo": {"attention": 0.95, "engagement": 0.90, "workload": 0.85, "narrative": "Respuesta agresiva de la IA. Sobrecargando de luz y energía el render."}
}


class FCSTNEngine:
    def __init__(self):
        self.state = CognitiveState()
        self.time_step = 0
        self.history = []
        self.clients = set()

    def process_input(self, text: str, time_taken: float) -> CognitiveState:
        self.time_step += 1
        text_lower = text.lower() if text else ""
        
        # Check for explicit keywords first
        matched_keyword = None
        for kw, override in KEYWORDS_MAP.items():
            if kw in text_lower:
                matched_keyword = kw
                self.state.attention = override["attention"]
                self.state.engagement = override["engagement"]
                self.state.workload = override["workload"]
                self.state.narrative = override["narrative"]
                break

        if not matched_keyword:
            # Map response speed and text length to cognitive load
            speed_factor = max(0, min(1, 1.0 - (time_taken / 10.0)))
            text_complexity = min(1.0, len(text) / 100.0) if text else 0.3

            # Update cognitive metrics with smoothing
            self.state.attention = self.state.attention * 0.6 + (speed_factor * 0.6 + text_complexity * 0.4) * 0.4
            self.state.engagement = self.state.engagement * 0.6 + (0.5 + (speed_factor - 0.5) * 0.4 + text_complexity * 0.4) * 0.4
            self.state.workload = self.state.workload * 0.6 + (speed_factor * 0.5 + text_complexity * 0.5) * 0.4

            # Clamp
            self.state.attention = max(0.05, min(0.95, self.state.attention))
            self.state.engagement = max(0.05, min(0.95, self.state.engagement))
            self.state.workload = max(0.05, min(0.95, self.state.workload))

        # Derive fractal dimension from cognitive metrics
        self.state.fractal_dim = 2.0 + (self.state.attention * 0.6 + self.state.engagement * 0.4)
        self.state.complexity = (self.state.attention + self.state.engagement) / 2.0
        self.state.instability = self.state.workload

        # Classify cognitive state
        if self.state.attention > 0.7 and self.state.engagement > 0.6:
            self.state.state_name = "focused"
            self.state.color = "#FF0055"
        elif self.state.workload > 0.7:
            self.state.state_name = "stressed"
            self.state.color = "#FF4400"
        elif self.state.attention < 0.3 and self.state.engagement < 0.3:
            self.state.state_name = "fatigued"
            self.state.color = "#4488FF"
        elif self.state.engagement > 0.5:
            self.state.state_name = "engaged"
            self.state.color = "#00F0FF"
        elif self.state.attention > 0.5:
            self.state.state_name = "curious"
            self.state.color = "#00FF88"
        else:
            self.state.state_name = "neutral"
            self.state.color = "#9933FF"

        # Generate narrative if not set by keyword
        if not matched_keyword:
            narrative_templates = {
                "focused": f"Enfoque profundo sintonizado. Elevando recursión a {self.state.fractal_dim:.2f}.",
                "stressed": f"Carga de trabajo elevada. Modulando geometría en {self.state.fractal_dim:.2f} para andamiaje de alivio.",
                "fatigued": f"Fatiga cerebral detectada. Reduciendo complejidad matemática para descanso cognitivo.",
                "engaged": f"Ecosistema en sintonía. Retroalimentación espacio-temporal estabilizada.",
                "curious": f"Sonda de curiosidad activa. Expandiendo fronteras del render fractal.",
                "neutral": f"Monitoreo normal del espacio cognitivo. Atención y flujo constantes."
            }
            self.state.narrative = narrative_templates.get(self.state.state_name, "Ecosistema estable.")

        # Update Stable Diffusion/Generative seed prompt
        prompt_styles = {
            "focused": "highly detailed hyper-complex mandelbrot 3d fractal, glowing laser grids, cybernetic neural synapse network, crimson and cyan glow",
            "stressed": "chaotic unstable fractal geometry, red and orange energy sparks, exploding neural patterns, high friction glitch art",
            "fatigued": "soft minimalist geometry, smooth calm fluid gradients, soft blue ambient light, zen mandela shapes",
            "engaged": "interconnected neural network matrix, glowing purple and teal nodes, beautiful digital harmony, sleek tech line art",
            "curious": "exploratory deep space fractal zoom, biological neon plant fractal, green emerald bio-luminescence",
            "neutral": "symmetrical clean mathematical 3d rendering, violet neon lattice lines, balanced composition"
        }
        self.state.image_prompt = prompt_styles.get(self.state.state_name, prompt_styles["neutral"])

        # Add text context to prompt if available
        if text:
            self.state.image_prompt += f", inspired by '{text[:50]}'"

        self.state.timestamp = time.time()
        self.history.append(self.state.to_dict())
        if len(self.history) > 200:
            self.history.pop(0)

        log.info(f"State: {self.state.state_name.upper()} | "
                 f"Attn: {self.state.attention:.2f} | "
                 f"Eng: {self.state.engagement:.2f} | "
                 f"Wrk: {self.state.workload:.2f} | "
                 f"Dim: {self.state.fractal_dim:.2f} | "
                 f"Text: '{text}'")

        return self.state

    def set_manual(self, attention=None, engagement=None, workload=None):
        if attention is not None:
            self.state.attention = max(0.05, min(0.95, attention))
        if engagement is not None:
            self.state.engagement = max(0.05, min(0.95, engagement))
        if workload is not None:
            self.state.workload = max(0.05, min(0.95, workload))

        self.state.fractal_dim = 2.0 + (self.state.attention * 0.6 + self.state.engagement * 0.4)
        self.state.complexity = (self.state.attention + self.state.engagement) / 2.0
        self.state.instability = self.state.workload

        if self.state.attention > 0.7 and self.state.engagement > 0.6:
            self.state.state_name = "focused"
            self.state.color = "#FF0055"
        elif self.state.workload > 0.7:
            self.state.state_name = "stressed"
            self.state.color = "#FF4400"
        elif self.state.attention < 0.3 and self.state.engagement < 0.3:
            self.state.state_name = "fatigued"
            self.state.color = "#4488FF"
        elif self.state.engagement > 0.5:
            self.state.state_name = "engaged"
            self.state.color = "#00F0FF"
        elif self.state.attention > 0.5:
            self.state.state_name = "curious"
            self.state.color = "#00FF88"
        else:
            self.state.state_name = "neutral"
            self.state.color = "#9933FF"

        # Auto narratives for manual overrides
        manual_narratives = {
            "focused": "Modo ENFOQUE manual activado. Estabilizando vector cognitivo de precisión.",
            "stressed": "Modo sobrecarga estrés forzado. Activando simulación caótica.",
            "fatigued": "Fatiga simulada activa. Bajando ritmos de procesamiento.",
            "engaged": "Ajuste manual: Interacción y sintonía en nivel óptimo.",
            "curious": "Estímulo cognitivo: Modo exploración activa.",
            "neutral": "Restableciendo red a estado de equilibrio basal."
        }
        self.state.narrative = manual_narratives.get(self.state.state_name, "Control manual activo.")
        
        self.state.timestamp = time.time()
        return self.state


engine = FCSTNEngine()


# Background Speech Recognition Thread
def speech_listener_thread(engine_instance):
    if not SPEECH_AVAILABLE:
        log.info("SpeechRecognition library not detected on system. Headless voice server features disabled.")
        return

    log.info("Voice Input Thread: Initializing microphone...")
    try:
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        
        log.info("Voice Input Thread: Calibrating for ambient noise...")
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
        log.info("Voice Input Thread: Microphone online. Listening in background for commands...")

        while True:
            try:
                with mic as source:
                    # listen with timeout of 3s to keep loop responsive
                    audio = recognizer.listen(source, timeout=3.0, phrase_time_limit=8.0)
                
                log.info("Voice Input Thread: Audio captured, performing speech-to-text...")
                start_time = time.time()
                text = recognizer.recognize_google(audio, language="es-MX")
                duration = time.time() - start_time
                
                log.info(f"Voice Input Thread: Heard -> '{text}' (processing in {duration:.2f}s)")
                # Send to engine
                engine_instance.process_input(text, duration)
                
            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                # Audio heard but not understood
                pass
            except Exception as e:
                log.warning(f"Voice Input Thread error: {e}")
                time.sleep(1)
    except Exception as e:
        log.error(f"Failed to bind speech listener microphone: {e}. Ensure a microphone is connected.")


async def broadcast_state():
    """Periodically broadcast current state to all connected clients."""
    while True:
        if engine.clients:
            msg = json.dumps({"type": "state", "data": engine.state.to_dict()})
            closed = set()
            for client in engine.clients:
                try:
                    await client.send(msg)
                except websockets.exceptions.ConnectionClosed:
                    closed.add(client)
                except Exception:
                    closed.add(client)
            engine.clients -= closed
        await asyncio.sleep(0.05)  # 20fps updates


async def handler(websocket):
    engine.clients.add(websocket)
    log.info(f"Client connected. Total: {len(engine.clients)}")

    try:
        # Send initial state
        await websocket.send(json.dumps({"type": "state", "data": engine.state.to_dict()}))

        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type", "")

                if msg_type == "input":
                    text = data.get("text", "")
                    time_taken = float(data.get("time_taken", 3.0))
                    engine.process_input(text, time_taken)
                elif msg_type == "control":
                    engine.set_manual(
                        attention=data.get("attention"),
                        engagement=data.get("engagement"),
                        workload=data.get("workload"),
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
    log.info("FCSTN Live Demo Server")
    log.info("WebSocket: ws://localhost:8765")
    if SPEECH_AVAILABLE:
        log.info("Voice Control: ACTIVE (SpeechRecognition enabled)")
        # Start voice listener in background thread
        t = threading.Thread(target=speech_listener_thread, args=(engine,), daemon=True)
        t.start()
    else:
        log.info("Voice Control: INACTIVE (Run 'pip install SpeechRecognition PyAudio' to enable)")
    log.info("=" * 50)

    async with websockets.serve(handler, "localhost", 8765):
        await broadcast_state()


if __name__ == "__main__":
    asyncio.run(main())

