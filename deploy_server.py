"""FCSTN Live Server - Combined deployment for Render/Heroku.
Serves Flutter web app + WebSocket + REST API + BCI integration.
"""
import os, sys, json, time, asyncio, logging
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from server.fcstn_server import FCSTNEngine, CognitiveState, KEYWORDS_MAP
from shared.logger import get_logger, ROOT_LOG

logging.basicConfig(level=logging.INFO, format="%(asctime)s [FCSTN] %(message)s")
log = get_logger("DEPLOY")

app = FastAPI(title="FCSTN Live Server", version="2.0.0")
engine = FCSTNEngine()

flutter_dir = ROOT / "flutter_app" / "build" / "web"
if flutter_dir.exists():
    app.mount("/", StaticFiles(directory=str(flutter_dir), html=True), name="flutter")
    log.info("Serving Flutter app", {"dir": str(flutter_dir)})
else:
    log.warn("Flutter build not found", {"hint": "cd flutter_app && flutter build web"})

class WSManager:
    def __init__(self):
        self.clients = {}
        self._counter = 0

    def add(self, ws, client_id):
        self.clients[client_id] = ws

    def remove(self, client_id):
        self.clients.pop(client_id, None)

    async def broadcast(self, msg):
        closed = []
        for cid, c in self.clients.items():
            try:
                await c.send_text(msg)
            except Exception as e:
                log.warn("Broadcast failed", {"client": cid, "error": str(e)})
                closed.append(cid)
        for cid in closed:
            self.clients.pop(cid, None)
        return len(self.clients)

manager = WSManager()

async def broadcast_loop():
    cycle = 0
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
            n = await manager.broadcast(json.dumps(state))
            if cycle % 200 == 0:
                log.debug("Broadcast cycle", {"clients": n, "state": engine.state.state_name})
        else:
            if cycle % 400 == 0:
                log.debug("Idle (no clients)")
        cycle += 1
        await asyncio.sleep(0.05)

@app.on_event("startup")
async def startup():
    asyncio.create_task(broadcast_loop())
    log.info("FCSTN Live Server started", {"version": "2.0.0"})

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    client_id = f"ws-{id(ws):x}"
    manager.add(ws, client_id)
    log.info("WS client connected", {"client": client_id, "total": len(manager.clients)})
    start_time = time.time()
    msg_count = 0
    try:
        await ws.send_text(json.dumps({"type": "state", "data": engine.state.to_dict()}))
        while True:
            data = await ws.receive_text()
            msg_count += 1
            try:
                msg = json.loads(data)
                t = msg.get("type", "")
                if t in ("input", "voice"):
                    text = msg.get("text", "")
                    log.info("Voice command", {"client": client_id, "text": text, "command": text.lower().strip()})
                    engine.process_input(text, float(msg.get("time_taken", 1.0)))
                elif t in ("control", "set"):
                    params = {k: msg[k] for k in ("attention","engagement","load","valence","coherence","phase") if k in msg}
                    log.info("Manual set", {"client": client_id, **params})
                    engine.set_manual(**params)
                elif t == "ping":
                    await ws.send_text(json.dumps({"type": "pong"}))
                    log.debug("Ping/Pong", {"client": client_id})
                else:
                    log.debug("Unknown message type", {"client": client_id, "type": t})
            except json.JSONDecodeError:
                log.warn("Invalid JSON", {"client": client_id, "raw": data[:100]})
    except WebSocketDisconnect:
        log.info("WS client disconnected", {"client": client_id, "duration_s": round(time.time() - start_time, 1), "messages": msg_count})
    except Exception as e:
        log.error("WS error", {"client": client_id, "error": str(e)})
    finally:
        manager.remove(client_id)
        log.info("WS client cleaned up", {"client": client_id, "remaining": len(manager.clients)})

@app.get("/api/state")
async def get_state():
    s = engine.state.to_dict()
    log.debug("API state requested", {"state": s.get("state_name")})
    return s

@app.get("/api/voice")
async def voice_command(text: str = ""):
    log.info("API voice command", {"text": text})
    engine.process_input(text, 1.0)
    return {"status": "ok", "state": engine.state.to_dict()}

@app.get("/api/logs")
async def get_logs(n: int = 100, level: str = ""):
    entries = ROOT_LOG.recent(n)
    if level:
        entries = [e for e in entries if e.level == level.upper()]
    return {"count": len(entries), "logs": [{
        "t": e.timestamp, "l": e.level, "s": e.source, "m": e.message, "d": e.data
    } for e in entries]}

@app.get("/health")
async def health():
    return {"status": "alive", "clients": len(manager.clients), "phase": engine.state.state_name}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    host = os.environ.get("HOST", "0.0.0.0")
    log.info("Starting server", {"host": host, "port": port})
    uvicorn.run(app, host=host, port=port, log_level="info")
