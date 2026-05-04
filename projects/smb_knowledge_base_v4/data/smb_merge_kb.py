#!/usr/bin/env python3
"""
Merge NotebookLM and Whisper Results for SMB Knowledge Base

Combines NotebookLM's natural language understanding with Whisper's
exact timestamp alignment for comprehensive trading knowledge base.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def load_json_file(filepath: Path) -> dict:
    """Load JSON file with error handling."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        print(f"Error loading {filepath}: {e}")
        return {}


def extract_notebooklm_insights(notebooklm_report: dict) -> dict:
    """Extract strategy insights from NotebookLM report."""
    insights = {
        "strategy_patterns": [],
        "risk_management": [],
        "entry_exit_signals": [],
        "assets_mentioned": [],
        "timeframes_mentioned": []
    }
    
    report_content = notebooklm_report.get("content", "")
    
    # Extract patterns (basic keyword search)
    pattern_keywords = {
        "technical_analysis": ["support", "resistance", "breakout", "consolidation", "trend", "chart"],
        "price_action": ["candle", "pattern", "candlestick", "reversal", "continuation"],
        "momentum": ["RSI", "MACD", "stochastic", "indicator", "divergence"],
        "volume": ["volume", "volume spike", "liquidity", "drawing", "flow"],
        "multi timeframe": ["higher timeframe", "lower timeframe", "timeframe", "alignment"],
        "risk management": ["risk", "position size", "stop loss", "take profit", "R-multiple"],
        "market structure": ["bullish", "bearish", "rection", "range", "breakout"],
        "gaps": ["gap", "fill", "react", "trigger"],
        "support_resistance": ["support", "resistance", "horizontal", "trendline", "S/R"]
    }
    
    content_lower = report_content.lower()
    
    for pattern_type, keywords in pattern_keywords.items():
        matches = sum(1 for kw in keywords if kw in content_lower)
        if matches > 0:
            insights["strategy_patterns"].append({
                "type": pattern_type,
                "confidence": min(0.95, 0.6 + (matches * 0.05)),
                "matches": matches
            })
    
    return insights


def merge_transcriptions(notebooklm_data: dict, whisper_data: dict) -> dict:
    """Merge NotebookLM and Whisper transcriptions."""
    merged = {
        "video_id": notebooklm_data.get("video_id") or whisper_data.get("video_id"),
        "notebooklm": {
            "insights": notebooklm_data.get("insights", {})
        },
        "whisper": {
            "segments": whisper_data.get("segments", []),
            "device": whisper_data.get("device", "unknown"),
            "accuracy": whisper_data.get("accuracy", 0.95)
        },
        "merged_segments": [],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Combine sources of information
    if whisper_data.get("segments"):
        for seg in whisper_data["segments"]:
            merged["merged_segments"].append({
                "start": seg.get("start", 0),
                "end": seg.get("end", 0),
                "text": seg.get("text", ""),
                "source": "whisper",
                "notebooklm_context": None
            })
    
    return merged


def enrich_with_notebooklm(whisper_kb: dict, notebooklm_kb: dict) -> dict:
    """Enrich Whisper knowledge base with NotebookLM insights."""
    enriched = whisper_kb.copy()
    enriched["notebooklm_enriched"] = {
        "analysis": notebooklm_kb.get("analysis", {}),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return enriched


def create_final_kb(notebooklm_file: Path, whisper_file: Path, output_file: Path):
    """Create final merged knowledge base."""
    
    # Load data
    notebooklm_data = load_json_file(notebooklm_file)
    whisper_data = load_json_file(whisper_file)
    
    print(f"Loaded NotebookLM data: {len(str(notebooklm_data))} bytes")
    print(f"Loaded Whisper data: {len(str(whisper_data))} bytes")
    
    # Merge
    merged = extract_notebooklm_insights(notebooklm_data)
    
    # Save enriched data
    output_data = {
        "version": "2.0",
        "processed_at": datetime.utcnow().isoformat(),
        "merger": {
            "method": "notebooklm_insights + whisper_transcription",
            "notebooklm_insights": merged
        },
        "videos": []
    }
    
    # Extract insights for each video
    if whisper_data.get("videos"):
        for video in whisper_data["videos"]:
            video_id = video.get("video_id")
            enriched_video = video.copy()
            enriched_video["notebooklm_insights"] = merged.get("strategy_patterns", [])
            output_data["videos"].append(enriched_video)
    
    # Save final KB
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Final KB saved to: {output_file}")
    print(f"Total videos enriched: {len(output_data['videos'])}")
    
    return output_data


def main():
    parser = argparse.ArgumentParser(
        description="Merge NotebookLM insights with Whisper transcriptions"
    )
    parser.add_argument("--notebooklm", type=Path, required=True,
                       help="NotebookLM report JSON or MD file")
    parser.add_argument("--whisper", type=Path, required=True,
                       help="Whisper transcription JSON file")
    parser.add_argument("--output", type=Path, default="smb_final_kb_enriched.json",
                       help="Output merged KB file")
    
    args = parser.parse_args()
    
    # Create final KB
    result = create_final_kb(args.notebooklm, args.whisper, args.output)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Merge Complete!")
    print("=" * 60)
    print(f"NotebookLM insights: {len(result['merger']['notebooklm_insights'])} patterns")
    print(f"Total videos: {len(result['videos'])}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
