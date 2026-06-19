"""
FCSTN Cognitive Controller - Interactive control panel
Lets you (or the audience) control the cognitive metrics in real-time
and see the 3D world respond immediately.

When used alongside the 3D visualizer, open this in a second window.
"""

import tkinter as tk
from tkinter import ttk
import json
import threading
import time

try:
    import websockets.sync.client as ws_sync
    HAS_WS = True
except ImportError:
    HAS_WS = False

SERVER_URL = "ws://localhost:8765"


def send_control(attention=None, engagement=None, workload=None):
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


def send_preset(preset):
    presets = {
        "fatigued": (0.15, 0.15, 0.2),
        "relaxed": (0.35, 0.25, 0.2),
        "neutral": (0.5, 0.5, 0.3),
        "curious": (0.65, 0.55, 0.3),
        "engaged": (0.75, 0.65, 0.35),
        "focused": (0.9, 0.85, 0.4),
        "hyperspace": (0.95, 0.9, 0.8),
    }
    if preset in presets:
        a, e, w = presets[preset]
        send_control(attention=a, engagement=e, workload=w)


class FCSTNController:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FCSTN Cognitive Controller")
        self.root.geometry("480x620")
        self.root.configure(bg='#0f111a')
        self.root.resizable(False, False)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#0f111a', foreground='white', font=('Outfit', 10))
        style.configure('TButton', font=('Outfit', 9, 'bold'), padding=6)
        style.map('TButton', background=[('active', '#00f0ff')])

        self.attention = tk.DoubleVar(value=0.5)
        self.engagement = tk.DoubleVar(value=0.5)
        self.workload = tk.DoubleVar(value=0.3)

        self.build_ui()
        self.update_loop()

    def build_ui(self):
        root = self.root

        # Title
        title = tk.Label(root, text="🧠 FCSTN CONTROL CENTER",
                         font=('Outfit', 16, 'bold'),
                         fg='#ffffff', bg='#0f111a')
        title.pack(pady=(20, 5))

        subtitle = tk.Label(root, text="Cognitive Space-Time Modulation",
                            font=('Outfit', 9), fg='#8b9bb4', bg='#0f111a')
        subtitle.pack(pady=(0, 20))

        # Main frame
        main = tk.Frame(root, bg='#0f111a')
        main.pack(fill='both', expand=True, padx=30)

        # Sliders
        self.add_slider(main, "ATTENTION", self.attention, "#00f0ff", 0)
        self.add_slider(main, "ENGAGEMENT", self.engagement, "#ff0055", 1)
        self.add_slider(main, "WORKLOAD", self.workload, "#ffb800", 2)

        # Separator
        sep = tk.Frame(main, height=1, bg='#2a2a3a')
        sep.pack(fill='x', pady=(15, 10))

        # Presets label
        plbl = tk.Label(main, text="COGNITIVE PRESETS",
                        font=('Outfit', 10, 'bold'), fg='#8b9bb4', bg='#0f111a')
        plbl.pack(pady=(0, 10))

        # Preset buttons in a grid
        presets_frame = tk.Frame(main, bg='#0f111a')
        presets_frame.pack(fill='x')

        presets = [
            ("💤 Fatigued", "fatigued", "#4488FF"),
            ("🧘 Relaxed", "relaxed", "#66BBAA"),
            ("◆ Neutral", "neutral", "#9933FF"),
            ("✨ Curious", "curious", "#00FF88"),
            ("🎯 Engaged", "engaged", "#00F0FF"),
            ("🔥 Focused", "focused", "#FF0055"),
            ("🌀 Hyper", "hyperspace", "#FF4400"),
        ]

        for i, (label, preset, color) in enumerate(presets):
            row = i // 4
            col = i % 4
            btn = tk.Button(presets_frame, text=label,
                            font=('Outfit', 8, 'bold'),
                            fg='white', bg=color, activebackground=color,
                            relief='flat', padx=8, pady=6, bd=0,
                            command=lambda p=preset: send_preset(p))
            btn.grid(row=row, column=col, padx=3, pady=3, sticky='ew')
            presets_frame.grid_columnconfigure(col, weight=1)

        # Status
        self.status_label = tk.Label(root, text="◆ Waiting for connection...",
                                     font=('Consolas', 9), fg='#8b9bb4', bg='#0f111a')
        self.status_label.pack(pady=(15, 5))

        # Connection indicator
        self.conn_indicator = tk.Canvas(root, width=12, height=12,
                                         bg='#0f111a', highlightthickness=0)
        self.conn_indicator.pack(pady=(0, 15))
        self.conn_dot = self.conn_indicator.create_oval(1, 1, 11, 11,
                                                         fill='#ff4400', outline='')

    def add_slider(self, parent, label, variable, color, row):
        frame = tk.Frame(parent, bg='#0f111a')
        frame.pack(fill='x', pady=5)

        header = tk.Frame(frame, bg='#0f111a')
        header.pack(fill='x')

        lbl = tk.Label(header, text=label, font=('Outfit', 9, 'bold'),
                       fg=color, bg='#0f111a', anchor='w')
        lbl.pack(side='left')

        val = tk.Label(header, text="0.50", font=('Consolas', 9),
                       fg='white', bg='#0f111a', anchor='e')
        val.pack(side='right')

        slider = tk.Scale(frame, from_=0.0, to=1.0, resolution=0.01,
                          orient='horizontal', variable=variable,
                          bg='#1a1a2a', fg=color, troughcolor='#2a2a3a',
                          highlightbackground='#0f111a', bd=0,
                          length=380, sliderrelief='flat')
        slider.pack(fill='x')

        # Update value label
        def update_val(*_):
            val.config(text=f"{variable.get():.2f}")
            self.on_slider_change()
        variable.trace_add('write', update_val)

    def on_slider_change(self):
        a = self.attention.get()
        e = self.engagement.get()
        w = self.workload.get()
        send_control(attention=a, engagement=e, workload=w)

    def update_loop(self):
        # Simple connection check
        try:
            if HAS_WS:
                with ws_sync.connect(SERVER_URL, timeout=0.5) as ws:
                    self.conn_indicator.itemconfig(self.conn_dot, fill='#00ff88')
                    self.status_label.config(text="◆ Connected to FCSTN Server", fg='#00ff88')
        except Exception:
            self.conn_indicator.itemconfig(self.conn_dot, fill='#ff4400')
            self.status_label.config(text="◆ Server not running (start fcstn_server.py)", fg='#ff4400')

        self.root.after(2000, self.update_loop)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = FCSTNController()
    app.run()
