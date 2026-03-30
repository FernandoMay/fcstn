"""
FCSTN Platform - Main Integration Module
Coordinates all subsystems: fractal generation, metric geometry, NDAN, and coalitions
"""

import numpy as np
from typing import Dict, Optional, List
import logging
from dataclasses import dataclass
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Core module imports
from src.core.fractal_engine.mandelbrot import MandelbrotGenerator, FractalParameters
from src.core.geometry_engine.metric_tensor import MetricTensorComputer, MetricConfig
from src.core.ndan_interface.bci_processor import NDANInterface, BCISignal, CognitiveFeatures
from src.core.coalition_network.coalition_formation import (
    CoalitionFormationGame, Agent, AgentType, ResourceManager
)


@dataclass
class PlatformConfig:
    """Configuration for FCSTN platform"""
    # Fractal parameters
    fractal_resolution: tuple = (1920, 1080)
    fractal_max_iterations: int = 256
    
    # Geometry parameters
    geometry_resolution: tuple = (64, 64, 64)
    curvature_scale: float = 1.0
    
    # NDAN parameters
    bci_sampling_rate: float = 250.0
    
    # Coalition parameters
    enable_coalition_formation: bool = True
    coalition_update_interval: float = 5.0  # seconds
    
    # Performance targets
    target_fps: int = 60
    target_latency_ms: float = 50.0


class FCSTPlatform:
    """
    Main FCSTN platform coordinating all subsystems.
    
    Architecture layers:
    - L1: Cognitive Layer (Human + XR + AI)
    - L2: Interface Layer (NDAN)
    - L3: Geometry Engine (Fractal + Metric)
    - L4: Infrastructure (Coalitions + Distributed Compute)
    """
    
    def __init__(self, config: Optional[PlatformConfig] = None):
        """
        Initialize FCSTN platform.
        
        Args:
            config: Platform configuration
        """
        self.config = config or PlatformConfig()
        self.running = False
        
        # Initialize subsystems
        self._initialize_subsystems()
        
        # Performance metrics
        self.metrics = {
            'fps': 0.0,
            'latency_ms': 0.0,
            'frame_count': 0,
            'adaptation_accuracy': 0.0
        }
        
        logging.info("FCSTN Platform initialized")
    
    def _initialize_subsystems(self):
        """Initialize all platform subsystems"""
        # Layer 3: Geometry Engine
        fractal_params = FractalParameters(
            resolution=self.config.fractal_resolution,
            max_iterations=self.config.fractal_max_iterations
        )
        self.fractal_generator = MandelbrotGenerator(fractal_params)
        
        metric_config = MetricConfig(
            grid_resolution=self.config.geometry_resolution,
            curvature_scale=self.config.curvature_scale
        )
        self.geometry_computer = MetricTensorComputer(metric_config)
        
        # Layer 2: NDAN Interface
        self.ndan = NDANInterface(sampling_rate=self.config.bci_sampling_rate)
        
        # Layer 4: Coalition Network (optional)
        if self.config.enable_coalition_formation:
            self.agents = self._create_default_agents()
            self.coalition_game = CoalitionFormationGame(self.agents)
            self.resource_manager = ResourceManager()
        
        # Current state
        self.current_fractal = None
        self.current_metric = None
        self.current_cognitive_features = None
        
        logging.info("All subsystems initialized")
    
    def _create_default_agents(self) -> List[Agent]:
        """Create default agent set for coalition formation"""
        return [
            Agent("Human_1", AgentType.HUMAN, ["perception"], {"compute": 10, "bandwidth": 5}),
            Agent("AI_Adaptive_1", AgentType.AI_AGENT, ["inference"], {"compute": 50, "bandwidth": 20}),
            Agent("XR_Device_1", AgentType.XR_DEVICE, ["rendering"], {"compute": 30, "bandwidth": 40}),
            Agent("Edge_1", AgentType.EDGE_NODE, ["processing"], {"compute": 100, "bandwidth": 100}),
        ]
    
    def process_cognitive_input(self, bci_signal: BCISignal) -> CognitiveFeatures:
        """
        Process incoming BCI signal through NDAN.
        
        Args:
            bci_signal: Raw BCI signal from sensors
            
        Returns:
            Extracted cognitive features
        """
        start_time = time.time()
        
        features = self.ndan.process_signal(bci_signal)
        self.current_cognitive_features = features
        
        # Update latency metric
        latency = (time.time() - start_time) * 1000
        self.metrics['latency_ms'] = latency
        
        return features
    
    def adapt_environment(self, cognitive_features: Optional[CognitiveFeatures] = None):
        """
        Adapt virtual environment based on cognitive state.
        
        Bidirectional feedback loop:
        Cognition -> NDAN -> Environment Parameters -> Geometry -> Rendering
        
        Args:
            cognitive_features: Cognitive features (uses current if None)
        """
        if cognitive_features is None:
            cognitive_features = self.current_cognitive_features
        
        if cognitive_features is None:
            logging.warning("No cognitive features available for adaptation")
            return
        
        # Convert cognitive features to environment parameters
        env_params = self.ndan.get_environment_parameters(cognitive_features)
        
        # Update fractal parameters
        self.fractal_generator.params.zoom = env_params['fractal_zoom']
        
        # Update geometry curvature
        self.geometry_computer.config.curvature_scale = env_params['curvature_scale']
        
        # Regenerate environment
        self.current_fractal = self.fractal_generator.generate_smooth()
        self.current_metric = self.geometry_computer.compute_from_fractal(self.current_fractal)
        
        logging.debug(f"Environment adapted: zoom={env_params['fractal_zoom']:.2f}, "
                     f"curvature={env_params['curvature_scale']:.2f}")
    
    def generate_environment(self) -> Dict:
        """
        Generate complete virtual environment.
        
        Returns:
            Dictionary containing fractal field, metric tensor, and metadata
        """
        start_time = time.time()
        
        # Generate fractal
        fractal_field = self.fractal_generator.generate_smooth()
        
        # Compute metric tensor
        metric_tensor = self.geometry_computer.compute_from_fractal(fractal_field)
        
        # Package environment
        environment = {
            'fractal_field': fractal_field,
            'metric_tensor': metric_tensor,
            'timestamp': time.time(),
            'generation_time_ms': (time.time() - start_time) * 1000
        }
        
        # Update FPS metric
        self.metrics['frame_count'] += 1
        self.metrics['fps'] = 1000.0 / environment['generation_time_ms']
        
        return environment
    
    def run_coalition_optimization(self):
        """Run coalition formation to optimize resource allocation"""
        if not self.config.enable_coalition_formation:
            return
        
        # Run merge-and-split algorithm
        coalitions = self.coalition_game.run_merge_and_split(max_iterations=10)
        
        # Allocate resources
        total_resources = {
            'compute': 500,
            'bandwidth': 300
        }
        allocations = self.resource_manager.allocate_resources(coalitions, total_resources)
        
        stats = self.coalition_game.get_coalition_statistics()
        logging.info(f"Coalition optimization: {stats['num_coalitions']} coalitions, "
                    f"total value: {stats['total_value']:.2f}")
    
    def start(self):
        """Start the FCSTN platform"""
        self.running = True
        logging.info("FCSTN Platform started")
        
        # Initial environment generation
        self.generate_environment()
        
        # Initial coalition formation
        if self.config.enable_coalition_formation:
            self.run_coalition_optimization()
    
    def stop(self):
        """Stop the FCSTN platform"""
        self.running = False
        logging.info("FCSTN Platform stopped")
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        return self.metrics.copy()
    
    def launch_xr_world(self, geometry=None):
        """
        Launch XR immersive world (placeholder for XR integration).
        
        Args:
            geometry: Optional pre-generated geometry
        """
        if geometry is None:
            env = self.generate_environment()
            geometry = env['metric_tensor']
        
        logging.info("Launching XR world...")
        logging.info(f"  Fractal resolution: {self.config.fractal_resolution}")
        logging.info(f"  Geometry resolution: {self.config.geometry_resolution}")
        logging.info(f"  Target FPS: {self.config.target_fps}")
        
        # In full implementation, this would:
        # 1. Initialize XR runtime (OpenVR, OpenXR)
        # 2. Create rendering pipeline
        # 3. Start cognitive feedback loop
        # 4. Begin real-time environment adaptation
        
        print("\n=== XR World Launched ===")
        print("Virtual environment ready for exploration")
        print("Cognitive adaptation: ENABLED")
        print("Coalition network: " + ("ACTIVE" if self.config.enable_coalition_formation else "DISABLED"))


def run_demo():
    """Run a demonstration of the FCSTN platform"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("FCSTN Platform Demonstration")
    print("="*60 + "\n")
    
    # Initialize platform
    platform = FCSTPlatform()
    platform.start()
    
    # Simulate BCI input
    from src.core.ndan_interface.bci_processor import generate_synthetic_eeg
    
    print("\n[1] Processing BCI signal...")
    bci_signal = generate_synthetic_eeg(duration=5.0)
    cognitive_features = platform.process_cognitive_input(bci_signal)
    
    print(f"  Attention: {cognitive_features.attention_index:.3f}")
    print(f"  Engagement: {cognitive_features.engagement_level:.3f}")
    print(f"  Cognitive State: {cognitive_features.cognitive_state.value}")
    
    # Adapt environment
    print("\n[2] Adapting environment to cognitive state...")
    platform.adapt_environment(cognitive_features)
    
    env_params = platform.ndan.get_environment_parameters(cognitive_features)
    print(f"  Fractal zoom: {env_params['fractal_zoom']:.2f}")
    print(f"  Curvature scale: {env_params['curvature_scale']:.2f}")
    
    # Generate environment
    print("\n[3] Generating virtual environment...")
    environment = platform.generate_environment()
    print(f"  Generation time: {environment['generation_time_ms']:.2f} ms")
    print(f"  Fractal field shape: {environment['fractal_field'].shape}")
    
    # Performance metrics
    print("\n[4] Performance Metrics:")
    metrics = platform.get_performance_metrics()
    for key, value in metrics.items():
        if 'time' in key or 'latency' in key:
            print(f"  {key}: {value:.2f} ms")
        elif 'fps' in key:
            print(f"  {key}: {value:.1f}")
        else:
            print(f"  {key}: {value}")
    
    # Coalition statistics
    if platform.config.enable_coalition_formation:
        print("\n[5] Coalition Network:")
        stats = platform.coalition_game.get_coalition_statistics()
        print(f"  Coalitions formed: {stats['num_coalitions']}")
        print(f"  Total network value: {stats['total_value']:.2f}")
        print(f"  Coalition types: {stats['coalition_types']}")
    
    print("\n" + "="*60)
    print("Demo complete. Platform ready for XR deployment.")
    print("="*60 + "\n")
    
    platform.stop()


if __name__ == "__main__":
    run_demo()
