# SMB Capital YouTube Knowledge Base v4.0 - Design & Architecture

**Version:** 4.0  
**Date:** 2026-05-03  
**Author:** Hermes Agent  
**Status:** In Development  
**Migration Path:** v3.0 (Implemented) → v4.0 (Future State)

---

## Executive Summary

**SMB Knowledge Base v4.0** transforms from a content indexing system into an **Edge-Driven Trading Knowledge Platform**.

### New Capabilities

| Capability | v3.0 | v4.0 |
|------------|------|------|
| Data Model | Free-text JSON | **Structured Pydantic models** |
| Storage | Single JSON file | **Multi-store: PostgreSQL + Neo4j + Qdrant** |
| Strategy Extraction | Natural language | **Structured output + LLM-as-Judge** |
| Chart Analysis | OCR + keyword matching | **Reconstruction + OHLCV alignment** |
| Strategy Validation | Manual review | **Auto backtesting + Edge scoring** |
| Query Interface | File-based | **REST API + Web Dashboard** |

### v4.0 Vision

> **"From Knowledge to Edge"** - We don't just catalog what traders say; we extract, validate, and score their actual trading edge.

---

## Core Principles

### 1. Structured First

All strategy data must conform to a rigorously defined Pydantic schema. Free text from NotebookLM is parsed, not stored.

### 2. Multi-Store Architecture

| Store | Purpose | Technology |
|-------|---------|------------|
| **PostgreSQL** | Metadata, video info, provenance | PostgreSQL 16 |
| **Neo4j** | Knowledge graph (strategies → evidence) | Neo4j 5.24 |
| **Qdrant** | Vector search (similar setups, regimes) | Qdrant 1.11 |

### 3. Edge-Centric Validation

Every strategy gets scored on: statistical significance, regime robustness, edge consistency.

### 4. Visual Reconstruction

Rather than extracting text from charts, we **reconstruct** OHLCV data using VLMs.

---

## System Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       SMB Knowledge Base v4.0                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                PHASE 1: Structured Extraction (v4)                 │     │
│  │  1. Load NotebookLM analysis                                       │     │
│  │  2. Parse natural language into Pydantic TradingStrategy model    │     │
│  │  3. Self-critique loop (confidence ≥ 0.75)                        │     │
│  │  4. Dual-mode: NotebookLM + Claude-3.5-Sonnet fallback            │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                              ↓                                                │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │        PHASE 2: Knowledge Graph Population (v4)                    │     │
│  │  1. Create Neo4j nodes (Trader, Strategy, Setup, Indicator, ...)  │     │
│  │  2. Add edges (Strategy → Evidence, Setup → Indicator, ...)       │     │
│  │  3. Generate embeddings for vector search                         │     │
│  │  4. Store provenance in PostgreSQL                                │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                              ↓                                                │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │            PHASE 3: Visual Intelligence (v4)                       │     │
│  │  1. Content-aware keyframe extraction (not fixed intervals)       │     │
│  │  2. YOLOv8 chart vs indicator classification                      │     │
│  │  3. Qwen2-VL-7B or Claude-3.5-Sonnet vision for reconstruction    │     │
│  │  4. OHLCV reconstruction aligned to Kairos timestamps              │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                              ↓                                                │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │          PHASE 4: Backtesting & Edge Scoring (v4)                  │     │
│  │  1. Auto-generate backtests from TradingStrategy                  │     │
│  │  2. Run with vectorbt (regime detection, regime-specific metrics) │     │
│  │  3. Monte Carlo significance testing                              │     │
│  │  4. Compute edge score (0-100)                                    │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                              ↓                                                │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │           PHASE 5: Validator Agent (v4)                            │     │
│  │  1. LLM-as-Judge cross-validation                                 │     │
│  │  2. Discrepancy flagging between rules and reconstructed chart    │     │
│  │  3. Auto-correction suggestions                                   │     │
│  │  4. Final validated strategy with edge score                      │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                              ↓                                                │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │              PHASE 6: Query & Dashboard Layer (v4)                 │     │
│  │  1. FastAPI endpoints (/strategies, /by_edge, /graph/query)       │     │
│  │  2. Streamlit dashboard for exploration                           │     │
│  │  3. Vector search for similar strategies                          │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Data Models (Pydantic v2)

### File: `core/smb_schema_v4.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MarketRegime(str, Enum):
    TRENDED_BULL = "trended_bull"
    TRENDED_BEAR = "trended_bear"
    CONSOLIDATION = "consolidation"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    GAP_UP = "gap_up"
    GAP_DOWN = "gap_down"

class RiskModel(BaseModel):
    position_size_percent: float = Field(..., ge=0.0, le=100.0)
    stop_loss_type: str
    stop_loss_value: float
    take_profit_type: str
    take_profit_value: float
    max_drawdown_acceptable: float
    risk_per_trade_percent: float

class Rule(BaseModel):
    description: str
    type: str  # "entry", "exit", "filter", "risk"
    condition: str
    confidence: float = Field(..., ge=0.0, le=1.0)

class SetupPattern(BaseModel):
    name: str
    description: str
    chart_pattern: str
    confirmation_signals: List[str]
    common_timeframes: List[str]

class BacktestResult(BaseModel):
    total_trades: int
    win_rate: float
    profit_factor: float
    max_drawdown: float
    Sharpe_ratio: float
    Sortino_ratio: float
    total_pnl: float
    average_risk_reward: float
    regime_specific_metrics: Dict[MarketRegime, Dict[str, float]]
    statistical_significance: float  # Monte Carlo p-value

class EvidenceRef(BaseModel):
    video_id: str
    timestamp_start: float
    timestamp_end: float
    confidence: float
    context_snippet: str

class TradingStrategy(BaseModel):
    """Primary data model for v4.0 - fully structured and validated"""
    strategy_id: str = Field(alias="id")
    name: str
    description: str
    trading_style: str
    primary_regime: MarketRegime
    secondary_regimes: List[MarketRegime]
    timeframes: List[str]
    assets: List[str]
    risk_model: RiskModel
    entry_rules: List[Rule]
    exit_rules: List[Rule]
    filter_rules: List[Rule]
    setup_patterns: List[SetupPattern]
    indicators_used: List[str]
    backtest_results: BacktestResult
    evidence_refs: List[EvidenceRef]
    confidence: float = Field(..., ge=0.0, le=1.0)
    edge_score: int = Field(..., ge=0, le=100)
    validation_status: str  # "unverified", "validated", "flagged"
    created_at: datetime
    last_updated: datetime
```

### Success Criterion

```python
# Test
sample_data = {...}  # From v3 JSON conversion
strategy = TradingStrategy.model_validate(sample_data)
assert isinstance(strategy, TradingStrategy)
assert strategy.edge_score >= 0 and strategy.edge_score <= 100
print(strategy.model_dump_json(indent=2))  # JSON serialization
```

---

## Project Directory Structure

### File: `/home/ml/smb_knowledge_base_v4/`

```
smb_knowledge_base_v4/
├── core/
│   ├── smb_schema_v4.py        # Pydantic models (Task 1)
│   └── database.py             # Multistore connections (Task 3)
├── ingestion/
│   ├── structured_extractor.py # Dual-mode extraction (Task 5)
│   └── prompts/                # Prompt templates (Task 4)
│       ├── structured_strategy_prompt.txt
│       ├── hierarchy_level1_philosophy.txt
│       ├── hierarchy_level2_methodology.txt
│       ├── hierarchy_level3_tactical.txt
│       └── self_critique_prompt.txt
├── visual/
│   ├── chart_classifier.py     # YOLOv8 chart detection (Task 8)
│   └── chart_reconstructor.py  # VLM reconstruction (Task 8)
├── graph/
│   ├── knowledge_graph_builder.py  # Neo4j population (Task 6)
│   └── cypher_queries.py       # Reusable queries
├── migration/
│   └── migrate_v3_to_v4.py     # Legacy data migration (Task 7)
├── validation/
│   ├── backtest_engine.py      # vectorbt integration (Task 9)
│   ├── edge_scorer.py          # Edge scoring logic (Task 9)
│   └── validator_agent.py      # LLM-as-Judge (Task 10)
├── api/
│   └── main.py                 # FastAPI endpoints (Task 11)
├── dashboard/
│   └── app.py                  # Streamlit UI (Task 11)
├── orchestration/
│   └── pipeline_v4.py          # End-to-end pipeline (Task 12)
├── requirements_v4.txt         # Dependencies (Task 2)
├── output/
│   └── strategies/             # Generated strategies
├── data/
│   ├── processed/              # Intermediate results
│   └── raw/                    # Original videos (reference)
└── logs/
    └── pipeline_v4.log
```

---

## Dependencies (`requirements_v4.txt`)

```
# Core library
pydantic>=2.7.0
pydantic-settings>=2.2.0

# Database
neo4j>=5.24.0
asyncpg>=0.29.0
qdrant-client>=1.11.0
sqlmodel>=0.0.19  # PostgreSQL
langchain>=0.2.0

# AI/ML
openai>=1.35.0
cloud vegetation>=0.0.1  # Grok API client (if applicable)
langchain-openai>=0.2.0
langchain Anthropic>=0.2.0

# Computer Vision
opencv-python>=4.9.0
ultralytics>=8.2.0  # YOLOv8
langchain-community>=0.2.0  # VLM wrappers

# Backtesting
vectorbt>=0.23.0
numpy>=1.26.0
pandas>=2.2.0

# Web Framework
fastapi>=0.115.0
streamlit>=1.36.0
uvicorn>=0.32.0

# Utilities
python-dotenv>=1.0.1
tqdm>=4.66.0
loguru>=0.7.2
```

---

## Core Components Breakdown

### Task 1: Core Data Models

**File:** `core/smb_schema_v4.py`

**Key Features:**
- 6 Pydantic v2 models with Field constraints
- Enum for MarketRegime (7 regimes)
- Nested models: RiskModel, BacktestResult, SetupPattern
- Proper field aliases for JSON serialization

### Task 2: Directory Structure

**(file creation in progress...)**

---

## Schema Design Rationale

### Why Pydantic v2?

| Feature | v1 | v2 |
|---------|----|----|
| Performance | Good | **2x faster** |
| JSON Schema | Manual | **Automatic** |
| Validation | Manual | **Automatic** |
| Serialization | Manual | **model_dump()** |
| **Model validation** | `validate()` | **`model_validate()`** |

### Why Multi-Store?

| Store | Why Not FS? | Why Not Single DB? |
|-------|-------------|-------------------|
| **PostgreSQL** | ❌ Unstructured | ✅ Metadata relationships |
| **Neo4j** | ❌ Graph queries slow | ✅ Native graph traversals |
| **Qdrant** | ❌ Vector search weak | ✅ High-performance ANN |

---

## Migration Strategy: v3 → v4

### Mapping v3 JSON to v4 Schema

| v3 Field | v4 Field | Transformation |
|----------|----------|----------------|
| `video_id` | `evidence_refs[].video_id` | Extracted to evidence |
| `transcription.segments` | `evidence_refs[].context_snippet` | Parse and map |
| `notebooklm_analysis.strategy_patterns` | `TradingStrategy.*_rules` | Parse and validate |
| `extracted_strategies.primary_strategy` | `TradingStrategy.trading_style` | Direct mapping |
| N/A | `TradingStrategy.edge_score` | **Generated** (Task 9) |
| N/A | `TradingStrategy.backtest_results` | **Generated** (Task 9) |

---

## Validation Gate

### Quality Thresholds

| Component | Threshold |
|-----------|-----------|
| NotebookLM confidence | ≥ 0.75 |
| Validation confidence | ≥ 0.80 |
| Edge score | ≥ 65 |
| Backtest trades | ≥ 20 |
| Statistical significance | p < 0.05 |

### Validation Levels

```
Unverified (0) → Validated (85) → Production-Ready (90)
     ↓              ↓                   ↓
   <0.75          ≥0.80              ≥0.90
```

---

## Success Criteria Summary

| Task | Deliverable | Success Criterion |
|------|-------------|-------------------|
| 1 | `core/smb_schema_v4.py` | `TradingStrategy.model_validate()` works |
| 2 | Directory structure | All 7 folders created |
| 3 | `core/database.py` | Health checks for all 3 stores |
| 4 | `prompt/` library | 5 prompt files created |
| 5 | `ingestion/structured_extractor.py` | ∀ videos → valid TradingStrategy |
| 6 | `graph/knowledge_graph_builder.py` | Query relationships correctly |
| 7 | `migration/migrate_v3_to_v4.py` | Legacy data populated |
| 8 | `visual/chart_reconstructor.py` | ≥85% OHLCV accuracy |
| 9 | `validation/backtest_engine.py` | Complete BacktestResult with edge score |
| 10 | `validation/validator_agent.py` | End-to-end validated strategies |
| 11 | `api/main.py` + `dashboard/app.py` | Dashboard displays top strategies |
| 12 | `orchestration/pipeline_v4.py` | Single command end-to-end run |

---

## Next Steps

1. ✅ Create v4.0 design document → **In progress**
2. ⏳ Create directory structure (`/home/ml/smb_knowledge_base_v4/`)
3. ⏳ Implement core Pydantic models
4. ⏳ Set up database connections
5. ⏳ Implement structured extractor
6. ⏳ Build knowledge graph builder
7. ⏳ Implement visual reconstruction
8. ⏳ Create backtesting engine
9. ⏳ Build validator agent
10. ⏳ Develop web API + dashboard
11. ⏳ Create pipeline orchestrator

---

**Document Status:** 📋 Design Complete  
**Implementation Status:** 🚧 In Progress  
**Target Release:** v4.0 Alpha Q2 2026
