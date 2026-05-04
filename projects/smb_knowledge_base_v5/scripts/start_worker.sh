#!/bin/bash
# Start Temporal Worker for SMB Knowledge Base v5.0

set -e

# Navigate to project directory
cd "$(dirname "$0")/.."

# Activate venv if available
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Run worker
python -m orchestration.worker
