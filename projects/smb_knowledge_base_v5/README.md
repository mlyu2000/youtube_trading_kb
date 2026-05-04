# SMB Knowledge Base - YouTube Trading Strategy Extraction

**Transforming SMB Capital YouTube videos into structured, actionable trading strategies using multi-version AI pipeline.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Temporal](https://img.shields.io/badge/Temporal-Orchestration-green.svg)](https://temporal.io)

---

## Overview

The SMB Knowledge Base extracts, validates, and stores trading strategies from SMB Capital YouTube videos. The project uses a **multi-version architecture** (v3 → v4 → v5) with progressive improvements:

| Version | Core Technology | Data Model | Orchestration |
|---------|-----------------|------------|---------------|
| v3.0 | Python scripts | Free-text JSON | Sequential |
| v4.0 | Pydantic v2 | Structured models | Sequential |
| v5.0 | Temporal.io | Graph + Vector | Distributed workflows |

---

## Architecture

### v4.0 Core Architecture

```yaml
YouTube URL 
    ↓
NotebookLM (Transcription)
    ↓
LLM Extraction
    ↓
v4 Schema (Pydantic)
    ↓
Neo4j + Qdrant
```

### v5.0 Distributed Architecture

```yaml
YouTube Monitor
    ↓
Temporal Client
    ↓
Temporal Workflows
    ↓
ClawTeam Swarm
    ↓
Observability (Prometheus + Grafana)
```

---

## Components

### Core Modules (v4.0)

| Module | Purpose |
|--------|---------|
| `core/smb_schema_v4.py` | Pydantic v2 data models |
| `ingestion/structured_extractor.py` | LLM-based strategy extraction |
| `validation/validator_agent.py` | Backtesting and validation |
| `graph/knowledge_graph_builder.py` | Neo4j graph storage |
| `dashboard/` | Streamlit/FastAPI visualizations |

### Orchestration (v5.0)

| Module | Purpose |
|--------|---------|
| `orchestration/workflows.py` | Temporal workflow definitions |
| `orchestration/activities.py` | NotebookLM transcription activities |
| `orchestration/worker.py` | Temporal worker configuration |
| `ingestion/youtube_monitor.py` | YouTube channel monitoring |

---

## Quick Start

### Prerequisites

- Python 3.11+
- NVIDIA GPU (A10/A30 or similar, 24GB VRAM)
- PostgreSQL 15+
- Neo4j 5+
- Temporal Server (optional, v5.0)

### v4.0 Setup

```bash
cd ~/smb_knowledge_base_v4
pip install -r requirements_v4.txt
python test_v4_pipeline.py
```

### v5.0 Setup

```bash
# Start Temporal server
docker run -p 7233:7233 temporalio/auto-setup:latest

cd ~/smb_knowledge_base_v5
pip install -r requirements_v5.txt
python test_v5_pilot.py
```

---

## Quality Thresholds

| Metric | v4.0 Minimum | Production | Status |
|--------|-------------|------------|--------|
| Edge Score | 65 | 75 | ✅ Passing |
| Confidence | 0.75 | 0.85 | ✅ Passing |
| p-value | < 0.05 | < 0.01 | ⚠️ Needs improvement |
| Profit Factor | 1.3 | 1.5 | ⚠️ Needs improvement |

---

## Migration Path

### v3 → v4
- Free-text JSON → Pydantic v2 structured models
- Backward compatible output schema
- Neo4j + Qdrant graph storage

### v4 → v5
- Sequential scripts → Temporal distributed workflows
- Single-agent extraction → Multi-agent ClawTeam swarm
- Local backtesting → Distributed orchestration

---

## Development

### Running Tests

```bash
# v4.0 pipeline tests
cd ~/smb_knowledge_base_v4
python test_v4_pipeline.py

# v5.0 workflow tests
cd ~/smb_knowledge_base_v5
python test_v5_pilot.py
```

---

## License

MIT License - See LICENSE file for details.

---

*Last updated: 2026-05-03*
