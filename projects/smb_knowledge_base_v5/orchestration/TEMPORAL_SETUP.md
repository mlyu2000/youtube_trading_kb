# Temporal.io Installation and Configuration

This guide covers installing and running Temporal for SMB Knowledge Base v5.0.

## Architecture

```
YouTube Upload → YouTube Monitor → Temporal Client → ProcessNewVideo Workflow
                                                           ↓
                                            +--------------+--------------+
                                            |              |              |
                                            ↓              ↓              ↓
                                    ExtractAndValidate     RunBacktest    UpdateKnowledgeGraph
                                            ↓
                                   RunSwarmAnalysis (ClawTeam)
                                            ↓
                                    Multi-Agent Swarm (Hermes)
```

## Installation

### Option 1: Temporal Cloud (Recommended)

```bash
# Create Temporal Cloud account
# Navigate to https://cloud.temporal.io
# Create namespace: "smb-knowledge-base"

# Install Temporal CLI
curl nonprofit.temporal.io/temporal -o temporal
chmod +x temporal
sudo mv temporal /usr/local/bin/

# Configure CLI
temporal config create-profile --address <your-namespace.temporal.io:7233>
temporal config set-profile --profile default
```

### Option 2: Local Temporal Server

```bash
# Using Docker
docker run -p 7233:7233 -p 8233:8233 temporalio/auto-setup:latest

# Or with custom config
cat > temporal-config.yaml <<EOF
# tempal config
EOF

docker run -v $(pwd)/temporal-config.yaml:/etc/temporal/config.yaml \
           -p 7233:7233 -p 8233:8233 temporalio/auto-setup
```

### Python SDK

```bash
# Install Temporal Python SDK
pip install temporalio==1.4
pip install temporal-sdk-core==1.4
```

## Worker Deployment

### Start Local Worker

```bash
cd ~/smb_knowledge_base_v5

# Run worker (connects to local Temporal)
python orchestration/worker.py

# Worker will:
# - Connect to Temporal Server at localhost:7233
# - Listen on task queue "smb-knowledge-base-v5"
# - Start metrics server at http://localhost:9090
```

### Start Worker in Production

```bash
# Using systemd service
cat > /etc/systemd/system/temporal-worker.service <<EOF
[Unit]
Description=Temporal Worker for SMB Knowledge Base v5
After=network.target

[Service]
Type=simple
User=ml
WorkingDirectory=/home/ml/smb_knowledge_base_v5
ExecStart=/usr/bin/python orchestration/worker.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reexec
sudo systemctl enable temporal-worker
sudo systemctl start temporal-worker
```

## Workflow Execution

### Start Workflow via Client

```bash
# Python CLI
python orchestration/client.py start --url "https://youtube.com/watch?v=45eaVU5NVi8"

# Or programmatically
python -c "
import asyncio
from orchestration.client import TemporalClient

async def main():
    client = TemporalClient()
    await client.connect()
    workflow_id = await client.start_video_processing('https://youtube.com/watch?v=45eaVU5NVi8')
    print(f'Workflow ID: {workflow_id}')

asyncio.run(main())
"
```

### List Workflows

```bash
python orchestration/client.py list

# Output:
# [Running] process-45eaVU5NVi8
# [Completed] process-sh5h0GJzjNk
# [Running] process-Rqmdw4xyIMM
```

### Get Workflow Result

```bash
python orchestration/client.py result --id process-45eaVU5NVi8

# Output:
# {
#   "strategy": {...},
#   "edge_score": 72,
#   "confidence": 0.85,
#   "backtest_metrics": {...},
#   "graph_status": {"status": "stored", "node_id": "strat_123"}
# }
```

### Cancel Workflow

```bash
python orchestration/client.py cancel --id process-45eaVU5NVi8
```

## Monitoring

### Metrics (Prometheus)

```bash
# Access metrics endpoint
curl http://localhost:9090/metrics

# Or add to Prometheus config
cat >> /etc/prometheus/prometheus.yml <<EOF
- job_name: 'temporal'
  static_configs:
    - targets: ['localhost:9090']
EOF

# Restart Prometheus
sudo systemctl restart prometheus
```

### Temporal UI

```bash
# If using Temporal Cloud
# Navigate to https://cloud.temporal.io/namespaces/your-namespace/workflows

# If using local, install temporal UI
docker run -p 8080:8080 temporalio/ui:latest

# Then open http://localhost:8080
```

## Environment Variables

```bash
# Add to ~/.bashrc or Docker environment
export TEMPORAL_NAMESPACE="default"
export TEMPORAL_ADDRESS="localhost:7233"
export TEMPORAL_METRICS_PORT="9090"
```

## Troubleshooting

### Worker Not Starting

```bash
# Check Temporal Server connectivity
telnet localhost 7233

# Check ports in use
lsof -i :7233

# Restart server
docker restart temporal
```

### Workflow Not Completing

```bash
# Check workflow history
python -c "
from temporalio.client import Client
import asyncio

async def main():
    client = await Client.connect('localhost:7233')
    handle = client.get_workflow_handle('process-45eaVU5NVi8')
    history = await handle.fetch_history()
    print(list(history.events))

asyncio.run(main())
"
```

### Connection Timeout

```bash
# Increase client timeout
client = await Client.connect(
    'localhost:7233',
    retry_policy={'initial_interval': '1s', 'maximum_interval': '60s'}
)
```

## Next Steps

1. Complete Task 14 (YouTube Monitor)
2. Complete Task 15 (ClawTeam Integration)
3. Link workflows to YouTube events
4. Set up auto-trigger on new SMB uploads
