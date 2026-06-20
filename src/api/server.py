import io
import time
import asyncio
import json
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image

# Import FCSTN components
import sys
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from src.core.fractal_engine.mandelbrot import MandelbrotGenerator, FractalParameters, create_color_mapping
from src.core.ndan_interface.bci_processor import NDANInterface, generate_synthetic_eeg, CognitiveFeatures, CognitiveState

# Import keyword map from server
try:
    from server.fcstn_server import KEYWORDS_MAP
except ImportError:
    # Inline fallback if server module not directly importable
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

from src.core.coalition_network.coalition_formation import (
    Agent, AgentType, CoalitionFormationGame
)

app = FastAPI(title="FCSTN Interactive Dashboard", version="2.0.0")

# Mount Static UI
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/dashboard", StaticFiles(directory=str(static_dir), html=True), name="static")

# Connection Manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

# Global Shared State
class SimulationState:
    def __init__(self):
        self.ndan = NDANInterface(sampling_rate=250.0)
        self.fractal_params = FractalParameters(
            resolution=(640, 480),
            max_iterations=128,
            center=(-0.5, 0.0),
            zoom=1.0
        )
        self.fractal_gen = MandelbrotGenerator(self.fractal_params, use_gpu=False)
        self.current_cognitive_features = None
        
        # Manual Control Flags
        self.manual_override = False
        self.manual_attention = 0.5
        self.manual_engagement = 0.5
        self.manual_workload = 0.5
        
        # Procedural Narratives and prompts
        self.last_narrative = "Red sintonizada. Ecosistema cognitivo estable."
        self.last_image_prompt = "fractal neuro-digital nexus, symmetrical geometry, network lattice"
        
        # Coalition State
        self.agent_counter = 3
        self.agents = [
            Agent("Player1", AgentType.HUMAN, ["perception"], {"compute": 10}),
            Agent("Player2", AgentType.HUMAN, ["perception"], {"compute": 10}),
            Agent("CloudServer", AgentType.CLOUD_NODE, ["ml_training"], {"compute": 500})
        ]
        self.coalition_graph = {"nodes": [], "edges": []}
        self.recompute_coalitions()

    def recompute_coalitions(self):
        game = CoalitionFormationGame(self.agents)
        final_coalitions = game.run_merge_and_split(max_iterations=5)
        nodes, edges = [], []
        agent_lookup = {a.id: a for a in self.agents}
        for c_id, coalition in final_coalitions.items():
            nodes.append({"id": c_id, "label": f"{coalition.coalition_type.value} ({len(coalition.members)})", "group": "coalition"})
            for member_id in coalition.members:
                agent = agent_lookup.get(member_id)
                if agent:
                    nodes.append({"id": agent.id, "label": agent.id, "group": agent.agent_type.value})
                    edges.append({"source": c_id, "target": agent.id})
        self.coalition_graph = {"nodes": nodes, "edges": edges}

    def process_voice_input(self, text: str, time_taken: float):
        text_lower = text.lower() if text else ""
        
        matched_keyword = None
        for kw, override in KEYWORDS_MAP.items():
            if kw in text_lower:
                matched_keyword = kw
                self.manual_attention = override["attention"]
                self.manual_engagement = override["engagement"]
                self.manual_workload = override["workload"]
                self.last_narrative = override["narrative"]
                self.manual_override = True
                break

        if not matched_keyword:
            speed_factor = max(0, min(1, 1.0 - (time_taken / 10.0)))
            text_complexity = min(1.0, len(text) / 100.0) if text else 0.3

            # Modulate metrics based on audio speed and length
            self.manual_attention = self.manual_attention * 0.6 + (speed_factor * 0.6 + text_complexity * 0.4) * 0.4
            self.manual_engagement = self.manual_engagement * 0.6 + (0.5 + (speed_factor - 0.5) * 0.4 + text_complexity * 0.4) * 0.4
            self.manual_workload = self.manual_workload * 0.6 + (speed_factor * 0.5 + text_complexity * 0.5) * 0.4

            self.manual_attention = max(0.05, min(0.95, self.manual_attention))
            self.manual_engagement = max(0.05, min(0.95, self.manual_engagement))
            self.manual_workload = max(0.05, min(0.95, self.manual_workload))
            self.manual_override = True

        # Determine cognitive state name based on metrics
        state_str = "neutral"
        if self.manual_attention > 0.7 and self.manual_engagement > 0.6:
            state_str = "focused"
        elif self.manual_workload > 0.7:
            state_str = "stressed"
        elif self.manual_attention < 0.3 and self.manual_engagement < 0.3:
            state_str = "fatigued"
        elif self.manual_engagement > 0.5:
            state_str = "engaged"
        elif self.manual_attention > 0.5:
            self.state_str = "curious"

        # Narrative formatting if not keyword-driven
        if not matched_keyword:
            fractal_dim = 2.0 + (self.manual_attention * 0.6 + self.manual_engagement * 0.4)
            narrative_templates = {
                "focused": f"Enfoque profundo sintonizado. Elevando recursión a {fractal_dim:.2f}.",
                "stressed": f"Carga de trabajo elevada. Modulando geometría en {fractal_dim:.2f} para andamiaje de alivio.",
                "fatigued": f"Fatiga cerebral detectada. Reduciendo complejidad matemática para descanso cognitivo.",
                "engaged": f"Ecosistema en sintonía. Retroalimentación espacio-temporal de voz estabilizada.",
                "curious": f"Sonda de curiosidad activa. Expandiendo fronteras del render fractal.",
                "neutral": f"Monitoreo de voz del espacio cognitivo. Atención y flujo constantes."
            }
            self.last_narrative = narrative_templates.get(state_str, "Ecosistema estable.")

        # Update prompt styles
        prompt_styles = {
            "focused": "highly detailed hyper-complex mandelbrot 3d fractal, glowing laser grids, cybernetic neural synapse network, crimson and cyan glow",
            "stressed": "chaotic unstable fractal geometry, red and orange energy sparks, exploding neural patterns, high friction glitch art",
            "fatigued": "soft minimalist geometry, smooth calm fluid gradients, soft blue ambient light, zen mandela shapes",
            "engaged": "interconnected neural network matrix, glowing purple and teal nodes, beautiful digital harmony, sleek tech line art",
            "curious": "exploratory deep space fractal zoom, biological neon plant fractal, green emerald bio-luminescence",
            "neutral": "symmetrical clean mathematical 3d rendering, violet neon lattice lines, balanced composition"
        }
        self.last_image_prompt = prompt_styles.get(state_str, prompt_styles["neutral"])
        if text:
            self.last_image_prompt += f", inspired by '{text[:50]}'"


state = SimulationState()

# Background Simulation Loop
async def update_simulation():
    while True:
        if state.manual_override:
            # Construct a manual state
            state_val = CognitiveState.NEUTRAL
            if state.manual_attention > 0.7 and state.manual_engagement > 0.6:
                state_val = CognitiveState.FOCUSED
            elif state.manual_workload > 0.7:
                state_val = CognitiveState.STRESSED
            elif state.manual_attention < 0.3 and state.manual_engagement < 0.3:
                state_val = CognitiveState.FATIGUED
            elif state.manual_engagement > 0.5:
                state_val = CognitiveState.ENGAGED
                
            features = CognitiveFeatures(
                alpha_power=0.5, beta_power=0.5, theta_power=0.5, gamma_power=0.5,
                attention_index=state.manual_attention,
                engagement_level=state.manual_engagement,
                workload=state.manual_workload,
                emotional_valence=0.0,
                cognitive_state=state_val
            )
            state.current_cognitive_features = features
        else:
            signal = generate_synthetic_eeg(duration=1.0)
            features = state.ndan.process_signal(signal)
            state.current_cognitive_features = features
            
        # Update fractal details (only max_iterations is tied to attention)
        if state.current_cognitive_features:
            state.fractal_params.max_iterations = int(64 + state.current_cognitive_features.attention_index * 192)
            
        # Broadcast state via WS
        if state.current_cognitive_features:
            state_name = state.current_cognitive_features.cognitive_state.value
            color_map = {
                "focused": "#FF0055",
                "stressed": "#FF4400",
                "fatigued": "#4488FF",
                "engaged": "#00F0FF",
                "curious": "#00FF88",
                "neutral": "#9933FF"
            }
            color_hex = color_map.get(state_name, "#9933FF")
            fractal_dim = 2.0 + (state.current_cognitive_features.attention_index * 0.6 + state.current_cognitive_features.engagement_level * 0.4)
            instability = state.current_cognitive_features.workload
            complexity = (state.current_cognitive_features.attention_index + state.current_cognitive_features.engagement_level) / 2.0

            if not state.manual_override:
                narrative_templates = {
                    "focused": f"Enfoque profundo sintonizado. Elevando recursión a {fractal_dim:.2f}.",
                    "stressed": f"Carga de trabajo elevada. Modulando geometría en {fractal_dim:.2f} para andamiaje de alivio.",
                    "fatigued": f"Fatiga cerebral detectada. Reduciendo complejidad matemática para descanso cognitivo.",
                    "engaged": f"Ecosistema en sintonía. Retroalimentación espacio-temporal estabilizada.",
                    "curious": f"Sonda de curiosidad activa. Expandiendo fronteras del render fractal.",
                    "neutral": f"Monitoreo normal del espacio cognitivo. Atención y flujo constantes."
                }
                state.last_narrative = narrative_templates.get(state_name, "Ecosistema estable.")
                
                prompt_styles = {
                    "focused": "highly detailed hyper-complex mandelbrot 3d fractal, glowing laser grids, cybernetic neural synapse network, crimson and cyan glow",
                    "stressed": "chaotic unstable fractal geometry, red and orange energy sparks, exploding neural patterns, high friction glitch art",
                    "fatigued": "soft minimalist geometry, smooth calm fluid gradients, soft blue ambient light, zen mandela shapes",
                    "engaged": "interconnected neural network matrix, glowing purple and teal nodes, beautiful digital harmony, sleek tech line art",
                    "curious": "exploratory deep space fractal zoom, biological neon plant fractal, green emerald bio-luminescence",
                    "neutral": "symmetrical clean mathematical 3d rendering, violet neon lattice lines, balanced composition"
                }
                state.last_image_prompt = prompt_styles.get(state_name, prompt_styles["neutral"])

            # Web dashboard message
            msg = {
                "type": "cognitive_state",
                "data": {
                    "attention": state.current_cognitive_features.attention_index,
                    "engagement": state.current_cognitive_features.engagement_level,
                    "workload": state.current_cognitive_features.workload,
                    "state": state_name,
                    "iterations": state.fractal_params.max_iterations,
                    "zoom": state.fractal_params.zoom,
                    "x": state.fractal_params.center[0],
                    "y": state.fractal_params.center[1],
                    "override": state.manual_override,
                    "color": color_hex,
                    "fractal_dim": fractal_dim,
                    "complexity": complexity,
                    "instability": instability,
                    "narrative": state.last_narrative,
                    "image_prompt": state.last_image_prompt
                }
            }
            await manager.broadcast(json.dumps(msg))
            
            # Unity standard message envelope (allows Unity Client to connect directly to 8000/ws)
            unity_msg = {
                "type": "state",
                "data": {
                    "attention": state.current_cognitive_features.attention_index,
                    "engagement": state.current_cognitive_features.engagement_level,
                    "workload": state.current_cognitive_features.workload,
                    "fractal_dim": fractal_dim,
                    "state_name": state_name,
                    "color": color_hex,
                    "complexity": complexity,
                    "instability": instability,
                    "timestamp": time.time(),
                    "narrative": state.last_narrative,
                    "image_prompt": state.last_image_prompt
                }
            }
            await manager.broadcast(json.dumps(unity_msg))
            
        await asyncio.sleep(0.1) # 10Hz update rate

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_simulation())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            cmd = json.loads(data)
            
            if cmd["action"] == "toggle_override":
                state.manual_override = cmd["value"]
            elif cmd["action"] == "set_metric":
                metric = cmd["metric"]
                val = float(cmd["value"])
                if metric == "attention": state.manual_attention = val
                if metric == "engagement": state.manual_engagement = val
                if metric == "workload": state.manual_workload = val
            elif cmd["action"] == "voice_input":
                text = cmd.get("text", "")
                time_taken = float(cmd.get("time_taken", 3.0))
                state.process_voice_input(text, time_taken)
            elif cmd["action"] == "add_agent":
                agent_type = AgentType(cmd["type"])
                state.agent_counter += 1
                new_agent = Agent(f"Node_{state.agent_counter}", agent_type, ["task"], {"compute": 50})
                state.agents.append(new_agent)
                state.recompute_coalitions()
                await manager.broadcast(json.dumps({"type": "coalition_update", "data": state.coalition_graph}))
            elif cmd["action"] == "remove_agent":
                if len(state.agents) > 0:
                    state.agents.pop() # Remove last
                    state.recompute_coalitions()
                    await manager.broadcast(json.dumps({"type": "coalition_update", "data": state.coalition_graph}))
            elif cmd["action"] == "get_coalition":
                await websocket.send_text(json.dumps({"type": "coalition_update", "data": state.coalition_graph}))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/fractal")
async def get_fractal(x: float = None, y: float = None, zoom: float = None):
    """Returns dynamic fractal based on passed navigation coordinates or internal state"""
    try:
        # Update navigation params if provided
        if x is not None and y is not None:
            state.fractal_params.center = (x, y)
        if zoom is not None:
            state.fractal_params.zoom = zoom
            
        fractal_array = state.fractal_gen.generate_smooth()
        
        # Color mapping depends on engagement
        colormap = 'inferno' if state.current_cognitive_features and state.current_cognitive_features.engagement_level > 0.6 else 'twilight'
        colored = create_color_mapping(fractal_array, colormap=colormap)
        
        img = Image.fromarray(colored)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        logging.error(f"Error generating fractal: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

