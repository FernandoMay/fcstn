#!/bin/bash
# FCSTN Platform Deployment Script

set -e  # Exit on error

echo "===================================="
echo "FCSTN Platform Deployment"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then 
    print_status "Python $PYTHON_VERSION (>= $REQUIRED_VERSION required)"
else
    print_error "Python $PYTHON_VERSION found, but >= $REQUIRED_VERSION required"
    exit 1
fi

# Check for GPU
echo ""
echo "Checking for GPU support..."
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n 1)
    print_status "NVIDIA GPU detected: $GPU_INFO"
    GPU_AVAILABLE=true
else
    print_warning "No NVIDIA GPU detected. Will use CPU mode (slower)"
    GPU_AVAILABLE=false
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_status "Pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies..."

# Core dependencies
print_status "Installing core dependencies..."
pip install numpy scipy matplotlib pillow > /dev/null 2>&1

# Scientific computing
print_status "Installing scientific computing packages..."
pip install sympy pandas numba > /dev/null 2>&1

# GPU support (if available)
if [ "$GPU_AVAILABLE" = true ]; then
    print_status "Installing GPU acceleration packages..."
    pip install cupy-cuda11x pycuda > /dev/null 2>&1
fi

# Graphics
print_status "Installing graphics packages..."
pip install moderngl pyrr glfw > /dev/null 2>&1

# BCI and signal processing
print_status "Installing BCI packages..."
pip install mne scikit-learn pywavelets > /dev/null 2>&1

# Machine learning
print_status "Installing ML frameworks..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu > /dev/null 2>&1

# Networking
print_status "Installing networking packages..."
pip install aiohttp websockets grpcio protobuf > /dev/null 2>&1

# Utilities
print_status "Installing utilities..."
pip install pyyaml python-dotenv pydantic loguru tqdm click > /dev/null 2>&1

# Development dependencies
echo ""
echo "Installing development dependencies..."
pip install pytest pytest-asyncio pytest-cov black flake8 mypy > /dev/null 2>&1
print_status "Development dependencies installed"

# Create necessary directories
echo ""
echo "Creating directory structure..."
mkdir -p data cache logs snapshots
print_status "Directories created"

# Run tests
echo ""
echo "Running tests..."
if python -m pytest tests/ -v --tb=short; then
    print_status "All tests passed"
else
    print_warning "Some tests failed. Check output above."
fi

# Build documentation (optional)
if command -v sphinx-build &> /dev/null; then
    echo ""
    echo "Building documentation..."
    if [ -d "docs/_build" ]; then
        rm -rf docs/_build
    fi
    # sphinx-build -b html docs docs/_build > /dev/null 2>&1
    # print_status "Documentation built"
fi

# Summary
echo ""
echo "===================================="
echo "Deployment Summary"
echo "===================================="
echo ""
print_status "Virtual environment: $(pwd)/venv"
print_status "Python version: $PYTHON_VERSION"
if [ "$GPU_AVAILABLE" = true ]; then
    print_status "GPU support: Enabled ($GPU_INFO)"
else
    print_warning "GPU support: Disabled (CPU mode)"
fi
print_status "Core modules: Installed"
print_status "Tests: Completed"

echo ""
echo "===================================="
echo "Next Steps"
echo "===================================="
echo ""
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Run the demo:"
echo "   python neurogaming_demo.py"
echo ""
echo "3. Or start the platform:"
echo "   python fcstn_platform.py"
echo ""
echo "4. Configure settings:"
echo "   Edit platform_config.yaml"
echo ""
echo "5. Run tests:"
echo "   pytest tests/ -v"
echo ""

# Create activation helper
cat > activate.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
echo "FCSTN environment activated"
echo "Python: $(python --version)"
echo "Run 'python fcstn_platform.py' to start"
EOF
chmod +x activate.sh
print_status "Created activation helper: ./activate.sh"

echo ""
print_status "Deployment complete!"
