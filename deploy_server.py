"""FCSTN Live Server - Combined deployment for Render/Heroku.
Serves Flutter web app + WebSocket + REST API + BCI integration.
"""
import os, sys, json, time, asyncio, logging, threading
from pathlib import Path

# Add root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import FCSTN engine
from server.fcstn_server import FCSTNEngine, CognitiveState, KEYWORDS_MAP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [FCSTN] %(message)s")
log = logging.getLogger("FCSTN")

app = FastAPI(title="FCSTN Live Server", version="2.0.0")
engine = FCSTNEngine()

# Serve Flutter web build
flutter_dir = ROOT / "flutter_app" / "build" / "web"
if flutter_dir.exists():
    app.mount("/", StaticFiles(directory=str(flutter_dir), html=True), name="flutter")
    log.info(f"Serving Flutter app from {flutter_dir}")
else:
    log.warning("Flutter build not found. Run: cd flutter_app && flutter build web")

# Connection manager
class WSManager:
    def __init__(self):
        self.clients = set()
    async def broadcast(self, msg):
        closed = set()
        for c in self.clients:
            try:
                await c.send_text(msg)
            except:
                closed.add(c)
        self.clients -= closed

manager = WSManager()

# Broadcast cognitive state every 50ms
async def broadcast_loop():
    while True:
        engine.idle_drift()
        if manager.clients:
            state = {
                "type": "state",
                "data": {
                    "attention": round(engine.state.attention, 4),
                    "engagement": round(engine.state.engagement, 4),
                    "load": round(engine.state.workload, 4),
                    "workload": round(engine.state.workload, 4),
                    "valence": round(engine.state.valence, 4),
                    "coherence": round(engine.state.coherence, 4),
                    "fractal_dimension": round(engine.state.fractal_dimension, 4),
                    "fractal_dim": round(engine.state.fractal_dimension, 4),
                    "state_name": engine.state.state_name,
                    "phase": engine.state.phase or engine.state.state_name,
                    "color": engine.state.color or "#00F0FF",
                    "complexity": round(engine.state.complexity, 4),
                    "instability": round(engine.state.instability, 4),
                    "timestamp": time.time(),
                    "narrative": engine.state.narrative or "",
                    "image_prompt": engine.state.image_prompt or "",
                }
            }
            await manager.broadcast(json.dumps(state))
        await asyncio.sleep(0.05)

@app.on_event("startup")
async def startup():
    asyncio.create_task(broadcast_loop())
    log.info("FCSTN Live Server started")

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    manager.clients.add(ws)
    log.info(f"WS client connected. Total: {len(manager.clients)}")
    try:
        # Send initial state
        await ws.send_text(json.dumps({"type": "state", "data": engine.state.to_dict()}))
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                t = msg.get("type", "")
                if t in ("input", "voice"):
                    engine.process_input(msg.get("text", ""), float(msg.get("time_taken", 1.0)))
                elif t in ("control", "set"):
                    engine.set_manual(
                        attention=msg.get("attention"),
                        engagement=msg.get("engagement"),
                        load=msg.get("load"),
                        valence=msg.get("valence"),
                        coherence=msg.get("coherence"),
                        phase=msg.get("phase"),
                    )
                elif t == "ping":
                    await ws.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        manager.clients.discard(ws)
        log.info(f"WS client disconnected. Total: {len(manager.clients)}")

@app.get("/api/state")
async def get_state():
    return engine.state.to_dict()

@app.get("/api/voice")
async def voice_command(text: str = ""):
    engine.process_input(text, 1.0)
    return {"status": "ok", "state": engine.state.to_dict()}

@app.get("/health")
async def health():
    return {"status": "alive", "clients": len(manager.clients), "phase": engine.state.state_name}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    host = os.environ.get("HOST", "0.0.0.0")
    log.info(f"FCSTN Live Server on {host}:{port}")
    log.info(f"  Web: http://localhost:{port}")
    log.info(f"  WS:  ws://localhost:{port}/ws")
    log.info(f"  API: http://localhost:{port}/api/state")
    uvicorn.run(app, host=host, port=port, log_level="info")
