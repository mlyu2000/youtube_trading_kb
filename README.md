# SMB Knowledge Base - YouTube Trading Videos

A multi-modal knowledge base system for processing and analyzing SMB Capital YouTube videos.

## Repository Structure

```
youtube_trading_kb/
├── data/                    # Raw and processed data
│   ├── transcripts/         # NotebookLM fulltext transcripts (5 videos)
│   └── knowledge_base/      # Knowledge base exports and reports
│
├── projects/                # Versioned project implementations
│   └── smb_knowledge_base_v5/
│       ├── core/            # Core processing logic
│       ├── ingestion/       # Video ingestion pipeline
│       ├── orchestration/   # Temporal workflow orchestration  
│       ├── graph/           # Graphify-based relationship discovery
│       ├── validation/      # Quality validation & testing
│       ├── skills/          # Hermes agent skills
│       ├── teams/           # ClawTeam organization
│       └── scripts/         # Processing scripts
│
├── README.md               # This file
└── docs/                   # Documentation (to be added)
```

## Architecture

### v5.0 - Multi-Modal Knowledge Base

**Status**: Active Development

**Components**:
- **NotebookLM** - Video transcript extraction with fulltext export
- **Graphify** - Automatic relationship discovery from transcripts
- **ClawTeam/OpenClaw/Hermes** - Multi-agent validation pipeline
- **Temporal** - Optional workflow orchestration

**Removed in v5.0**:
- Neo4j - Relationship storage (replaced by Graphify auto-discovery)
- Qdrant - Vector storage (-graphify handles embeddings)

### Data Flow

```
YouTube Source → NotebookLM Export → Graphify Processing → Knowledge Graph
```

### Key Artifacts

| Artifact | Description |
|----------|-------------|
| `_cQnMSU5yGk.md` | NotebookLM transcript with strategy extraction |
| `smb_pilot_report.md` | Full-text notebook export |
| `smb_final_kb_v3.json` | JSON knowledge base export |

## Setup

### Prerequisites
- Python 3.11+
- uv (Python package manager)
- NotebookLM CLI
- graphify CLI

### Installation

```bash
cd projects/smb_knowledge_base_v5
uv sync
```

## Usage

### Ingest New Video

```bash
cd projects/smb_knowledge_base_v5
python scripts/ingest_video.py <YOUTUBE_URL>
```

### Process Knowledge Base

```bash
# Export from NotebookLM
notebooklm source fulltext <notebook_id> --output data/knowledge_base/

# Process with Graphify
graphify update data/knowledge_base/
```

## Development

### Testing

```bash
cd projects/smb_knowledge_base_v5
pytest test_v5_pilot.py
pytest test_e2e.py
```

### Validation Pipeline

See `validation/` for quality gates and testing frameworks.

## Files

- `data/transcripts/*.md` - Transcript files (5 videos)
- `data/knowledge_base/*.json` - Knowledge base JSON exports
- `projects/smb_knowledge_base_v5/core/` - Processing logic
- `projects/smb_knowledge_base_v5/orchestration/` - Workflow definitions

## Links

- SMB Capital YouTube Channel
- NotebookLM Documentation
- Graphify Documentation

---

**Maintainer**: ml  
**License**: MIT
