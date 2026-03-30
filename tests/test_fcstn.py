"""
Comprehensive Test Suite for FCSTN Platform
"""

import pytest
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.fractal_engine.mandelbrot import MandelbrotGenerator, FractalParameters
from core.geometry_engine.metric_tensor import MetricTensorComputer, MetricConfig, GeodesicComputer
from core.ndan_interface.bci_processor import BCIProcessor, BCISignal, NDANInterface, generate_synthetic_eeg
from core.coalition_network.coalition_formation import Agent, AgentType, CoalitionFormationGame


class TestFractalEngine:
    """Tests for fractal generation"""
    
    def test_mandelbrot_generation(self):
        """Test basic Mandelbrot set generation"""
        params = FractalParameters(
            resolution=(256, 256),
            max_iterations=100
        )
        generator = MandelbrotGenerator(params, use_gpu=False)
        fractal = generator.generate()
        
        assert fractal.shape == (256, 256)
        assert fractal.min() >= 0
        assert fractal.max() <= params.max_iterations
    
    def test_smooth_coloring(self):
        """Test smooth iteration coloring"""
        params = FractalParameters(resolution=(128, 128))
        generator = MandelbrotGenerator(params, use_gpu=False)
        fractal = generator.generate_smooth()
        
        assert fractal.shape == (128, 128)
        assert not np.all(fractal == fractal.astype(int))  # Should have fractional values
    
    def test_multiscale_generation(self):
        """Test multi-scale fractal generation"""
        params = FractalParameters(resolution=(64, 64))
        generator = MandelbrotGenerator(params, use_gpu=False)
        scales = generator.generate_multiscale(num_scales=3)
        
        assert len(scales) == 3
        for zoom, fractal in scales.items():
            assert fractal.shape == (64, 64)
    
    def test_density_field(self):
        """Test fractal density field computation"""
        params = FractalParameters(resolution=(64, 64))
        generator = MandelbrotGenerator(params, use_gpu=False)
        density = generator.compute_density_field()
        
        assert density.shape == (64, 64)
        assert density.min() >= 0.0
        assert density.max() <= 1.0
    
    def test_interesting_regions(self):
        """Test identification of complex regions"""
        params = FractalParameters(resolution=(128, 128))
        generator = MandelbrotGenerator(params, use_gpu=False)
        regions = generator.find_interesting_regions(threshold=0.5)
        
        assert isinstance(regions, list)
        assert len(regions) > 0
        for x, y, complexity in regions:
            assert 0 <= x < 128
            assert 0 <= y < 128
            assert complexity >= 0.5


class TestGeometryEngine:
    """Tests for metric tensor computation"""
    
    def test_minkowski_metric(self):
        """Test flat space-time metric"""
        config = MetricConfig(grid_resolution=(16, 16, 16))
        computer = MetricTensorComputer(config)
        metric = computer.minkowski_metric()
        
        assert metric.g.shape == (16, 16, 16, 4, 4)
        
        # Check diagonal at origin
        origin = (8, 8, 8)
        assert metric.g[origin, 0, 0] == -1.0  # g_tt
        assert metric.g[origin, 1, 1] == 1.0   # g_xx
        assert metric.g[origin, 2, 2] == 1.0   # g_yy
        assert metric.g[origin, 3, 3] == 1.0   # g_zz
    
    def test_schwarzschild_metric(self):
        """Test curved space-time metric"""
        config = MetricConfig(grid_resolution=(16, 16, 16))
        computer = MetricTensorComputer(config)
        metric = computer.schwarzschild_metric(mass=1.0)
        
        assert metric.g.shape == (16, 16, 16, 4, 4)
        
        # Metric should be different from Minkowski far from origin
        edge = (15, 15, 15)
        assert metric.g[edge, 0, 0] != -1.0
    
    def test_fractal_to_metric(self):
        """Test conversion from fractal to metric tensor"""
        # Generate small fractal
        fractal_params = FractalParameters(resolution=(32, 32))
        fractal_gen = MandelbrotGenerator(fractal_params, use_gpu=False)
        fractal = fractal_gen.generate()
        
        # Convert to metric
        config = MetricConfig(grid_resolution=(32, 32, 8))
        computer = MetricTensorComputer(config)
        metric = computer.compute_from_fractal(fractal)
        
        assert metric.g.shape == (32, 32, 8, 4, 4)
    
    def test_curvature_computation(self):
        """Test scalar curvature computation"""
        config = MetricConfig(grid_resolution=(8, 8, 8))
        computer = MetricTensorComputer(config)
        metric = computer.schwarzschild_metric(mass=1.0)
        
        center = (4, 4, 4)
        R = metric.scalar_curvature(center)
        
        assert isinstance(R, float)
        # Curved space should have non-zero curvature
        assert abs(R) > 1e-6


class TestNDANInterface:
    """Tests for BCI signal processing"""
    
    def test_signal_generation(self):
        """Test synthetic EEG generation"""
        signal = generate_synthetic_eeg(duration=2.0, sampling_rate=250.0)
        
        assert signal.data.shape[0] == 8  # 8 channels
        assert signal.data.shape[1] == 500  # 2 seconds * 250 Hz
        assert signal.sampling_rate == 250.0
    
    def test_preprocessing(self):
        """Test signal preprocessing"""
        signal = generate_synthetic_eeg(duration=1.0)
        processor = BCIProcessor(sampling_rate=250.0)
        
        preprocessed = processor.preprocess(signal)
        
        assert preprocessed.shape == signal.data.shape
        # Mean should be close to zero after baseline removal
        assert abs(np.mean(preprocessed)) < 1.0
    
    def test_band_power_extraction(self):
        """Test frequency band power extraction"""
        signal = generate_synthetic_eeg(duration=5.0)
        processor = BCIProcessor(sampling_rate=250.0)
        
        preprocessed = processor.preprocess(signal)
        alpha_power = processor.extract_band_power(preprocessed, (8.0, 13.0))
        
        assert alpha_power > 0
        assert isinstance(alpha_power, float)
    
    def test_feature_extraction(self):
        """Test full cognitive feature extraction"""
        signal = generate_synthetic_eeg(duration=5.0)
        processor = BCIProcessor(sampling_rate=250.0)
        
        features = processor.extract_features(signal)
        
        assert 0 <= features.attention_index <= 1
        assert 0 <= features.engagement_level <= 1
        assert 0 <= features.workload <= 1
        assert features.alpha_power > 0
        assert features.beta_power > 0
    
    def test_ndan_processing(self):
        """Test complete NDAN pipeline"""
        signal = generate_synthetic_eeg(duration=5.0)
        ndan = NDANInterface(sampling_rate=250.0)
        
        features = ndan.process_signal(signal)
        env_params = ndan.get_environment_parameters(features)
        
        assert 'complexity_level' in env_params
        assert 'curvature_scale' in env_params
        assert env_params['curvature_scale'] > 0
    
    def test_cognitive_trends(self):
        """Test cognitive trend computation"""
        ndan = NDANInterface()
        
        # Process multiple signals
        for _ in range(10):
            signal = generate_synthetic_eeg(duration=1.0)
            ndan.process_signal(signal)
        
        trends = ndan.get_cognitive_trend(window=5)
        
        assert 'attention_trend' in trends
        assert 'engagement_trend' in trends
        assert -1 <= trends['attention_trend'] <= 1


class TestCoalitionNetwork:
    """Tests for coalition formation"""
    
    def test_agent_creation(self):
        """Test agent instantiation"""
        agent = Agent(
            id="test_1",
            agent_type=AgentType.HUMAN,
            capabilities=["perception"],
            resources={"compute": 10, "bandwidth": 5}
        )
        
        assert agent.id == "test_1"
        assert agent.agent_type == AgentType.HUMAN
        assert agent.resources["compute"] == 10
    
    def test_coalition_formation(self):
        """Test basic coalition formation"""
        agents = [
            Agent("H1", AgentType.HUMAN, [], {"compute": 10}),
            Agent("A1", AgentType.AI_AGENT, [], {"compute": 50}),
            Agent("XR1", AgentType.XR_DEVICE, [], {"compute": 30}),
        ]
        
        game = CoalitionFormationGame(agents)
        coalitions = game.run_merge_and_split(max_iterations=10)
        
        assert len(coalitions) > 0
        total_members = sum(len(c.members) for c in coalitions.values())
        assert total_members == len(agents)
    
    def test_coalition_value(self):
        """Test coalition value computation"""
        agents = [
            Agent("H1", AgentType.HUMAN, [], {"compute": 10, "bandwidth": 5}),
            Agent("A1", AgentType.AI_AGENT, [], {"compute": 50, "bandwidth": 20}),
            Agent("XR1", AgentType.XR_DEVICE, [], {"compute": 30, "bandwidth": 40}),
        ]
        
        game = CoalitionFormationGame(agents)
        
        # Value of all together should include synergy
        all_members = {"H1", "A1", "XR1"}
        value_all = game._compute_coalition_value(all_members)
        
        # Value of individuals
        value_individuals = sum(
            game._compute_coalition_value({agent.id})
            for agent in agents
        )
        
        # Coalition should have synergy bonus
        assert value_all > value_individuals
    
    def test_merge_and_split(self):
        """Test merge and split operations"""
        agents = [
            Agent("A1", AgentType.AI_AGENT, [], {"compute": 50}),
            Agent("A2", AgentType.AI_AGENT, [], {"compute": 50}),
        ]
        
        game = CoalitionFormationGame(agents)
        
        # Initial state: 2 singleton coalitions
        assert len(game.coalitions) == 2
        
        # After optimization, they might merge
        final_coalitions = game.run_merge_and_split(max_iterations=10)
        
        # Check convergence
        stats = game.get_coalition_statistics()
        assert stats['num_coalitions'] > 0
        assert stats['total_value'] > 0


class TestIntegration:
    """Integration tests for complete system"""
    
    def test_cognitive_to_environment(self):
        """Test cognitive signal to environment generation"""
        from fcstn_platform import FCSTPlatform
        
        platform = FCSTPlatform()
        platform.start()
        
        # Generate BCI signal
        signal = generate_synthetic_eeg(duration=5.0)
        
        # Process through NDAN
        features = platform.process_cognitive_input(signal)
        
        # Adapt environment
        platform.adapt_environment(features)
        
        # Generate environment
        env = platform.generate_environment()
        
        assert 'fractal_field' in env
        assert 'metric_tensor' in env
        assert env['fractal_field'].shape == (1920, 1080)
        
        platform.stop()
    
    def test_performance_metrics(self):
        """Test performance measurement"""
        from fcstn_platform import FCSTPlatform
        
        platform = FCSTPlatform()
        platform.start()
        
        # Generate environment multiple times
        for _ in range(5):
            platform.generate_environment()
        
        metrics = platform.get_performance_metrics()
        
        assert 'fps' in metrics
        assert 'latency_ms' in metrics
        assert metrics['frame_count'] == 5
        
        platform.stop()


@pytest.fixture
def sample_fractal():
    """Fixture providing a sample fractal field"""
    params = FractalParameters(resolution=(64, 64), max_iterations=100)
    generator = MandelbrotGenerator(params, use_gpu=False)
    return generator.generate()


@pytest.fixture
def sample_bci_signal():
    """Fixture providing a sample BCI signal"""
    return generate_synthetic_eeg(duration=5.0, sampling_rate=250.0)


def test_end_to_end_pipeline(sample_fractal, sample_bci_signal):
    """Test complete processing pipeline"""
    # 1. Process BCI signal
    processor = BCIProcessor()
    features = processor.extract_features(sample_bci_signal)
    
    # 2. Generate environment from fractal
    config = MetricConfig(grid_resolution=(64, 64, 16))
    computer = MetricTensorComputer(config)
    metric = computer.compute_from_fractal(sample_fractal)
    
    # 3. Adapt based on cognition
    adaptive_metric = computer.adaptive_metric_from_cognition(
        np.array([features.attention_index, features.engagement_level]),
        metric
    )
    
    assert adaptive_metric.g.shape == (64, 64, 16, 4, 4)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
