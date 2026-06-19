"""
FCSTN 3D Fractal World Visualizer
Connects to the FCSTN server and renders a living 3D fractal world
that responds to cognitive metrics in real-time.

Controls:
  - Keys 1-5: Set cognitive state directly
  - Keys 0: Reset to neutral
  - Keys A/D: Change attention
  - Keys S/W: Change engagement
  - Keys Q/E: Change workload
"""

import asyncio
import json
import sys
import time
import threading
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D

try:
    import websockets.sync.client as ws_sync
    HAS_WS = True
except ImportError:
    HAS_WS = False
    print("[!] websockets not available. Run: pip install websockets")


# Global state received from server
current_state = {
    "attention": 0.5,
    "engagement": 0.5,
    "workload": 0.3,
    "fractal_dim": 2.5,
    "state_name": "neutral",
    "color": "#9933FF",
    "complexity": 0.5,
    "instability": 0.3,
}

state_lock = threading.Lock()

# Server config
SERVER_URL = "ws://localhost:8765"


def ws_listener():
    """Background thread that listens for WebSocket updates."""
    if not HAS_WS:
        return
    while True:
        try:
            with ws_sync.connect(SERVER_URL) as ws:
                while True:
                    msg = ws.recv()
                    data = json.loads(msg)
                    if data.get("type") == "state":
                        with state_lock:
                            current_state.update(data["data"])
        except (ConnectionRefusedError, OSError, Exception) as e:
            print(f"[WS] Disconnected: {e}. Reconnecting in 2s...")
            time.sleep(2)


def send_control(attention=None, engagement=None, workload=None):
    """Send control message to server."""
    if not HAS_WS:
        return
    try:
        with ws_sync.connect(SERVER_URL) as ws:
            payload = {"type": "control"}
            if attention is not None:
                payload["attention"] = attention
            if engagement is not None:
                payload["engagement"] = engagement
            if workload is not None:
                payload["workload"] = workload
            ws.send(json.dumps(payload))
    except Exception:
        pass


# Keyboard state
keys_pressed = {}
key_timers = {}


def on_key(event):
    """Handle keyboard input for live control."""
    global keys_pressed, key_timers
    k = event.key.lower() if event.key else ""

    if k in ('1', '2', '3', '4', '5', '0'):
        presets = {
            '1': (0.2, 0.2, 0.2),   # fatigued
            '2': (0.4, 0.3, 0.3),   # relaxed
            '3': (0.5, 0.5, 0.3),   # neutral
            '4': (0.7, 0.6, 0.4),   # engaged
            '5': (0.9, 0.8, 0.5),   # focused
            '0': (0.5, 0.5, 0.3),   # reset
        }
        a, e, w = presets.get(k, (0.5, 0.5, 0.3))
        send_control(attention=a, engagement=e, workload=w)

    att_map = {'a': -0.1, 'd': 0.1}
    eng_map = {'s': -0.1, 'w': 0.1}
    wrk_map = {'q': -0.1, 'e': 0.1}

    with state_lock:
        if k in att_map:
            a = max(0.05, min(0.95, current_state['attention'] + att_map[k]))
            send_control(attention=a)
        if k in eng_map:
            e = max(0.05, min(0.95, current_state['engagement'] + eng_map[k]))
            send_control(engagement=e)
        if k in wrk_map:
            w = max(0.05, min(0.95, current_state['workload'] + wrk_map[k]))
            send_control(workload=w)


def generate_fractal_surface(dim, complexity, instability, grid_size=80):
    """Generate a 3D fractal-like surface based on cognitive parameters."""
    x = np.linspace(-2, 2, grid_size)
    y = np.linspace(-2, 2, grid_size)
    X, Y = np.meshgrid(x, y)

    # Fractal dimension controls frequency
    freq = 1.5 + dim * 0.8
    # Complexity controls number of octaves
    octaves = max(1, int(3 + complexity * 5))
    # Instability controls noise amplitude
    noise_amp = 0.1 + instability * 0.5

    Z = np.zeros_like(X)
    amplitude = 1.0
    for o in range(octaves):
        f = freq * (2 ** o)
        a = amplitude * (0.5 ** o)
        phase = time.time() * 0.3 * (1 + instability * 0.5)

        Z += a * (
            np.sin(f * X + phase + o * 0.5) *
            np.cos(f * Y * 0.8 + phase * 0.7 + o * 0.3)
        )
        # Add fractal noise
        if o > 1:
            noise = np.random.randn(*X.shape) * noise_amp * a
            Z += noise * 0.3
        amplitude *= 0.7

    # Normalize
    Z = Z / Z.max() if Z.max() != 0 else Z

    # Apply fractal dimension warping
    warp = dim - 2.0
    Z = Z * (1 + warp * 0.5)
    # Add curvature based on complexity
    r2 = X**2 + Y**2
    Z -= r2 * 0.1 * complexity

    return X, Y, Z


def get_surface_color(state_name, base_color="#9933FF"):
    """Map state to colormap."""
    state_map = {
        "focused": cm.inferno,
        "stressed": cm.hot,
        "fatigued": cm.winter,
        "engaged": cm.cool,
        "curious": cm.spring,
        "neutral": cm.twilight,
    }
    return state_map.get(state_name, cm.twilight)


# State display names
STATE_LABELS = {
    "focused": "🔥 FOCUSED",
    "stressed": "⚡ STRESSED",
    "fatigued": "💤 FATIGUED",
    "engaged": "🎯 ENGAGED",
    "curious": "✨ CURIOUS",
    "neutral": "◆ NEUTRAL",
}


def main():
    print("\n" + "=" * 55)
    print("  FCSTN - 3D Fractal World Visualizer")
    print("  Live cognitive space-time visualization")
    print("=" * 55)
    print("\n  Controls:")
    print("    1-5: Cognitive state presets")
    print("    0:   Reset to neutral")
    print("    A/D: Attention -/+")
    print("    W/S: Engagement -/+")
    print("    Q/E: Workload -/+")
    print("\n  Connecting to server...")

    # Start WebSocket listener thread
    listener = threading.Thread(target=ws_listener, daemon=True)
    listener.start()
    time.sleep(0.5)

    # Setup the 3D figure
    plt.ion()
    fig = plt.figure(figsize=(14, 10))
    fig.patch.set_facecolor('#0f111a')
    fig.canvas.manager.set_window_title('FCSTN - Fractal Cognitive Space-Time World')

    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#0f111a')
    ax.grid(False)
    ax.set_axis_off()

    # Connect keyboard
    fig.canvas.mpl_connect('key_press_event', on_key)

    # Text elements for HUD
    title = ax.text2D(0.5, 0.95, "FRACTAL COGNITIVE SPACE-TIME", transform=ax.transAxes,
                      fontsize=14, fontweight='bold', color='white', ha='center',
                      fontfamily='sans-serif')

    state_text = ax.text2D(0.05, 0.90, "", transform=ax.transAxes,
                           fontsize=18, fontweight='bold', color='#00f0ff',
                           fontfamily='monospace')

    metrics_text = ax.text2D(0.05, 0.78, "", transform=ax.transAxes,
                             fontsize=11, color='#8b9bb4', fontfamily='monospace',
                             verticalalignment='top')

    help_text = ax.text2D(0.05, 0.04, "Keys: 1-5 Presets | A/D Attn | W/S Eng | Q/E Work | 0 Reset",
                          transform=ax.transAxes, fontsize=9, color='#555566',
                          fontfamily='monospace')

    # Initial surface
    X, Y, Z = generate_fractal_surface(2.5, 0.5, 0.3)
    surf = ax.plot_surface(X, Y, Z, cmap=cm.twilight, rstride=1, cstride=1,
                           antialiased=True, alpha=0.95, linewidth=0)
    ax.view_init(elev=35, azim=45)

    # Animation loop
    def animate(frame):
        nonlocal surf, X, Y

        with state_lock:
            dim = current_state.get("fractal_dim", 2.5)
            complexity = current_state.get("complexity", 0.5)
            instability = current_state.get("instability", 0.3)
            state_name = current_state.get("state_name", "neutral")
            color_hex = current_state.get("color", "#9933FF")
            attention = current_state.get("attention", 0.5)
            engagement = current_state.get("engagement", 0.5)
            workload = current_state.get("workload", 0.3)

        # Generate new surface
        X, Y, Z = generate_fractal_surface(dim, complexity, instability)

        # Remove old surface and draw new
        surf.remove()
        cmap = get_surface_color(state_name)
        rstride = max(1, int(2 - complexity * 1.5))
        cstride = rstride
        surf = ax.plot_surface(X, Y, Z, cmap=cmap, rstride=rstride, cstride=cstride,
                               antialiased=complexity > 0.3, alpha=0.92, linewidth=0)

        # Update view angle slowly rotating
        current_azim = ax.azim or 45
        ax.view_init(elev=30 + 5 * np.sin(time.time() * 0.1), azim=current_azim + 0.3)

        # Auto-rotate faster when engaged
        speed = 0.3 + engagement * 0.7
        ax.view_init(elev=30 + 10 * np.sin(time.time() * 0.1 * speed),
                     azim=ax.azim + 0.2 * speed)

        # Update HUD
        state_label = STATE_LABELS.get(state_name, state_name.upper())
        state_text.set_text(f"◆ {state_label}")
        state_text.set_color(color_hex)

        metrics_text.set_text(
            f"  DIMENSION:  {dim:.3f}\n"
            f"  ATTENTION:  {attention:.2f}\n"
            f"  ENGAGEMENT: {engagement:.2f}\n"
            f"  WORKLOAD:   {workload:.2f}\n"
            f"  COMPLEXITY: {complexity:.2f}\n"
            f"  INSTABILITY:{instability:.2f}"
        )

        return surf, state_text, metrics_text

    anim = FuncAnimation(fig, animate, interval=50, blit=False, cache_frame_data=False)

    print("\n  ✓ Connected! 3D world is alive.")
    print("  Press keys to interact. Close window to exit.\n")

    plt.show(block=True)


if __name__ == "__main__":
    main()
