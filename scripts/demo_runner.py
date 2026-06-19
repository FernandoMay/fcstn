"""
FCSTN Demo Runner - Generates all presentation-ready outputs
Run: python scripts/demo_runner.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import logging
logging.basicConfig(level=logging.WARNING)

from core.fractal_engine.mandelbrot import MandelbrotGenerator, FractalParameters, create_color_mapping
from core.geometry_engine.metric_tensor import MetricTensorComputer, MetricConfig
from core.ndan_interface.bci_processor import NDANInterface, generate_synthetic_eeg
from core.coalition_network.coalition_formation import Agent, AgentType, CoalitionFormationGame

OUTPUTS = Path(__file__).parent.parent / 'outputs'
OUTPUTS.mkdir(exist_ok=True)

FIG_W = 16
DPI = 150


def generate_fractal_demo():
    fig, axes = plt.subplots(2, 3, figsize=(FIG_W, 10))

    configs = [
        ("Zoom 1x (Overview)", 1.0, 128),
        ("Zoom 10x (Detail)", 10.0, 256),
        ("Zoom 50x (Deep)", 50.0, 512),
        ("Center: (-0.75, 0.1)", 1.0, 128, (-0.75, 0.1)),
        ("Center: (0.285, 0.01)", 1.0, 128, (0.285, 0.01)),
        ("Center: (-1.25, 0.0)", 5.0, 256, (-1.25, 0.0)),
    ]

    for ax, cfg in zip(axes.flat, configs):
        title = cfg[0]
        zoom = cfg[1]
        iters = cfg[2]
        center = cfg[3] if len(cfg) > 3 else (-0.5, 0.0)

        params = FractalParameters(resolution=(400, 400), max_iterations=iters, center=center, zoom=zoom)
        gen = MandelbrotGenerator(params, use_gpu=False)
        fractal = gen.generate_smooth()
        rgb = create_color_mapping(fractal, 'twilight')

        ax.imshow(rgb)
        ax.set_title(title, fontsize=10, color='white')
        ax.axis('off')

    plt.tight_layout()
    path = OUTPUTS / 'fractal_demo.png'
    plt.savefig(path, dpi=DPI, bbox_inches='tight', facecolor='#0f111a')
    plt.close()
    print(f"  [OK] {path.name}")


def generate_metric_visualization():
    fig, axes = plt.subplots(1, 3, figsize=(FIG_W, 5))

    config = MetricConfig(grid_resolution=(32, 32, 32))
    computer = MetricTensorComputer(config)

    # Minkowski
    minkowski = computer.minkowski_metric()
    g_xx_m = minkowski.g[:, :, 16, 1, 1]
    im1 = axes[0].imshow(g_xx_m, cmap='viridis', aspect='auto')
    axes[0].set_title('Minkowski (Flat Space)', fontsize=11, color='white')
    plt.colorbar(im1, ax=axes[0], shrink=0.8)

    # Schwarzschild
    schwarz = computer.schwarzschild_metric(mass=1.0)
    g_xx_s = schwarz.g[:, :, 16, 1, 1]
    im2 = axes[1].imshow(g_xx_s, cmap='inferno', aspect='auto')
    axes[1].set_title('Schwarzschild (Black Hole)', fontsize=11, color='white')
    plt.colorbar(im2, ax=axes[1], shrink=0.8)

    # Adaptive from fractal
    fparams = FractalParameters(resolution=(32, 32), max_iterations=100)
    fgen = MandelbrotGenerator(fparams, use_gpu=False)
    fractal = fgen.generate()
    adaptive = computer.compute_from_fractal(fractal)
    g_xx_a = adaptive.g[:, :, 16, 1, 1]
    im3 = axes[2].imshow(g_xx_a, cmap='plasma', aspect='auto')
    axes[2].set_title('Adaptive (Fractal-Mapped)', fontsize=11, color='white')
    plt.colorbar(im3, ax=axes[2], shrink=0.8)

    for ax in axes:
        ax.axis('off')

    plt.tight_layout()
    path = OUTPUTS / 'metric_visualization.png'
    plt.savefig(path, dpi=DPI, bbox_inches='tight', facecolor='#0f111a')
    plt.close()
    print(f"  [OK] {path.name}")


def generate_cognitive_dashboard():
    ndan = NDANInterface()
    metrics_over_time = {'attention': [], 'engagement': [], 'workload': [], 'state': []}

    for t in range(50):
        signal = generate_synthetic_eeg(duration=0.5)
        features = ndan.process_signal(signal)
        metrics_over_time['attention'].append(features.attention_index)
        metrics_over_time['engagement'].append(features.engagement_level)
        metrics_over_time['workload'].append(features.workload)
        metrics_over_time['state'].append(features.cognitive_state.value)

    fig, axes = plt.subplots(3, 1, figsize=(FIG_W, 8))

    time_axis = np.arange(len(metrics_over_time['attention'])) * 0.5

    axes[0].plot(time_axis, metrics_over_time['attention'], color='#00f0ff', linewidth=2)
    axes[0].fill_between(time_axis, metrics_over_time['attention'], alpha=0.3, color='#00f0ff')
    axes[0].set_ylabel('Attention', fontsize=11, color='white')
    axes[0].set_ylim(0, 1)
    axes[0].grid(True, alpha=0.2)
    axes[0].tick_params(colors='white')

    axes[1].plot(time_axis, metrics_over_time['engagement'], color='#ff0055', linewidth=2)
    axes[1].fill_between(time_axis, metrics_over_time['engagement'], alpha=0.3, color='#ff0055')
    axes[1].set_ylabel('Engagement', fontsize=11, color='white')
    axes[1].set_ylim(0, 1)
    axes[1].grid(True, alpha=0.2)
    axes[1].tick_params(colors='white')

    axes[2].plot(time_axis, metrics_over_time['workload'], color='#ffb800', linewidth=2)
    axes[2].fill_between(time_axis, metrics_over_time['workload'], alpha=0.3, color='#ffb800')
    axes[2].set_ylabel('Workload', fontsize=11, color='white')
    axes[2].set_xlabel('Time (seconds)', fontsize=11, color='white')
    axes[2].set_ylim(0, 1)
    axes[2].grid(True, alpha=0.2)
    axes[2].tick_params(colors='white')

    fig.suptitle('Cognitive Metrics Over Time (Synthetic BCI)', fontsize=14, color='white', y=1.02)
    plt.tight_layout()
    path = OUTPUTS / 'cognitive_dashboard.png'
    plt.savefig(path, dpi=DPI, bbox_inches='tight', facecolor='#0f111a')
    plt.close()
    print(f"  [OK] {path.name}")


def generate_coalition_visualization():
    agents = [
        Agent("H1", AgentType.HUMAN, ["perception"], {"compute": 10, "bandwidth": 5}),
        Agent("H2", AgentType.HUMAN, ["perception"], {"compute": 10, "bandwidth": 5}),
        Agent("A1", AgentType.AI_AGENT, ["inference"], {"compute": 50, "bandwidth": 20}),
        Agent("A2", AgentType.AI_AGENT, ["inference"], {"compute": 50, "bandwidth": 20}),
        Agent("XR1", AgentType.XR_DEVICE, ["rendering"], {"compute": 30, "bandwidth": 40}),
        Agent("XR2", AgentType.XR_DEVICE, ["rendering"], {"compute": 30, "bandwidth": 40}),
        Agent("E1", AgentType.EDGE_NODE, ["processing"], {"compute": 100, "bandwidth": 100}),
        Agent("C1", AgentType.CLOUD_NODE, ["compute"], {"compute": 500, "bandwidth": 200}),
    ]

    game = CoalitionFormationGame(agents)
    final_coalitions = game.run_merge_and_split(max_iterations=20)
    stats = game.get_coalition_statistics()

    fig, ax = plt.subplots(figsize=(FIG_W, 6))
    ax.axis('off')

    info_text = (
        f"Coalition Formation Results\n"
        f"{'='*35}\n"
        f"  Total coalitions: {stats['num_coalitions']}\n"
        f"  Total network value: {stats['total_value']:.2f}\n"
        f"  Avg coalition size: {stats['avg_coalition_size']:.2f}\n"
        f"  Coalition types: {stats['coalition_types']}\n"
        f"{'='*35}\n"
    )

    for c_id, coalition in final_coalitions.items():
        info_text += (
            f"\n  [{coalition.coalition_type.value.upper()}]\n"
            f"    ID: {c_id}\n"
            f"    Members: {', '.join(sorted(coalition.members))}\n"
            f"    Value: {coalition.value:.2f}\n"
        )

    ax.text(0.05, 0.95, info_text, transform=ax.transAxes, fontsize=10,
            fontfamily='monospace', verticalalignment='top', color='#00f0ff',
            bbox=dict(boxstyle='round', facecolor='#0f111a', edgecolor='#00f0ff', alpha=0.8))

    path = OUTPUTS / 'coalition_results.png'
    plt.savefig(path, dpi=DPI, bbox_inches='tight', facecolor='#0f111a')
    plt.close()
    print(f"  [OK] {path.name}")


def generate_architecture_diagram():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_facecolor('#0f111a')

    layers = [
        (7.0, 9.5, "L1: Cognitive Layer", "Human Users + XR Devices + AI Agents", '#00f0ff'),
        (5.0, 7.0, "L2: NDAN Interface", "BCI Processing · Feature Extraction · Feedback", '#ff0055'),
        (3.0, 5.0, "L3: Geometry Engine", "Fractal Generation · Metric Tensor · Geodesics", '#ffb800'),
        (1.0, 3.0, "L4: Infrastructure", "Coalition Formation · D2D · Resource Mgmt", '#00ffaa'),
    ]

    for y_bot, y_top, title, desc, color in layers:
        rect = FancyBboxPatch((1, y_bot), 10, y_top - y_bot,
                              boxstyle="round,pad=0.1",
                              facecolor=color + '20',
                              edgecolor=color,
                              linewidth=2)
        ax.add_patch(rect)
        ax.text(6, (y_bot + y_top) / 2 + 0.2, title,
                ha='center', va='center', fontsize=14, fontweight='bold', color=color)
        ax.text(6, (y_bot + y_top) / 2 - 0.3, desc,
                ha='center', va='center', fontsize=9, color='#8b9bb4')

        if y_bot > 1.0:
            mid = (y_bot + y_top) / 2
            next_top = (y_bot + y_top) / 2 - 0.2
            next_bot = y_bot
            ax.annotate('', xy=(6, next_bot + 0.05), xytext=(6, next_top),
                        arrowprops=dict(arrowstyle='->', color='#8b9bb4', lw=2))

    ax.set_title('FCSTN: 4-Layer Architecture', fontsize=18, fontweight='bold',
                 color='white', pad=20)

    path = OUTPUTS / 'architecture_diagram.png'
    plt.savefig(path, dpi=DPI, bbox_inches='tight', facecolor='#0f111a')
    plt.close()
    print(f"  [OK] {path.name}")


if __name__ == '__main__':
    print("\nFCSTN Demo Output Generator")
    print("=" * 40)
    print("\n[1] Generating fractal demos...")
    generate_fractal_demo()
    print("\n[2] Generating metric visualizations...")
    generate_metric_visualization()
    print("\n[3] Generating cognitive dashboard...")
    generate_cognitive_dashboard()
    print("\n[4] Generating coalition visualization...")
    generate_coalition_visualization()
    print("\n[5] Generating architecture diagram...")
    generate_architecture_diagram()
    print(f"\n{'=' * 40}")
    print(f"All outputs saved to: {OUTPUTS}")
    print(f"{'=' * 40}\n")
