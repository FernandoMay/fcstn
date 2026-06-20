"""FCSTN BCI WebSocket Server - Real brain signals everything.

Broadcasts cognitive state, Mandelbrot path, music params, game maps,
dream visuals, and image prompts over WebSocket to all clients.
"""

import asyncio
import json
import logging
import time
import threading
import numpy as np
import websockets

from .acquisition import create_source, MuseSource, RecordedSource
from .signal import SignalProcessor
from .fractal_mapper import FractalMapper
from .generators import (
    ImagePromptGenerator, MusicGenerator,
    TextGenerator, GameMapGenerator, DreamGenerator
)
from shared.logger import get_logger

log = get_logger("BCI")


class BCIBrainServer:
    """Integrates real EEG acquisition processing multi-modal generation WebSocket broadcast."""

    def __init__(self, ws_port=8766, source_type='recorded', source_kwargs=None):
        self.ws_port = ws_port
        self.source_type = source_type
        self.source_kwargs = source_kwargs or {}

        self.source = None
        self.processor = None
        self.mapper = FractalMapper()
        self.image_gen = ImagePromptGenerator()
        self.music_gen = MusicGenerator()
        self.text_gen = TextGenerator()
        self.game_map_gen = GameMapGenerator(size=128)
        self.dream_gen = DreamGenerator()

        self.running = False
        self.clients = set()

        self._brain_state = None
        self._fractal_path = None
        self._image_prompt = ""
        self._music_params = {}
        self._narrative = ""
        self._game_map = None
        self._dream_params = {}
        self._last_broadcast_time = 0
        self._eeg_quality = 0
        self._total_samples = 0
        self._dropped_broadcasts = 0

        log.info("BCIBrainServer initialized", {"port": ws_port, "source": source_type})

    def start(self):
        """Start the full BCI pipeline."""
        self.running = True

        log.info("Starting BCI pipeline", {"source": self.source_type})
        try:
            if self.source_type == 'muse':
                self.source = MuseSource(**self.source_kwargs)
                log.info("Muse BLE source selected", {"kwargs": self.source_kwargs})
            else:
                self.source = RecordedSource(**self.source_kwargs)
                log.info("Recorded EEG source selected", {"kwargs": self.source_kwargs})
            self.source.start()
            log.info("EEG source started")
        except Exception as e:
            log.error("Failed to start EEG source", {"error": str(e)})
            return

        timeout = 5
        start = time.time()
        while len(self.source.buffer) < self.source.sampling_rate:
            time.sleep(0.1)
            if time.time() - start > timeout:
                log.warn("Timeout waiting for EEG data", {"timeout_s": timeout, "buffer_size": len(self.source.buffer)})
                break

        self.processor = SignalProcessor(
            sampling_rate=self.source.sampling_rate,
            n_channels=self.source.n_channels,
            window_seconds=2,
        )
        log.info("SignalProcessor initialized", {"sr": self.source.sampling_rate, "ch": self.source.n_channels})

        self.music_gen.start()
        log.info("Music generator started")

        self.source.on_data = self._on_eeg_data
        log.info("Data callback registered")

        self._broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self._broadcast_thread.start()
        log.info("Broadcast thread started")

        log.info("BCI Brain Server running", {"port": self.ws_port})

    def stop(self):
        """Stop the BCI pipeline."""
        self.running = False
        if self.source:
            self.source.stop()
        self.music_gen.stop()
        log.info("BCI Brain Server stopped", {"total_samples": self._total_samples, "dropped": self._dropped_broadcasts})

    def _on_eeg_data(self, samples):
        """Callback for new EEG data samples."""
        if self.processor:
            self.processor.feed(samples)
            self._total_samples += len(samples) if hasattr(samples, '__len__') else 1

    def _update_state(self):
        """Update all derived state from current brain state."""
        if self.processor is None:
            return

        brain = self.processor.get_state()
        self._brain_state = brain

        bp = brain.band_powers
        prev_quality = self._eeg_quality
        self._eeg_quality = 1.0 if sum(bp.values()) > 0.01 else 0.0

        if self._eeg_quality != prev_quality:
            log.info("EEG quality changed", {"quality": self._eeg_quality, "bands": {k: round(v, 6) for k, v in bp.items()}})

        self._fractal_path = self.mapper.path
        self.mapper.update(brain)

        self._image_prompt = self.image_gen.generate(brain)
        self.music_gen.update(brain)
        self._narrative = self.text_gen.generate(brain)

        if not hasattr(self, '_last_map_time') or time.time() - self._last_map_time > 5:
            self._game_map = self.game_map_gen.generate(brain)
            self._last_map_time = time.time()
            log.debug("Game map regenerated", {"biome": self._game_map.get('biome', 'unknown') if self._game_map else 'none'})

        self._dream_params = self.dream_gen.update(brain)

    def get_full_state(self) -> dict:
        """Get complete brain state as JSON-serializable dict."""
        brain = self._brain_state or self.processor.get_state() if self.processor else None

        state = {
            'type': 'bci_state',
            'source': self.source_type,
            'eeg_quality': self._eeg_quality,
            'timestamp': time.time(),
            'total_samples': self._total_samples,
        }

        if brain:
            state['cognitive'] = brain.to_dict()

            bp = brain.band_powers
            state['bands'] = {k: round(v, 6) for k, v in bp.items()}

            state['ratios'] = {
                'alpha_theta': round(brain.alpha_theta_ratio, 4),
                'beta_alpha': round(brain.beta_alpha_ratio, 4),
                'delta_theta': round(brain.delta_theta_ratio, 4),
                'gamma_beta': round(brain.gamma_beta_ratio, 4),
                'asymmetry': round(brain.asymmetry, 4),
            }

        if self._fractal_path:
            state['fractal'] = self._fractal_path.to_dict()

        if self._image_prompt:
            state['image_prompt'] = self._image_prompt

        if self._narrative:
            state['narrative'] = self._narrative
            state['cognitive']['narrative'] = self._narrative

        if self.music_gen:
            state['music'] = {'bpm': self.music_gen._bpm} if hasattr(self.music_gen, '_bpm') else {}

        if self._game_map:
            state['game_map'] = {
                k: v for k, v in self._game_map.items()
                if k != 'heightmap'
            }
            if 'heightmap' in self._game_map:
                hm = np.array(self._game_map['heightmap'])
                import math
                step = max(1, len(hm) // 64)
                state['game_map']['heightmap_preview'] = hm[::step, ::step].tolist()

        if self._dream_params:
            state['dream'] = {k: v for k, v in self._dream_params.items()
                              if k != 'fragments'}
            state['dream']['fragments'] = [
                {k: v for k, v in f.items() if k != 'id'}
                for f in self._dream_params.get('fragments', [])
            ]

        return state

    def _broadcast_loop(self):
        """Periodically update and broadcast state."""
        cycle = 0
        while self.running:
            try:
                self._update_state()
                state = self.get_full_state()
                msg = json.dumps(state)

                closed = set()
                for client in self.clients:
                    try:
                        asyncio.run_coroutine_threadsafe(client.send(msg), self._ws_loop).result(timeout=0.5)
                    except Exception:
                        closed.add(client)
                if closed:
                    self.clients -= closed
                    log.debug("Removed stale clients", {"count": len(closed)})

                if cycle % 200 == 0:
                    log.debug("BCI broadcast cycle", {
                        "clients": len(self.clients),
                        "quality": self._eeg_quality,
                        "state": state.get('cognitive', {}).get('state_name', 'unknown') if state.get('cognitive') else 'no_cog'
                    })
                cycle += 1
            except Exception as e:
                log.warn("Broadcast error", {"error": str(e)})
                self._dropped_broadcasts += 1
            time.sleep(0.05)

    async def ws_handler(self, websocket):
        """Handle WebSocket client connection."""
        cid = f"bci-{id(websocket):x}"
        self.clients.add(websocket)
        log.info("BCI client connected", {"client": cid, "total": len(self.clients)})
        start = time.time()
        try:
            await websocket.send(json.dumps(self.get_full_state()))
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type', '')
                    if msg_type == 'get_state':
                        await websocket.send(json.dumps(self.get_full_state()))
                    elif msg_type == 'set_mode':
                        mode = data.get('mode', 'free')
                        log.info("Mapper mode change", {"client": cid, "mode": mode})
                        self.mapper.set_mode(mode)
                    elif msg_type == 'ping':
                        await websocket.send(json.dumps({'type': 'pong'}))
                    else:
                        log.debug("Unknown BCI message", {"client": cid, "type": msg_type})
                except json.JSONDecodeError:
                    log.warn("Invalid BCI message", {"client": cid})
        except websockets.exceptions.ConnectionClosed:
            log.info("BCI client disconnected", {"client": cid, "duration_s": round(time.time() - start, 1)})
        finally:
            self.clients.discard(websocket)
            log.info("BCI client cleaned up", {"client": cid, "remaining": len(self.clients)})


_ws_clients_bci = set()
_server_instance = None


def get_server():
    global _server_instance
    return _server_instance


async def _broadcast_to_ws(server):
    """Async broadcast loop for WebSocket clients."""
    cycle = 0
    while server.running:
        if _ws_clients_bci:
            state = server.get_full_state()
            msg = json.dumps(state)
            closed = set()
            for client in _ws_clients_bci:
                try:
                    await client.send(msg)
                except Exception:
                    closed.add(client)
            _ws_clients_bci -= closed
            if cycle % 200 == 0:
                log.debug("BCI WS broadcast", {"clients": len(_ws_clients_bci)})
            cycle += 1
        await asyncio.sleep(0.05)


async def _ws_handler(websocket):
    """Async WebSocket handler."""
    cid = f"bci-{id(websocket):x}"
    _ws_clients_bci.add(websocket)
    log.info("BCI WS client", {"client": cid, "total": len(_ws_clients_bci)})
    start = time.time()
    try:
        server = get_server()
        if server:
            await websocket.send(json.dumps(server.get_full_state()))
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', '')
                server = get_server()
                if not server:
                    continue
                if msg_type == 'get_state':
                    await websocket.send(json.dumps(server.get_full_state()))
                elif msg_type == 'set_mode':
                    mode = data.get('mode', 'free')
                    log.info("BCI mode change", {"client": cid, "mode": mode})
                    server.mapper.set_mode(mode)
                elif msg_type == 'ping':
                    await websocket.send(json.dumps({'type': 'pong'}))
            except json.JSONDecodeError:
                pass
    except websockets.exceptions.ConnectionClosed:
        log.info("BCI WS disconnected", {"client": cid, "duration_s": round(time.time() - start, 1)})
    finally:
        _ws_clients_bci.discard(websocket)
        log.info("BCI WS cleaned up", {"client": cid, "remaining": len(_ws_clients_bci)})


def run_server(ws_port=8766, source_type='recorded', source_kwargs=None):
    """Run the BCI brain server (blocking)."""
    global _server_instance

    server = BCIBrainServer(
        ws_port=ws_port,
        source_type=source_type,
        source_kwargs=source_kwargs or {},
    )
    _server_instance = server
    server.start()

    async def main_loop():
        async with websockets.serve(_ws_handler, 'localhost', ws_port):
            log.info("BCI WebSocket server listening", {"url": f"ws://localhost:{ws_port}"})
            await _broadcast_to_ws(server)

    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()


def run_standalone():
    """Entry point: run BCI server with recorded data."""
    import argparse
    parser = argparse.ArgumentParser(description='FCSTN BCI Brain Server')
    parser.add_argument('--port', type=int, default=8766,
                        help='WebSocket port (default: 8766)')
    parser.add_argument('--source', type=str, default='recorded',
                        choices=['recorded', 'muse', 'openbci'],
                        help='EEG source (default: recorded)')
    parser.add_argument('--file', type=str, default='bci/data/sample_eeg.bin',
                        help='Recorded EEG file path')
    parser.add_argument('--speed', type=float, default=1.0,
                        help='Playback speed (recorded source)')
    args = parser.parse_args()

    kwargs = {}
    if args.source == 'recorded':
        kwargs = {'filepath': args.file, 'speed': args.speed, 'loop': True}
    elif args.source == 'muse':
        kwargs = {'timeout': 15}

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(message)s',
    )

    run_server(ws_port=args.port, source_type=args.source, source_kwargs=kwargs)


if __name__ == '__main__':
    run_standalone()
