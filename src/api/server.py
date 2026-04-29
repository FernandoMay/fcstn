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
        for c_id, coalition in final_coalitions.items():
            nodes.append({"id": c_id, "label": f"{coalition.coalition_type.value} ({len(coalition.members)})", "group": "coalition"})
            for member in coalition.members:
                nodes.append({"id": member.id, "label": member.name, "group": member.agent_type.value})
                edges.append({"source": c_id, "target": member.id})
        self.coalition_graph = {"nodes": nodes, "edges": edges}

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
        # We leave zoom and center alone so the user can navigate them freely
        if state.current_cognitive_features:
            state.fractal_params.max_iterations = int(64 + state.current_cognitive_features.attention_index * 192)
            
        # Broadcast state via WS
        if state.current_cognitive_features:
            msg = {
                "type": "cognitive_state",
                "data": {
                    "attention": state.current_cognitive_features.attention_index,
                    "engagement": state.current_cognitive_features.engagement_level,
                    "workload": state.current_cognitive_features.workload,
                    "state": state.current_cognitive_features.cognitive_state.value,
                    "iterations": state.fractal_params.max_iterations,
                    "zoom": state.fractal_params.zoom,
                    "x": state.fractal_params.center[0],
                    "y": state.fractal_params.center[1],
                    "override": state.manual_override
                }
            }
            await manager.broadcast(json.dumps(msg))
            
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
