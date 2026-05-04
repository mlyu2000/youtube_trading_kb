# SMB Knowledge Base v5.0

Current Phase: **v5.0 - Temporal Orchestration + NotebookLM Transcription**

## What's Here

This repository contains **Phase 2 (in development)** of the SMB Knowledge Base:

- **Phase 1**: NotebookLM transcription ✅
- **Phase 2**: Temporal orchestration 🔄 (this project)
  - YouTube monitor + temporal client
  - Multi-agent ClawTeam swarm integration
  - Schema-compliant strategy validation

## What's Not Here

Phase 3, 4, 5 have been moved to a separate project:
- `/home/ml/smb_knowledge_base_phases_3_4_5/`

## Project Structure

```
smb_knowledge_base_v5/
├── ingestion/         # YouTube monitor, note
├── utils/             #辅助工具
├── graph/             # Neo4j integration
├── scripts/           # Automation scripts
├── validation/        # Schema validation (no backtesting)
├── orchestration/     # Temporal workflows & client
└── teams/             # ClawTeam agent configurations
```

## Quick Start

See: `INGESTION_README.md` for YouTube monitoring setup.

## Development Status

- ✅ Project structure
- 🔜 Phase 2: Temporal orchestration
- 📝 Phase 3+: See `/home/ml/smb_knowledge_base_phases_3_4_5/`

## License

Private project - personal use only
