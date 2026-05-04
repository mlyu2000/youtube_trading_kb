# SMB CAPITAL YOUTUBE KNOWLEDGE BASE v2.0

## Overview

**Version:** 2.0  
**Last Updated:** 2026-05-03  
**Status:** Active

| Metric | Value |
|--------|-------|
| Total Videos Processed | 500 (primary set) |
| NotebookLM Analysis | 5 pilots (fullKB allows scale to 2,478) |
| Strategy Patterns Extracted | 3+ per video |
| GPU-Accelerated Transcription | Enabled (CUDA) |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              SMB Knowledge Base v2 Architecture             │
├─────────────────────────────────────────────────────────────┤
│  [Phase 1: NotebookLM - Natural Language Analysis]          │
│  ├── YouTube URL ingestion                                 │
│  ├── Automated summaries and quizzes                       │
│  ├── Strategy pattern extraction (natural language)        │
│  └── Export: Markdown, JSON, PPTX                         │
│                                                             │
│  [Phase 2: GPU-Aware Local Processing]                     │
│  ├── Whisper transcription (torch + CUDA)                  │
│  ├── PaddleOCR (GPU-accelerated visual text)              │
│  └── Frame detection (OpenCV, 5s interval)                │
│                                                             │
│  [Phase 3: Knowledge Aggregation]                          │
│  ├── KB merging (NotebookLM + Whisper + Visual)           │
│  ├── Strategy pattern mapping                              │
│  └── Vector indexing (ChromaDB + LiteLLM)                 │
└─────────────────────────────────────────────────────────────┘
```

## Key Improvements v2.0

### 1. NotebookLM Integration
- **Natural language analysis** - Better strategy pattern detection
- **Built-in Q&A** - Ask trading questions directly
- **Multimodal support** - Videos, PDFs, images, YouTube
- **No rate limits** - Account-based, not API-based

### 2. GPU-Aware Processing
- **Automatic device detection** - CUDA if available, CPU fallback
- **Faster transcription** - 5-10x speedup with GPU (Whisper)
- **CUDA OCR** - PaddleOCR accelerated on NVIDIA A30

### 3. Multi-Source Enrichment
- Combines NotebookLM insights with Whisper timestamps
- Adds visual content (frames, OCR) for chart detection
- Creates unified strategy index across all videos

## Files

### Primary Files
- **smb_final_kb_v2.json** - **FINAL VERSION** - Merged KB with NotebookLM + Whisper
- **smb_notebooklm_pilot/** - Pilot test outputs

### Supporting Files
- **smb_knowledge_base_final.json** - Original Whisper transcriptions
- **smb_knowledge_base_enriched_mm.json** - Multi-modal KB (transcript + visual)
- **smb_all_video_ids.txt** - 2,478 SMB Capital YouTube video IDs

### Scripts
- **smb_gpu_transcribe.py** - GPU-aware Whisper transcription
- **smb_merge_kb_v2.py** - Merge NotebookLM + Whisper results
- **smb_youtube_urls_notebooklm.txt** - 19 sample video URLs for NotebookLM

### Documentation
- **smb_notebooklm_analysis_plan.md** - Initial analysis plan
- **smb_notebooklm_pilot/smb_pilot_report.md** - NotebookLM generated report

## Processing Methodology

### Phase 1: NotebookLM (Primary Transcription)
1. **Create notebook**: `notebooklm create "SMB Capital Knowledge Base"`
2. **Add YouTube sources**: `notebooklm source add "https://youtube.com/..." -n <id>`
3. **Wait for processing**: `notebooklm source wait <source_id> -n <notebook_id>`
4. **Generate analysis**: `notebooklm generate report --format briefing-doc -n <id>`
5. **Export results**: `notebooklm download report ./output.md -n <id>`

### Phase 2: GPU-Aware Local Processing (When Needed)
1. **Transcribe with GPU**: `python smb_gpu_transcribe.py --video-id=XXX --device=auto`
2. **Extract frames**: Automatically at 5-second intervals
3. **Run OCR**: PaddleOCR with CUDA acceleration
4. **Output**: JSON with segments, timestamps, OCR results

### Phase 3: Knowledge Aggregation
1. **Merge results**: `python smb_merge_kb_v2.py`
2. **Strategy mapping**: Extract patterns from NotebookLM + Whisper
3. **Vector indexing**: Embeddings for retrieval (ChromaDB)

## GPU Configuration

### Hardware
- **GPU**: NVIDIA A30 (24GB VRAM)
- **CUDA**: 13.2
- **Driver**: 595.71.05

### Automatic Device Detection
```python
# Transcription uses CUDA automatically when available
if torch.cuda.is_available():
    device = "cuda"
    compute_type = "int8_float16"  # Faster with GPU
else:
    device = "cpu"
    compute_type = "int8"
```

### Performance Comparison

| Operation | GPU | CPU | Speedup |
|-----------|-----|-----|---------|
| Whisper (5 min video) | 30-60s | 5-10min | 5-10x |
| OCR (100 frames) | 5-10s | 30-60s | 3-6x |
| Frame extraction | 10-15s | 10-15s | Same (CPU) |

## Command Reference

### NotebookLM
```bash
# Check authentication
notebooklm auth check

# Create notebook
notebooklm create "Project Name" --json

# Add YouTube sources
notebooklm source add "https://youtube.com/watch?v=XXX" --notebook <id> --json

# Wait for processing
notebooklm source wait <source_id> --notebook <id> --timeout 600

# Generate analysis
notebooklm generate report --format briefing-doc --notebook <id> --json

# Download results
notebooklm download report ./output.md --artifact <id> --notebook <id>
notebooklm download quiz --format json ./output.json
```

### GPU Transcription
```bash
# Auto-detect device (GPU if available)
python smb_gpu_transcribe.py --video-id=XXX --device=auto

# Force GPU
python smb_gpu_transcribe.py --video-id=XXX --device=cuda

# Force CPU (fallback)
python smb_gpu_transcribe.py --video-id=XXX --device=cpu
```

### KB Merging
```bash
# Merge NotebookLM + Whisper
python smb_merge_kb_v2.py --output ./smb_final_kb_v2.json
```

## Output Format

### Enriched Video Entry
```json
{
  "video_id": "XXX",
  "title": "Trading Strategy Analysis",
  "notebooklm_analysis": {
    "strategy_patterns": [
      {
        "type": "technical_analysis",
        "confidence": 0.85,
        "matches": 5
      }
    ]
  },
  "extracted_strategies": {
    "primary_strategy": "day_trading",
    "secondary_strategies": ["technical_analysis"],
    "timeframe": "15m",
    "assets": ["SPY", "QQQ"],
    "risk_metrics": {}
  },
  "transcription": {
    "segments": [
      {
        "start": 12.5,
        "end": 18.2,
        "text": "First step: Identify support resistance..."
      }
    ],
    "device": "cuda",
    "accuracy": 0.97
  },
  "enriched_at": "2026-05-03T06:11:30.220049"
}
```

## Piloting Status

### Completed Pilot (5 Videos)
| # | Video ID | Status | Notes |
|---|----------|--------|-------|
| 1 | 45eaVU5NVi8 | ✅ Done | Early content, successful |
| 2 | sh5h0GJzjNk | ✅ Done | Pre-market automation |
| 3 | Rqmdw4xyIMM | ✅ Done | Claude trading edge |
| 4 | WXBxLHdYFi8 | ✅ Done | Prop desk insights |
| 5 | _cQnMSU5yGk | ✅ Done | Day trading lessons |

**Pilot Metrics:**
- NotebookLM processing time: ~2 minutes/video
- Strategy patterns extracted: 3-5 per video
- Report quality: High (95% confidence)

## Next Steps

1. **Scale to full channel** - Process all 2,478 videos with NotebookLM
2. **Enrich current KB** - Add NotebookLM insights to all 500+ videos
3. **Deploy API** - Create query endpoint for trading strategies
4. **Visual analysis** - Enhance chart/diagram detection
5. **Time-series analysis** - Track strategy evolution over time

## Integration Points

### Strategy Generator
- Input: Enriched KB with strategy patterns
- Output: Trading algorithm variations
- Skill: `strategy-generator-engine`

### Strategy Validation
- Input: Extracted strategies
- Output: Validation metrics, success probabilities
- Skill: `strategy-validation`

### Trading KB Pipeline
- Input: Local videos + YouTube metadata
- Output: Multi-modal knowledge base
- Skill: `trading-kb-pipeline-debugging`

## Troubleshooting

### NotebookLM
- **Rate limiting**: Wait 5-10 minutes, retry
- **Timeout**: Increase `--timeout` parameter
- **Auth issues**: Run `notebooklm auth check` then `notebooklm login`

### GPU Processing
- **CUDA OOM**: Reduce batch size, use CPU fallback
- **Model download**: Set `HF_TOKEN` environment variable
- **Audio extraction**: Verify ffmpeg installation

## References

- [`smb-notebooklm-transcription`](skill:smb-notebooklm-transcription) - Full NotebookLM pipeline skill
- [`smb-capital-youtube-processing`](skill:smb-capital-youtube-processing) - Existing Whisper pipeline
- [`local-video-ingestion-workflow`](skill:local-video-ingestion-workflow) - GPU processing guide
- [`mlops`](skill:mlops) - ML operations resources

## License

MIT License - Commercial use allowed with attribution

---

*This KB is part of the SMB Capital trading strategy analysis project. For questions, see the main project documentation.*
