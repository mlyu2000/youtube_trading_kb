#!/usr/bin/env python3
"""
SMB Knowledge Base Merge Script

Merges multiple knowledge base sources:
1. NotebookLM natural language analysis
2. Whisper local transcription (GPU-accelerated)
3. Google Maps OCR (visual content)
4. YouTube API metadata

Outputs:
- Combined KB with enriched metadata
- Strategy pattern index
- Video quality scores
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


# File paths
SMB_DIR = Path("/home/ml")
NOTEBOOKLM_FILES = [
    SMB_DIR / "smb_notebooklm_pilot" / "smb_pilot_report.md"
]
WHISPER_KB_FILES = [
    SMB_DIR / "smb_knowledge_base_final.json",
    SMB_DIR / "smb_knowledge_base_enriched_mm.json"
]
OUTPUT_DIR = SMB_DIR / "smb_notebooklm_pilot"


def load_json(filepath: Path) -> dict:
    """Load JSON with fallback."""
    try:
        if filepath.exists():
            with open(filepath, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load {filepath}: {e}")
    return {}


def parse_notebooklm_report(filepath: Path) -> dict:
    """Parse NotebookLM markdown report to JSON."""
    if not filepath.exists():
        return {"content": "", "analysis": {}}
    
    with open(filepath, "r") as f:
        content = f.read()
    
    # Basic parsing - extract key sections
    analysis = {
        "strategy_patterns": [],
        "risk_management": [],
        "entry_exit_signals": [],
        "assets_mentioned": [],
        "timeframes_mentioned": []
    }
    
    content_lower = content.lower()
    
    # Simple pattern extraction
    patterns = {
        "technical_analysis": ["support", "resistance", "breakout", "chart pattern", "trendline"],
        "momentum": ["rsi", "macd", "stochastic", "indicator"],
        "volume": ["volume", "liquidity", "flow"],
        "risk": ["stop loss", "position size", "risk management", "risk/reward"],
        "price_action": ["candlestick", "reversal", "continuation"]
    }
    
    for pattern_type, keywords in patterns.items():
        matches = sum(1 for kw in keywords if kw in content_lower)
        if matches > 0:
            analysis["strategy_patterns"].append({
                "type": pattern_type,
                "confidence": min(0.95, 0.5 + matches * 0.1),
                "matches": matches
            })
    
    return {
        "content": content,
        "analysis": analysis,
        "source": "notebooklm",
        "processed_at": datetime.utcnow().isoformat()
    }


def extract_strategy_from_video(video_data: dict) -> dict:
    """Extract strategy patterns from video transcript."""
    strategies = {
        "primary_strategy": None,
        "secondary_strategies": [],
        "timeframe": None,
        "assets": [],
        "risk_metrics": {}
    }
    
    # Check for common strategies
    transcript_text = ""
    if isinstance(video_data, dict):
        segments = video_data.get("transcription", {}).get("segments", [])
        transcript_text = " ".join(seg.get("text", "") for seg in segments)
    
    transcript_lower = transcript_text.lower()
    
    strategy_keywords = {
        "day_trading": ["day trade", "intraday", "open", "close", "market hours"],
        "swing_trading": ["swing", "days", "weeks", "momentum"],
        "position_trading": ["position", "hold", "long-term", "fundamental"],
        "scalping": ["scalp", "ticks", "pips", "quick"],
        "technical_analysis": ["chart", "pattern", "candlestick", "indicator"],
        "fundamental_analysis": ["fundamental", "earnings", "news", "event"],
        "sentiment_analysis": ["sentiment", "fear", "greed", "market mood"]
    }
    
    detected = []
    for strategy, keywords in strategy_keywords.items():
        if any(kw in transcript_lower for kw in keywords):
            detected.append(strategy)
    
    if detected:
        strategies["primary_strategy"] = detected[0]
        strategies["secondary_strategies"] = detected[1:]
    
    return strategies


def merge_knowledge_bases():
    """Main merge function."""
    
    print("=" * 60)
    print("SMB Knowledge Base Merge v2.0")
    print("=" * 60)
    print(f"Started: {datetime.utcnow().isoformat()}")
    
    # Load NotebookLM analysis
    print("\n[1/4] Loading NotebookLM analysis...")
    notebooklm_data = parse_notebooklm_report(NOTEBOOKLM_FILES[0])
    print(f"  - Strategy patterns found: {len(notebooklm_data['analysis']['strategy_patterns'])}")
    
    # Load existing Whisper KB
    print("\n[2/4] Loading existing Whisper knowledge base...")
    whisper_kb = load_json(WHISPER_KB_FILES[0])
    
    # Count videos
    video_count = len(whisper_kb.get("videos", []))
    print(f"  - Videos in KB: {video_count}")
    
    # Merge strategy patterns
    print("\n[3/4] Enriching videos with NotebookLM insights...")
    enriched_videos = []
    
    for video in whisper_kb.get("videos", []):
        video_id = video.get("video_id", "unknown")
        
        # Get video-specific data
        video_data = video.copy()
        
        # Extract strategies from transcript
        strategies = extract_strategy_from_video(video_data)
        
        # Add enriched fields
        video_data["notebooklm_analysis"] = notebooklm_data["analysis"]
        video_data["extracted_strategies"] = strategies
        video_data["enriched_at"] = datetime.utcnow().isoformat()
        
        enriched_videos.append(video_data)
    
    # Build final KB
    print("\n[4/4] Building final enriched KB...")
    final_kb = {
        "version": "2.0",
        "created_at": datetime.utcnow().isoformat(),
        "sources": {
            "notebooklm": str(NOTEBOOKLM_FILES[0]),
            "whisper": str(WHISPER_KB_FILES[0])
        },
        "metadata": {
            "total_videos": len(enriched_videos),
            "notebooklm_pattern_count": len(notebooklm_data["analysis"]["strategy_patterns"])
        },
        "videos": enriched_videos,
        "strategy_index": {
            "patterns_detected": notebooklm_data["analysis"]["strategy_patterns"],
            "total_strategy_types": len(notebooklm_data["analysis"]["strategy_patterns"])
        }
    }
    
    # Save final KB
    output_file = OUTPUT_DIR / "smb_final_kb_v2.json"
    with open(output_file, "w") as f:
        json.dump(final_kb, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print("Merge Complete!")
    print("=" * 60)
    print(f"Output: {output_file}")
    print(f"Total videos: {len(enriched_videos)}")
    print(f"Strategy patterns: {len(notebooklm_data['analysis']['strategy_patterns'])}")
    print(f"Enrichment completed at: {datetime.utcnow().isoformat()}")
    
    return final_kb


def main():
    parser = argparse.ArgumentParser(
        description="Merge NotebookLM and Whisper KBs for SMB Capital"
    )
    parser.add_argument("--output", type=Path, default=None,
                       help="Custom output file path")
    
    args = parser.parse_args()
    
    if args.output:
        global OUTPUT_DIR
        OUTPUT_DIR = args.output.parent
    
    result = merge_knowledge_bases()
    
    # Print summary
    print("\nSample enriched video:")
    if result["videos"]:
        sample = result["videos"][0]
        print(f"  Video ID: {sample.get('video_id')}")
        print(f"  Primary strategy: {sample.get('extracted_strategies', {}).get('primary_strategy')}")
        print(f"  Enriched with: {len(sample.get('notebooklm_analysis', {}).get('strategy_patterns', []))} patterns")


if __name__ == "__main__":
    main()
