#!/bin/bash
# v5_setup.sh - Set up SMB Knowledge Base v5.0 environment

set -e

echo "=== SMB Knowledge Base v5.0 Setup ==="

# Check prerequisites
echo "Checking prerequisites..."

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "Python version: $PYTHON_VERSION"
if [[ ! "$PYTHON_VERSION" =~ ^3\.11 ]]; then
    echo "Warning: Python 3.11 recommended"
fi

# Check for ClawTeam-OpenClaw
if [ ! -d "/home/ml/ClawTeam-OpenClaw" ]; then
    echo "Cloning ClawTeam-OpenClaw..."
    git clone https://github.com/win4r/ClawTeam-OpenClaw.git
fi

# Install ClawTeam if not installed
if ! pip show clawteam > /dev/null 2>&1; then
    cd /home/ml/ClawTeam-OpenClaw
    pip install -e .
    cd /home/ml
else
    echo "ClawTeam already installed"
fi

# Create v5.0 directory
mkdir -p ~/smb_knowledge_base_v5
mkdir -p ~/smb_knowledge_base_v5/{orchestration,ingestion,skills,teams,validation,graph,utils}

# Check for Temporal
if ! command -v temporal &> /dev/null; then
    echo "Installing Temporal CLI..."
    curl nonprofit.temporal.io/temporal -o /tmp/temporal
    chmod +x /tmp/temporal
    sudo mv /tmp/temporal /usr/local/bin/
else
    echo "Temporal CLI already installed"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install temporalio==1.4
pip install temporal-sdk-core==1.4
pip install google-api-python-client
pip install google-auth-httplib2
pip install google-auth-oauthlib
pip install dspy-ai
pip install langgraph
pip install openai-whisper
pip install librosa
pip install soundfile
pip install ib-insync
pip install tradovate-ws
pip install prometheus-client
pip install structlog
pip install python-json-logger
pip install qdrant-client
pip install neo4j
pip install pydantic>=2.6.0,<3.0.0
pip install numpy
pip install pandas
pip install scipy
pip install requests
pip install tqdm

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Docker not installed - installing Temporal locally not possible"
else
    echo "Docker installed - can run Temporal server locally"
    
    # Check if Temporal container is running
    if ! docker ps | grep -q temporal; then
        echo "Starting Temporal server..."
        docker run -d -p 7233:7233 -p 8233:8233 --name temporal temporalio/auto-setup:latest
        sleep 5
        echo "Temporal server started"
    else
        echo "Temporal container already running"
    fi
fi

# Copy v5.0 files
echo "Copying v5.0 files..."
cp -r ~/ClawTeam-OpenClaw ~/smb_knowledge_base_v5/
cp ~/smb_knowledge_base_v4/core/smb_schema_v4.py ~/smb_knowledge_base_v5/core/ 2>/dev/null || true
cp ~/smb_knowledge_base_v4/ingestion/structured_extractor.py ~/smb_knowledge_base_v5/ingestion/ 2>/dev/null || true
cp ~/smb_knowledge_base_v4/validation/validator_agent.py ~/smb_knowledge_base_v5/validation/ 2>/dev/null || true
cp ~/smb_knowledge_base_v4/graph/knowledge_graph_builder.py ~/smb_knowledge_base_v5/graph/ 2>/dev/null || true

# Copy v5-specific files
cp ~/smb_knowledge_base_v5/orchestration/workflows.py ~/smb_knowledge_base_v5/orchestration/workflows.py
cp ~/smb_knowledge_base_v5/ingestion/youtube_monitor.py ~/smb_knowledge_base_v5/ingestion/youtube_monitor.py
cp ~/smb_knowledge_base_v5/skills/trading_skills.py ~/smb_knowledge_base_v5/skills/trading_skills.py
cp ~/smb_knowledge_base_v5/teams/smb_trading_team.yaml ~/smb_knowledge_base_v5/teams/smb_trading_team.yaml
cp ~/smb_knowledge_base_v5/orchestration/self_improvement.py ~/smb_knowledge_base_v5/orchestration/self_improvement.py

# Set permissions
chmod +x ~/smb_knowledge_base_v5/ingestion/youtube_monitor.py
chmod +x ~/smb_knowledge_base_v5/orchestration/worker.py

echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Start worker: cd ~/smb_knowledge_base_v5 && python orchestration/worker.py"
echo "2. Test video: python orchestration/client.py start --url 'https://youtube.com/watch?v=45eaVU5NVi8'"
echo "3. Check status: python orchestration/client.py list"
echo ""
echo "For full v5 guide: cat ~/SMB_KNOWLEDGE_BASE_STEP_BY_STEP_v5.md"
