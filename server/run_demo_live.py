"""
FCSTN Live Demo Orchestrator - ESCOM Summer School 2026

Starts the full demo ecosystem:
  1. FCSTN WebSocket Server (cognitive engine)
  2. 3D Fractal World Visualizer
  3. Cognitive Controller panel

All connected via WebSockets in real-time.

Usage:
  python server/run_demo_live.py          # Full demo
  python server/run_demo_live.py --server  # Server only
  python server/run_demo_live.py --viz     # Visualizer only (needs server)
  python server/run_demo_live.py --ctrl    # Controller only (needs server)
"""

import sys
import os
import subprocess
import time
import signal
import threading
from pathlib import Path

ROOT = Path(__file__).parent.parent
SERVER_SCRIPT = str(ROOT / 'server' / 'fcstn_server.py')
VIZ_SCRIPT = str(ROOT / 'server' / 'visualizer_3d.py')
CTRL_SCRIPT = str(ROOT / 'server' / 'controller.py')


def print_banner():
    print("""
    ╔══════════════════════════════════════════════════╗
    ║     FCSTN - LIVE DEMO ECOSYSTEM                  ║
    ║     Fractal Cognitive Space-Time Networks        ║
    ║     ESCOM Summer School · July 3, 2026          ║
    ╚══════════════════════════════════════════════════╝
    """)


def run_script(path, name):
    proc = subprocess.Popen(
        [sys.executable, path],
        stdout=None, stderr=None,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    )
    print(f"  [{name}] PID {proc.pid}")
    return proc


def main():
    args = set(sys.argv[1:])

    print_banner()
    print("  Initializing FCSTN Live Demo...\n")

    processes = []

    if '--server' in args or not (args & {'--viz', '--ctrl'}):
        print("  [1/3] Starting FCSTN Server (ws://localhost:8765)...")
        p = run_script(SERVER_SCRIPT, "Server")
        processes.append(p)
        time.sleep(1.5)

    if '--viz' in args or not (args & {'--server', '--ctrl'}):
        print("  [2/3] Starting 3D Fractal Visualizer...")
        p = run_script(VIZ_SCRIPT, "Visualizer")
        processes.append(p)
        time.sleep(0.5)

    if '--ctrl' in args or not (args & {'--server', '--viz'}):
        print("  [3/3] Starting Cognitive Controller...")
        p = run_script(CTRL_SCRIPT, "Controller")
        processes.append(p)
        time.sleep(0.5)

    print("\n  ⚡ All systems online! Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  Shutting down...")
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        print("  Done. Thanks for running FCSTN Live!\n")


if __name__ == "__main__":
    main()
