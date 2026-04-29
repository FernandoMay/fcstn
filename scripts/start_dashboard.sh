#!/bin/bash
# Start the FCSTN Web Dashboard

echo "====================================="
echo "Starting FCSTN Web Dashboard"
echo "====================================="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ensure dependencies are installed
echo "Checking dependencies..."
pip install -r requirements.txt > /dev/null

# Set environment variable to fix numba caching issue with MNE
export NUMBA_CACHE_DIR=/tmp/numba_cache
mkdir -p /tmp/numba_cache

# Start the uvicorn server
echo "Starting API Server on http://localhost:8000/dashboard"
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
