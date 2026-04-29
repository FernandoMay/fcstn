# FCSTN Quick Start Guide

## 🚀 Getting Started in 5 Minutes

This guide will get you up and running with the FCSTN platform quickly.

## Prerequisites

- Python 3.9 or higher
- 8GB RAM minimum
- (Optional) NVIDIA GPU with CUDA 11+

## Installation

### Option 1: Automated (Recommended)

```bash
# Navigate to project directory
cd fcstn/

# Run deployment script
chmod +x deploy.sh
./deploy.sh

# Activate environment
source venv/bin/activate
```

### Option 2: Manual

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install core dependencies
pip install numpy scipy matplotlib pillow sympy pandas

# Install BCI processing
pip install mne scikit-learn

# Install optional GPU support (if you have NVIDIA GPU)
pip install cupy-cuda11x

# Install testing tools
pip install pytest
```

## Running Your First Demo

### 1. Platform Demo

```bash
python fcstn_platform.py
```

**What it does:**
- Initializes all 4 layers of FCSTN
- Processes synthetic BCI signals
- Generates fractal environments
- Demonstrates cognitive adaptation
- Shows coalition formation

**Expected output:**
```
====================================================================
FCSTN Platform Demonstration
====================================================================

[1] Processing BCI signal...
  Attention: 0.723
  Engagement: 0.651
  Cognitive State: engaged

[2] Adapting environment to cognitive state...
  Fractal zoom: 2.45
  Curvature scale: 2.30

[3] Generating virtual environment...
  Generation time: 18.35 ms
  Fractal field shape: (1920, 1080)

[4] Performance Metrics:
  fps: 54.5
  latency_ms: 45.23 ms

[5] Coalition Network:
  Coalitions formed: 3
  Total network value: 385.00
```

### 2. Neurogaming Demo

```bash
python neurogaming_demo.py
```

**What it does:**
- Simulates a 60-second gaming session
- Demonstrates brain-responsive gameplay
- Shows adaptive difficulty scaling
- Generates visualization plots
- Demonstrates coalition formation

**Outputs:**
- `neurogame_session.png` - Session metrics over time
- `cognitive_environments.png` - Visual examples of adapted environments

### 3. Run Tests

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_fcstn.py::TestFractalEngine -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## Basic Usage Examples

### Generate a Fractal

```python
from src.core.fractal_engine.mandelbrot import MandelbrotGenerator, FractalParameters

# Create parameters
params = FractalParameters(
    resolution=(800, 600),
    max_iterations=256,
    center=(-0.5, 0.0),
    zoom=1.0
)

# Generate fractal
generator = MandelbrotGenerator(params, use_gpu=False)
fractal = generator.generate()

print(f"Generated fractal: {fractal.shape}")
```

### Process BCI Signal

```python
from src.core.ndan_interface.bci_processor import NDANInterface, generate_synthetic_eeg

# Initialize NDAN
ndan = NDANInterface(sampling_rate=250.0)

# Generate test signal
signal = generate_synthetic_eeg(duration=5.0)

# Process signal
features = ndan.process_signal(signal)

print(f"Attention: {features.attention_index:.3f}")
print(f"Engagement: {features.engagement_level:.3f}")
print(f"State: {features.cognitive_state.value}")
```

### Compute Metric Tensor

```python
from src.core.geometry_engine.metric_tensor import MetricTensorComputer, MetricConfig

# Create configuration
config = MetricConfig(grid_resolution=(32, 32, 32))
computer = MetricTensorComputer(config)

# Generate metric
metric = computer.minkowski_metric()  # Flat space-time

# Compute curvature
R = metric.scalar_curvature((16, 16, 16))
print(f"Curvature: {R}")
```

### Form Coalitions

```python
from src.core.coalition_network.coalition_formation import Agent, AgentType, CoalitionFormationGame

# Create agents
agents = [
    Agent("H1", AgentType.HUMAN, [], {"compute": 10}),
    Agent("A1", AgentType.AI_AGENT, [], {"compute": 50}),
    Agent("XR1", AgentType.XR_DEVICE, [], {"compute": 30}),
]

# Form coalitions
game = CoalitionFormationGame(agents)
coalitions = game.run_merge_and_split(max_iterations=20)

stats = game.get_coalition_statistics()
print(f"Coalitions: {stats['num_coalitions']}")
print(f"Total value: {stats['total_value']:.2f}")
```

### Complete Pipeline

```python
from fcstn_platform import FCSTPlatform

# Initialize platform
platform = FCSTPlatform()
platform.start()

# Simulate BCI input
from src.core.ndan_interface.bci_processor import generate_synthetic_eeg
signal = generate_synthetic_eeg(duration=5.0)

# Process through full pipeline
cognitive_features = platform.process_cognitive_input(signal)
platform.adapt_environment(cognitive_features)
environment = platform.generate_environment()

print(f"Environment generated in {environment['generation_time_ms']:.2f}ms")

platform.stop()
```

## Configuration

Edit `config/platform_config.yaml` to customize:

```yaml
# Key settings
fractal:
  resolution:
    width: 1920
    height: 1080
  max_iterations: 256

ndan:
  enabled: true
  bci_sampling_rate: 250.0

coalition:
  enabled: true
  max_iterations: 50

performance:
  target_fps: 60
  target_total_latency_ms: 50.0
```

## Troubleshooting

### "ModuleNotFoundError"
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "CUDA not available" (GPU warnings)
```python
# This is normal if you don't have NVIDIA GPU
# The system will use CPU mode (slower but functional)

# To check GPU availability:
python -c "try: import cupy; print('GPU available')
except: print('Using CPU mode')"
```

### Slow performance
```python
# 1. Reduce resolution
params.resolution = (640, 480)

# 2. Reduce iterations
params.max_iterations = 128

# 3. Use smaller grid
config.grid_resolution = (32, 32, 32)
```

### Tests failing
```bash
# Run tests with verbose output
pytest tests/ -v --tb=long

# Common issues:
# - Missing dependencies: pip install -r requirements.txt
# - Import errors: Add src to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

## Next Steps

### 1. Explore Examples
```bash
cd examples/
python neurogaming_demo.py
```

### 2. Read Documentation
- Architecture: `docs/architecture.md`
- Validation Plan: `docs/experimental_roadmap.md`
- API Reference: Docstrings in code

### 3. Customize
- Modify `config/platform_config.yaml`
- Extend classes in `src/core/`
- Create new applications

### 4. Deploy
- See `docs/architecture.md` for deployment strategies
- Configure edge/cloud infrastructure
- Set up XR hardware integration

## Common Tasks

### Create Custom Fractal Parameters
```python
params = FractalParameters(
    center=(-0.75, 0.1),  # Interesting region
    zoom=2.0,              # Zoom level
    max_iterations=512,    # More detail
    resolution=(1920, 1080)
)
```

### Connect Real BCI Hardware
```python
# See docs/architecture.md for hardware integration
# Requires OpenBCI, Emotiv, or compatible device

# Basic pattern:
signal = read_from_hardware()  # Your hardware API
features = ndan.process_signal(signal)
platform.adapt_environment(features)
```

### Extend with New Features
```python
# Create custom fractal generator
class MyFractalGenerator(MandelbrotGenerator):
    def generate(self):
        # Your custom algorithm
        pass

# Create custom coalition strategy
class MyCoalitionGame(CoalitionFormationGame):
    def _compute_coalition_value(self, members):
        # Your custom value function
        pass
```

## Performance Tips

1. **Use GPU**: Install CuPy for 10-50x speedup
2. **Reduce Resolution**: Lower resolution = higher FPS
3. **Cache Results**: Enable caching in config
4. **Async Processing**: Use separate threads for BCI/rendering
5. **Edge Computing**: Deploy processing near users

## Getting Help

- **Documentation**: Check `docs/` folder
- **Examples**: See `examples/` folder
- **Tests**: Run `pytest tests/ -v` to see working examples
- **Issues**: Check test output for debugging hints

## Resources

- Paper: "Fractal Cognitive Space-Time Networks" (included)
- Architecture: `docs/architecture.md`
- Roadmap: `docs/experimental_roadmap.md`
- Config: `config/platform_config.yaml`

---

**Ready to build cognitive virtual environments!** 🎮🧠🌌
