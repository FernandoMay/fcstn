"""FCSTN Live Server - Combined deployment for Render/Heroku.
Serves Flutter web app + WebSocket + REST API + BCI integration + Fractal Renderer.
"""
import os, sys, json, time, asyncio, logging, io, math, threading, concurrent.futures
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
import uvicorn

from server.fcstn_server import FCSTNEngine, CognitiveState, KEYWORDS_MAP
from shared.logger import get_logger, ROOT_LOG
from server.fractal_renderer import (render_mandelbrot, render_terrain, render_julia,
                                     render_multi_fractal, render_fractal_by_state,
                                     PALETTES)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [FCSTN] %(message)s")
log = get_logger("DEPLOY")

app = FastAPI(title="FCSTN Live Server", version="2.1.0")
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

# ---- Fractal image cache ----
_fractal_cache = {}
_fractal_cache_lock = threading.Lock()
_FRACTAL_CACHE_TTL = 2.0  # seconds
_fractal_executor = None

def _get_fractal_executor():
    global _fractal_executor
    if _fractal_executor is None:
        _fractal_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    return _fractal_executor

def _get_cached_fractal(key, render_func, *args, **kwargs):
    now = time.time()
    with _fractal_cache_lock:
        cached = _fractal_cache.get(key)
        if cached and (now - cached['time']) < _FRACTAL_CACHE_TTL:
            return cached['image']
    img = render_func(*args, **kwargs)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    with _fractal_cache_lock:
        _fractal_cache[key] = {'image': buf.getvalue(), 'time': now}
    return _fractal_cache[key]['image']

async def _render_fractal_async(key, render_func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_get_fractal_executor(), _get_cached_fractal, key, render_func, *args, **kwargs)

@app.get("/api/palettes")
async def list_palettes():
    return {"palettes": list(PALETTES.keys())}

@app.get("/api/fractal")
async def fractal(
    mode: str = Query("mandelbrot", description="mandelbrot, terrain, julia, multifractal"),
    palette: str = Query("cyberpunk", description="Color palette name"),
    width: int = Query(960, ge=64, le=3840),
    height: int = Query(540, ge=64, le=2160),
    zoom: float = Query(1.0, ge=0.01, le=1e6),
    cx: float = Query(-0.5, description="Center X"),
    cy: float = Query(0.0, description="Center Y"),
    rotation: float = Query(0.0, description="Rotation in radians"),
    max_iter: int = Query(256, ge=16, le=2048),
    julia_cx: float = Query(0.285),
    julia_cy: float = Query(0.01),
    palette_offset: float = Query(0.0, ge=0.0, le=1.0),
):
    log.info("Fractal requested", {"mode": mode, "palette": palette, "zoom": zoom})
    key = f"{mode}:{palette}:{width}:{height}:{zoom}:{cx}:{cy}:{rotation}:{max_iter}:{julia_cx}:{julia_cy}:{palette_offset}"
    try:
        loop = asyncio.get_event_loop()
        if mode == "terrain":
            img_data = await loop.run_in_executor(_get_fractal_executor(), _get_cached_fractal, key, render_terrain, width, height, palette, cx, cy, zoom, 60, 0.5)
        elif mode == "julia":
            img_data = await loop.run_in_executor(_get_fractal_executor(), _get_cached_fractal, key, render_julia, width, height, palette, max_iter, julia_cx, julia_cy, zoom, palette_offset)
        elif mode == "multifractal":
            img_data = await loop.run_in_executor(_get_fractal_executor(), _get_cached_fractal, key, render_multi_fractal, width, height, palette, "layers", cx, cy, zoom)
        else:
            img_data = await loop.run_in_executor(_get_fractal_executor(), _get_cached_fractal, key, render_mandelbrot, width, height, palette, max_iter, cx, cy, zoom, rotation, palette_offset)
        return Response(content=img_data, media_type="image/png")
    except Exception as e:
        log.error("Fractal render failed", {"error": str(e), "mode": mode})
        return Response(content=str(e), status_code=500)

@app.get("/api/fractal/state")
async def fractal_by_state(width: int = 960, height: int = 540):
    """Render fractal dynamically based on current cognitive state."""
    log.info("Fractal by state requested", {"state": engine.state.state_name})
    key = f"state:{engine.state.state_name}:{engine.state.attention:.2f}:{engine.state.engagement:.2f}:{time.time()//2}"
    state_dict = engine.state.to_dict()
    loop = asyncio.get_event_loop()
    img_data = await loop.run_in_executor(_get_fractal_executor(), _get_cached_fractal, key, render_fractal_by_state, state_dict, width, height)
    return Response(content=img_data, media_type="image/png")

@app.get("/api/fractal/map")
async def fractal_map_tile(
    zoom_level: int = Query(0, ge=0, le=8),
    tile_x: int = Query(0),
    tile_y: int = Query(0),
    palette: str = Query("earth"),
):
    """Minecraft-style tile map of the Mandelbrot set (256x256 tiles)."""
    log.info("Map tile requested", {"zoom": zoom_level, "x": tile_x, "y": tile_y})
    from server.fractal_renderer import render_map_tile
    try:
        loop = asyncio.get_event_loop()
        img = await loop.run_in_executor(_get_fractal_executor(), render_map_tile, zoom_level, tile_x, tile_y, palette)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        log.error("Map tile failed", {"error": str(e)})
        return Response(content=str(e), status_code=500)

@app.get("/health")
async def health():
    return {"status": "alive", "clients": len(manager.clients), "phase": engine.state.state_name}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    host = os.environ.get("HOST", "0.0.0.0")
    log.info("Starting server", {"host": host, "port": port})
    uvicorn.run(app, host=host, port=port, log_level="info")
