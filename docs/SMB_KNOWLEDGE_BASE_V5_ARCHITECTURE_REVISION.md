# SMB Capital YouTube Knowledge Base - Revised Architecture Flow v5.0

**Version:** 5.0  |  **Date:** 2026-05-03  |  **Author:** Hermes Agent  |  **Status:** Draft for v5.0 revision

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Revision Overview](#architecture-revision-overview)
3. [Revised Data Flow](#revised-data-flow)
4. [NotebookLM Integration Flow](#notebooklm-integration-flow)
5. [Temporal Orchestration Layer](#temporal-orchestration-layer)
6. [Multi-Store Architecture](#multi-store-architecture)
7. [Strategy Extraction Pipeline](#strategy-extraction-pipeline)
8. [Validation & Backtesting Integration](#validation--backtesting-integration)
9. [Scalability & Batch Processing](#scalability--batch-processing)
10. [Conclusion](#conclusion)

---

## Executive Summary

The SMB Capital YouTube Knowledge Base v5.0 introduces a **complete architectural revision** centered on:

### Core Changes

| Component | v3.0 | v4.0 | v5.0 |
|-----------|------|------|------|
| **Transcription** | Whisper (local) | Whisper (local) | **NotebookLM (cloud)** |
| **Strategy Extraction** | Local scripts | Pydantic v2 + structured schema | **Temporal workflows + ClawTeam** |
| **Storage** | Single JSON | Neo4j + Qdrant | **PostgreSQL + Neo4j + Qdrant** |
| **Orchestration** | Serial scripts | Manual workflow | **Automated Temporal workflows** |
| **Validation** | Manual QA | Auto-validation agent | **LLM-as-Judge + self-critique loop** |

### New Capabilities

1. **NotebookLM-driven Transcription** - Cloud-native transcript generation with visual context
2. **Multi-Agent Strategy Extraction** - ClawTeam swarm orchestrates extraction, validation, and enrichment
3. **Multi-Store Persistence** - Relational (PostgreSQL) + Graph (Neo4j) + Vector (Qdrant) stores
4. **Automated Validation Loop** - LLM self-critique ensures quality before storage
5. **Backtesting Integration** - Strategy to TradingAlgorithm to Backtest pipeline

---

## Architecture Revision Overview

### Why Revision?

The v3.0 to v4.0 pipeline had critical limitations:

| Problem | Impact | v5.0 Solution |
|---------|--------|---------------|
| **Transcription quality** | Whisper misses visual context | NotebookLM understands video context (charts + speech) |
| **Extraction consistency** | Local scripts -> inconsistent outputs | ClawTeam agents enforce standardized schema |
| **Storage fragmentation** | Multiple isolated stores | Unified multi-store architecture |
| **Validation manual** | QA bottleneck | Automated LLM-as-Judge validation |
| **Scalability linear** | Serial processing | Temporal concurrency + batch mode |

---

## Revised Data Flow

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                     SMB Knowledge Base v5.0 Architecture                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                    PHASE 1: NotebookLM Transcription (NEW)                     │  │
│  │  1. Reuse shared notebook (ID: 3227d0dc-d155-4bf2-8091-e169e75f4e88)         │  │
│  │  2. DELETE ALL existing sources (clean reuse)                                │  │
│  │  3. ADD NEW batch (5-50 videos)                                              │  │
│  │  4. WAIT for processing (1-2 min per video)                                  │  │
│  │  5. EXTRACT transcripts + visual context via -s <source_id>                  │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                      v                                               │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │              PHASE 2: Temporal Orchestration (NEW)                            │  │
│  │  Workflows (5 concurrent per pilot batch):                                    │  │
│  │    - extract_strategy                                                          │  │
│  │    - validate_strategy                                                         │  │
│  │    - enrich_with_knowledge_graph                                              │  │
│  │    - store_to_multi_store                                                      │  │
│  │    - self_improvement                                                          │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                      v                                               │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                     PHASE 3: Multi-Store Persistence (v4.0)                   │  │
│  │  PostgreSQL (relational) + Neo4j (graph) + Qdrant (vector)                   │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## NotebookLM Integration Flow

### Clean Reuse Strategy (v5.0 Key Innovation)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    NotebookLM Clean Reuse Workflow                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  1. LOAD notebook_id from state file (3227d0dc-d155-4bf2-8091-e169e75f4e88)       │
│                                                                                      │
│  2. DELETE ALL Sources                                                              │
│     notebooklm source list -n <nb_id>                                               │
│     for each source_id: notebooklm source delete <id> -n <nb_id> -y                │
│      - Result: 0 sources (clean slate)                                             │
│                                                                                      │
│  3. ADD NEW BATCH                                                                   │
│     notebooklm source add "https://youtube.com/watch?v=XXX" -n <nb_id> --json      │
│      - Returns: {"source_id": "...", "title": "SMB Video XXX", "status": "..." } │
│      - Maps: {"45eaVU5NVi8": "545580db-d18a-4971-b317-58924d11219e", ...}        │
│                                                                                      │
│  4. WAIT FOR PROCESSING                                                             │
│     for each source_id: notebooklm source wait <id> -n <nb_id>                     │
│      - Status: "READY" (transcript + visual context available)                     │
│                                                                                      │
│  5. EXTRACT WITH -s SOURCE_ID                                                       │
│     notebooklm ask "<prompt>" -n <nb_id> -s <src_id> --json                        │
│      - Guarantees: Context ONLY from specific video, not others in notebook        │
│      - Extracts: entry_conditions, exit_conditions, risk_parameters, ...           │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Temporal Orchestration Layer

### Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    Temporal Workflow Diagram                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Workflow: ProcessVideo (video_id={id})                                            │
│     v                                                                                │
│     - Activity: extract_strategy(video_id, notebook_id, source_id)               │
│     │     - Returns: raw_strategy (JSON, Pydantic v2 compatible)                  │
│     │                                                                                │
│     - Activity: validate_strategy(raw_strategy)                                   │
│     │     - Returns: validated_strategy (confidence >= 0.75, edge_score >= 65)    │
│     │                                                                                │
│     - Activity: enrich_with_knowledge_graph(validated_strategy)                   │
│     │     - Returns: enriched_strategy (with Neo4j node IDs)                      │
│     │                                                                                │
│     - Activity: store_to_multi_store(enriched_strategy)                           │
│     │     - PostgreSQL: strategy metadata + regime metrics                        │
│     │     - Neo4j: strategy graph (entry/exit patterns)                           │
│     │     - Qdrant: vector embeddings (for similarity search)                     │
│     │                                                                                │
│     - Activity: self_improvement(enriched_strategy)                               │
│     │     - Returns: DSPy prompt improvement suggestions                          │
│     │                                                                                │
│     - complete: workflow_id="process-{video_id}"                                 │
│                                                                                      │
│  Concurrent Execution (5 pilots):                                                    │
│    - process-45eaVU5NVi8  (notebook_id=3227d0dc...)                                │
│    - process-sh5h0GJzjNk  (notebook_id=3227d0dc...)                                │
│    - process-Rqmdw4xyIMM  (notebook_id=3227d0dc...)                                │
│    - process-WXBxLHdYFi8  (notebook_id=3227d0dc...)                                │
│    - process-_cQnMSU5yGk  (notebook_id=3227d0dc...)                                │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Multi-Store Architecture

### Store Responsibilities

| Store | Purpose | Data Model | Schema |
|-------|---------|------------|--------|
| **PostgreSQL** | Strategy metadata + regime metrics | Relational tables | Pydantic v2 to SQL |
| **Neo4j** | Strategy graph (entry/exit patterns) | Graph nodes + relationships | ENUM patterns |
| **Qdrant** | Vector embeddings | Dense vectors + payloads | Embedding service |

---

## Strategy Extraction Pipeline

### Complete v5.0 Pipeline

```
YouTube Video (45eaVU5NVi8)
     v
     - NotebookLM: source add - source_id="545580db..."
     v
     - NotebookLM: wait for READY status
     v
     - Temporal Workflow: ProcessVideo
           v
           - Activity: extract_strategy
           │     - notebooklm ask "..." -n <nb_id> -s <src_id> --json
           │     - Returns: raw_strategy (missing some fields)
           v
           - Activity: validate_strategy
                 - LLM-as-Judge: "Does this meet quality gates?"
                 - quality gates: confidence >= 0.75, edge_score >= 65, p<0.05
                 - Returns: validated_strategy or rejected
           v
           - Activity: enrich_with_knowledge_graph
                 - Neo4j: Create/merge Strategy node + relationships
                 - Returns: enriched_strategy (with Neo4j node_id)
           v
           - Activity: store_to_multi_store
                 - PostgreSQL: INSERT INTO strategies (...)
                 - Neo4j: MERGE (s:Strategy {id: ...})
                 - Qdrant: upsert vectors + payloads
           v
           - Activity: self_improvement
                 - DSPy: "Why did extraction fail? Improve prompt."
                 - Returns: prompt_suggestion
     v
     - Workflow Complete: workflow_id="process-45eaVU5NVi8"
```

---

## Conclusion

### v5.0 Capabilities Summary

| Capability | v3.0 | v4.0 | v5.0 |
|------------|------|------|------|
| NotebookLM transcription | No | No | Yes |
| Clean reuse strategy | No | No | Yes |
| Temporal orchestration | No | No | Yes |
| Multi-store persistence | No | Partial | Yes |
| Multi-agent extraction | No | No | Yes |
| LLM-as-Judge validation | No | Partial | Yes |
| Backtesting integration | No | No | Yes |
| DSPy self-improvement | No | No | Yes |

---

**Document Status:** Draft v5.0 Architecture  |  **Implementation:** In Progress  
**Target Release:** 2026-05-05
