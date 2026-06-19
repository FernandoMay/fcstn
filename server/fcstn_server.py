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
from dataclasses import dataclass, field, asdict

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

    def to_dict(self):
        return asdict(self)


class FCSTNEngine:
    def __init__(self):
        self.state = CognitiveState()
        self.time_step = 0
        self.history = []
        self.clients = set()

    def process_input(self, text: str, time_taken: float) -> CognitiveState:
        self.time_step += 1
        # Map response speed to cognitive load
        speed_factor = max(0, min(1, 1.0 - (time_taken / 10.0)))
        text_complexity = min(1.0, len(text) / 100.0) if text else 0.3

        # Update cognitive metrics with smoothing
        self.state.attention = self.state.attention * 0.7 + (speed_factor * 0.7 + text_complexity * 0.3) * 0.3
        self.state.engagement = self.state.engagement * 0.7 + (0.5 + (speed_factor - 0.5) * 0.5 + text_complexity * 0.3) * 0.3
        self.state.workload = self.state.workload * 0.7 + (speed_factor * 0.6 + text_complexity * 0.4) * 0.3

        # Clamp
        self.state.attention = max(0.05, min(0.95, self.state.attention))
        self.state.engagement = max(0.05, min(0.95, self.state.engagement))
        self.state.workload = max(0.05, min(0.95, self.state.workload))

        # Derive fractal dimension from cognitive metrics
        self.state.fractal_dim = 2.0 + (self.state.attention * 0.5 + self.state.engagement * 0.5)
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

        self.state.timestamp = time.time()
        self.history.append(self.state.to_dict())
        if len(self.history) > 200:
            self.history.pop(0)

        log.info(f"State: {self.state.state_name.upper()} | "
                 f"Attn: {self.state.attention:.2f} | "
                 f"Eng: {self.state.engagement:.2f} | "
                 f"Wrk: {self.state.workload:.2f} | "
                 f"Dim: {self.state.fractal_dim:.2f}")

        return self.state

    def set_manual(self, attention=None, engagement=None, workload=None):
        if attention is not None:
            self.state.attention = max(0.05, min(0.95, attention))
        if engagement is not None:
            self.state.engagement = max(0.05, min(0.95, engagement))
        if workload is not None:
            self.state.workload = max(0.05, min(0.95, workload))

        self.state.fractal_dim = 2.0 + (self.state.attention * 0.5 + self.state.engagement * 0.5)
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

        self.state.timestamp = time.time()
        return self.state


engine = FCSTNEngine()


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
    log.info("=" * 50)

    async with websockets.serve(handler, "localhost", 8765):
        await broadcast_state()


if __name__ == "__main__":
    asyncio.run(main())
