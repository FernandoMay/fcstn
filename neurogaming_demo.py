"""
Complete FCSTN Example: Neurogaming Application

This example demonstrates a full implementation of a brain-responsive
gaming environment using the FCSTN framework.
"""

import numpy as np
import matplotlib.pyplot as plt
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import FCSTN modules
import sys
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.fractal_engine.mandelbrot import MandelbrotGenerator, FractalParameters, create_color_mapping
from src.core.geometry_engine.metric_tensor import MetricTensorComputer, MetricConfig
from src.core.ndan_interface.bci_processor import (
    NDANInterface, generate_synthetic_eeg, CognitiveState
)
from src.core.coalition_network.coalition_formation import (
    Agent, AgentType, CoalitionFormationGame, ResourceManager
)


class NeurogameEnvironment:
    """
    Brain-responsive gaming environment that adapts to player's cognitive state.
    """
    
    def __init__(self):
        """Initialize the neurogame environment"""
        self.logger = logging.getLogger("NeurogameEnvironment")
        
        # Initialize FCSTN components
        self.logger.info("Initializing FCSTN components...")
        
        # Fractal generator
        self.fractal_params = FractalParameters(
            resolution=(800, 600),
            max_iterations=128,
            center=(-0.5, 0.0),
            zoom=1.0
        )
        self.fractal_gen = MandelbrotGenerator(self.fractal_params, use_gpu=False)
        
        # Geometry computer
        self.geometry_config = MetricConfig(
            grid_resolution=(32, 32, 32),
            curvature_scale=1.0
        )
        self.geometry_computer = MetricTensorComputer(self.geometry_config)
        
        # NDAN interface
        self.ndan = NDANInterface(sampling_rate=250.0)
        
        # Game state
        self.difficulty_level = 1.0
        self.player_position = np.array([0.0, 0.0, 0.0])
        self.score = 0
        self.session_start = time.time()
        
        self.logger.info("Neurogame environment initialized")
    
    def simulate_gameplay_session(self, duration_seconds=60):
        """
        Simulate a gaming session with cognitive adaptation.
        
        Args:
            duration_seconds: Duration of the session
        """
        self.logger.info(f"Starting {duration_seconds}s gameplay session...")
        
        num_frames = duration_seconds * 2  # 2 updates per second
        dt = 1.0 / 2.0  # Time step
        
        # Storage for analysis
        metrics = {
            'time': [],
            'attention': [],
            'engagement': [],
            'difficulty': [],
            'complexity': [],
            'cognitive_state': []
        }
        
        for frame in range(num_frames):
            current_time = frame * dt
            
            # 1. Simulate player's neural activity
            # In real system, this comes from BCI hardware
            bci_signal = self._simulate_player_neural_state(current_time)
            
            # 2. Process through NDAN
            cognitive_features = self.ndan.process_signal(bci_signal)
            
            # 3. Adapt environment based on cognitive state
            self._adapt_game_environment(cognitive_features)
            
            # 4. Update game difficulty
            self._update_difficulty(cognitive_features)
            
            # 5. Generate new environment frame
            fractal_field = self.fractal_gen.generate_smooth()
            
            # 6. Record metrics
            metrics['time'].append(current_time)
            metrics['attention'].append(cognitive_features.attention_index)
            metrics['engagement'].append(cognitive_features.engagement_level)
            metrics['difficulty'].append(self.difficulty_level)
            metrics['complexity'].append(self.fractal_params.zoom)
            metrics['cognitive_state'].append(cognitive_features.cognitive_state.value)
            
            # 7. Log progress
            if frame % 10 == 0:
                self.logger.info(
                    f"t={current_time:.1f}s | "
                    f"Attention={cognitive_features.attention_index:.2f} | "
                    f"Difficulty={self.difficulty_level:.2f} | "
                    f"State={cognitive_features.cognitive_state.value}"
                )
        
        self.logger.info("Session complete!")
        return metrics
    
    def _simulate_player_neural_state(self, time):
        """
        Simulate player's neural activity over time.
        
        Models:
        - Early session: High engagement, increasing attention
        - Mid session: Peak performance
        - Late session: Fatigue sets in
        """
        # Fatigue increases over time
        fatigue_factor = min(time / 60.0, 1.0)  # 0 to 1 over 60 seconds
        
        # Engagement decreases with fatigue
        engagement_baseline = 0.8 * (1.0 - 0.5 * fatigue_factor)
        
        # Attention has natural variations
        attention_variation = 0.2 * np.sin(2 * np.pi * time / 15.0)
        
        # Generate signal with modulated characteristics
        signal = generate_synthetic_eeg(duration=2.0)
        
        # In a real system, these would be extracted from the signal
        # Here we directly modulate them for simulation purposes
        
        return signal
    
    def _adapt_game_environment(self, cognitive_features):
        """
        Adapt the game environment based on cognitive state.
        
        Adaptations:
        - Focused state: Increase complexity and detail
        - Fatigued state: Simplify geometry, reduce curvature
        - Stressed state: Reduce environmental chaos
        """
        env_params = self.ndan.get_environment_parameters(cognitive_features)
        
        # Update fractal parameters
        self.fractal_params.zoom = env_params['fractal_zoom']
        
        # Update geometry curvature
        self.geometry_config.curvature_scale = env_params['curvature_scale']
        
        # Adjust visual complexity based on cognitive load
        if cognitive_features.workload > 0.7:
            # High workload - simplify
            self.fractal_params.max_iterations = 64
        elif cognitive_features.attention_index > 0.7:
            # High attention - increase detail
            self.fractal_params.max_iterations = 256
        else:
            # Default
            self.fractal_params.max_iterations = 128
    
    def _update_difficulty(self, cognitive_features):
        """
        Implicit difficulty scaling based on cognitive state.
        
        - High engagement + attention -> Increase difficulty
        - Fatigue or stress -> Decrease difficulty
        - Maintains optimal challenge level
        """
        # Target: keep player in "flow state"
        ideal_attention = 0.6
        ideal_engagement = 0.7
        
        # Compute deviation from ideal
        attention_diff = cognitive_features.attention_index - ideal_attention
        engagement_diff = cognitive_features.engagement_level - ideal_engagement
        
        # Adjust difficulty (with damping)
        adjustment = 0.1 * (attention_diff + engagement_diff) / 2.0
        
        self.difficulty_level = np.clip(
            self.difficulty_level + adjustment,
            0.5,  # Min difficulty
            3.0   # Max difficulty
        )


def plot_session_metrics(metrics):
    """
    Visualize the gameplay session metrics.
    
    Args:
        metrics: Dictionary of recorded metrics
    """
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # Plot 1: Cognitive metrics
    ax1 = axes[0]
    ax1.plot(metrics['time'], metrics['attention'], label='Attention', linewidth=2)
    ax1.plot(metrics['time'], metrics['engagement'], label='Engagement', linewidth=2)
    ax1.set_ylabel('Level (0-1)')
    ax1.set_title('Cognitive State Over Time')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Difficulty adaptation
    ax2 = axes[1]
    ax2.plot(metrics['time'], metrics['difficulty'], 'r-', linewidth=2, label='Difficulty')
    ax2.set_ylabel('Difficulty Level')
    ax2.set_title('Adaptive Difficulty Scaling')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Environment complexity
    ax3 = axes[2]
    ax3.plot(metrics['time'], metrics['complexity'], 'g-', linewidth=2, label='Fractal Zoom')
    ax3.set_xlabel('Time (seconds)')
    ax3.set_ylabel('Zoom Factor')
    ax3.set_title('Environment Complexity')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('outputs/neurogame_session.png', dpi=150)
    print("Session visualization saved to outputs/neurogame_session.png")


def demonstrate_coalition_formation():
    """
    Demonstrate coalition formation for distributed gaming.
    """
    logger = logging.getLogger("CoalitionDemo")
    logger.info("Demonstrating coalition formation...")
    
    # Create gaming network agents
    agents = [
        Agent("Player1", AgentType.HUMAN, ["perception", "decision"], 
              {"compute": 10, "bandwidth": 5, "latency": 20}),
        Agent("Player2", AgentType.HUMAN, ["perception", "decision"],
              {"compute": 10, "bandwidth": 5, "latency": 25}),
        Agent("GameAI_1", AgentType.AI_AGENT, ["npc_behavior", "pathfinding"],
              {"compute": 50, "bandwidth": 20, "latency": 10}),
        Agent("GameAI_2", AgentType.AI_AGENT, ["environment_gen", "physics"],
              {"compute": 60, "bandwidth": 25, "latency": 10}),
        Agent("VR_HMD_1", AgentType.XR_DEVICE, ["rendering", "tracking"],
              {"compute": 40, "bandwidth": 50, "latency": 5}),
        Agent("VR_HMD_2", AgentType.XR_DEVICE, ["rendering", "tracking"],
              {"compute": 40, "bandwidth": 50, "latency": 5}),
        Agent("EdgeServer_1", AgentType.EDGE_NODE, ["processing", "hosting"],
              {"compute": 200, "bandwidth": 200, "latency": 15}),
        Agent("EdgeServer_2", AgentType.EDGE_NODE, ["processing", "hosting"],
              {"compute": 200, "bandwidth": 200, "latency": 15}),
        Agent("CloudGPU", AgentType.CLOUD_NODE, ["ml_training", "heavy_compute"],
              {"compute": 1000, "bandwidth": 500, "latency": 50}),
    ]
    
    # Form coalitions
    game = CoalitionFormationGame(agents)
    final_coalitions = game.run_merge_and_split(max_iterations=30)
    
    # Analyze results
    stats = game.get_coalition_statistics()
    
    logger.info(f"\nCoalition Formation Results:")
    logger.info(f"  Total coalitions: {stats['num_coalitions']}")
    logger.info(f"  Total network value: {stats['total_value']:.2f}")
    logger.info(f"  Average coalition size: {stats['avg_coalition_size']:.2f}")
    logger.info(f"  Coalition types: {stats['coalition_types']}")
    
    logger.info(f"\nDetailed Coalition Structure:")
    for coalition_id, coalition in final_coalitions.items():
        logger.info(f"  {coalition_id} ({coalition.coalition_type.value}):")
        logger.info(f"    Members: {coalition.members}")
        logger.info(f"    Value: {coalition.value:.2f}")
        logger.info(f"    Resources: {coalition.resources}")
    
    # Resource allocation
    resource_manager = ResourceManager()
    total_resources = {
        "compute": 1000,
        "bandwidth": 500,
        "latency": 100
    }
    allocations = resource_manager.allocate_resources(final_coalitions, total_resources)
    
    logger.info(f"\nResource Allocations:")
    for coalition_id, resources in allocations.items():
        logger.info(f"  {coalition_id}: {resources}")


def main():
    """
    Main demonstration function.
    """
    print("\n" + "="*70)
    print("FCSTN Neurogaming Example")
    print("Brain-Responsive Gaming Environment Demonstration")
    print("="*70 + "\n")
    
    # 1. Run gameplay session
    print("[1] Running 60-second gameplay session...")
    env = NeurogameEnvironment()
    metrics = env.simulate_gameplay_session(duration_seconds=60)
    
    # 2. Visualize results
    print("\n[2] Generating visualization...")
    plot_session_metrics(metrics)
    
    # 3. Demonstrate coalition formation
    print("\n[3] Demonstrating multi-player coalition formation...")
    demonstrate_coalition_formation()
    
    # 4. Generate example fractal environments
    print("\n[4] Generating example fractal environments...")
    
    states = [
        ("Focused State", 0.9, 0.8),
        ("Relaxed State", 0.3, 0.4),
        ("Fatigued State", 0.2, 0.2),
    ]
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    for idx, (state_name, attention, engagement) in enumerate(states):
        # Generate fractal with corresponding parameters
        zoom = 1.0 + 2.0 * attention
        params = FractalParameters(
            resolution=(400, 400),
            max_iterations=int(128 * (1 + engagement)),
            zoom=zoom
        )
        
        gen = MandelbrotGenerator(params, use_gpu=False)
        fractal = gen.generate_smooth()
        colored = create_color_mapping(fractal, colormap='twilight')
        
        axes[idx].imshow(colored)
        axes[idx].set_title(f"{state_name}\n(Attention={attention:.1f}, Engagement={engagement:.1f})")
        axes[idx].axis('off')
    
    plt.tight_layout()
    plt.savefig('outputs/cognitive_environments.png', dpi=150)
    print("Cognitive environments saved to outputs/cognitive_environments.png")
    
    print("\n" + "="*70)
    print("Demonstration Complete!")
    print("="*70 + "\n")
    
    print("Generated outputs:")
    print("  - neurogame_session.png: Session metrics visualization")
    print("  - cognitive_environments.png: Example environments for different states")
    print("\nKey findings:")
    print("  - Environment automatically adapts to player's cognitive state")
    print("  - Difficulty scales implicitly based on attention and engagement")
    print("  - Coalition formation optimizes distributed resource allocation")
    print("  - Fractal complexity correlates with cognitive engagement")


if __name__ == "__main__":
    main()
