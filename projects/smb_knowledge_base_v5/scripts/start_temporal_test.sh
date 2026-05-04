#!/bin/bash
# Start Temporal test with pilot videos

set -e

cd "$(dirname "$0")/.."

# Start worker in background
echo "Starting Temporal worker..."
python -m orchestration.worker &
WORKER_PID=$!

# Wait for worker to start
sleep 2

# Start test
echo "Starting test..."
python test_v5_pilot.py

# Cleanup
kill $WORKER_PID 2>/dev/null || true
