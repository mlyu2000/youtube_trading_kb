#!/usr/bin/env python3
"""
SMB Knowledge Base Merge Script v3.0 - With Visual Chart/Diagram OCR Enrichment

Merges multiple knowledge base sources:
1. NotebookLM natural language analysis
2. Whisper local transcription (GPU-accelerated)
3. Google Maps OCR (visual content)
4. YouTube API metadata

Outputs:
- Combined KB with enriched metadata
- Strategy pattern index
- Visual chart/diagram index
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


def extract_visual_ocr_insights(video_data: dict) -> dict:
    """Extract visual chart/diagram OCR insights from video data.
    
    OCR Schema v2.0:
    - frame_id: frame identifier
    - timestamp: video timestamp (seconds)
    - visual_type: portrait/landscape/square
    - description: frame content description
    - ocr_results: [{text, confidence, bounding_box}]
    - detected_chart_type: price_chart, bar_chart, line_chart, etc.
    - ocr_confidence_avg: average OCR confidence
    """
    
    ocr_data = video_data.get("ocr", {})
    if not ocr_data or ocr_data.get("result_count", 0) == 0:
        return {"visual_ocr_enabled": False}
    
    visual_insights = ocr_data.get("visual_insights", {})
    
    # Extract chart summary
    chart_summary = visual_insights.get("chart_summary", {})
    
    # Build chart index
    chart_index = {}
    for chart_type, data in chart_summary.items():
        chart_index[chart_type] = {
            "count": data["count"],
            "supporting_frames": data["timestamps"],
            "sample_texts": [r["text"] for r in data["ocr_samples"][:5]]
        }
    
    # Extract visual timestamps with high confidence OCR
    visual_timestamps = visual_insights.get("visual_timestamps", [])
    
    return {
        "visual_ocr_enabled": True,
        "total_visual_entries": visual_insights.get("total_visual_entries", 0),
        "chart_summary": chart_index,
        "visual_timestamps": visual_timestamps[:10],  # Top 10
        "ocr_confidence_avg": ocr_data.get("visual_insights", {}).get("total_visual_entries", 0) > 0
    }


def merge_knowledge_bases():
    """Main merge function."""
    
    print("=" * 60)
    print("SMB Knowledge Base Merge v3.0 - Visual OCR Enriched")
    print("=" * 60)
    print(f"Started: {datetime.utcnow().isoformat()}")
    
    # Load NotebookLM analysis
    print("\n[1/5] Loading NotebookLM analysis...")
    notebooklm_data = parse_notebooklm_report(NOTEBOOKLM_FILES[0])
    print(f"  - Strategy patterns found: {len(notebooklm_data['analysis']['strategy_patterns'])}")
    
    # Load existing Whisper KB
    print("\n[2/5] Loading existing Whisper knowledge base...")
    whisper_kb = load_json(WHISPER_KB_FILES[0])
    
    # Count videos
    video_count = len(whisper_kb.get("videos", []))
    print(f"  - Videos in KB: {video_count}")
    
    # Merge strategy patterns and visual OCR
    print("\n[3/5] Enriching videos with NotebookLM insights...")
    enriched_videos = []
    
    # Count visual OCR enrichment
    visual_ocr_count = 0
    chart_types_detected = set()
    
    for video in whisper_kb.get("videos", []):
        video_id = video.get("video_id", "unknown")
        
        # Get video-specific data
        video_data = video.copy()
        
        # Extract strategies from transcript
        strategies = extract_strategy_from_video(video_data)
        
        # Extract visual OCR insights
        visual_insights = extract_visual_ocr_insights(video_data)
        
        if visual_insights.get("visual_ocr_enabled", False):
            visual_ocr_count += 1
            for chart_type in visual_insights.get("chart_summary", {}).keys():
                chart_types_detected.add(chart_type)
        
        # Add enriched fields
        video_data["notebooklm_analysis"] = notebooklm_data["analysis"]
        video_data["extracted_strategies"] = strategies
        video_data["visual_ocr_insights"] = visual_insights
        video_data["enriched_at"] = datetime.utcnow().isoformat()
        
        enriched_videos.append(video_data)
    
    # Build final KB
    print("\n[4/5] Building final enriched KB...")
    
    # Determine if visual OCR was available
    visual_ocr_available = visual_ocr_count > 0
    
    final_kb = {
        "version": "3.0",
        "created_at": datetime.utcnow().isoformat(),
        "sources": {
            "notebooklm": str(NOTEBOOKLM_FILES[0]),
            "whisper": str(WHISPER_KB_FILES[0]),
            "visual_ocr": "enabled" if visual_ocr_available else "disabled"
        },
        "metadata": {
            "total_videos": len(enriched_videos),
            "notebooklm_pattern_count": len(notebooklm_data["analysis"]["strategy_patterns"]),
            "visual_ocr_enriched": visual_ocr_count,
            "total_visual_entries": sum(v.get("visual_ocr_insights", {}).get("total_visual_entries", 0) for v in enriched_videos),
            "chart_types_detected": list(chart_types_detected)
        },
        "videos": enriched_videos,
        "strategy_index": {
            "patterns_detected": notebooklm_data["analysis"]["strategy_patterns"],
            "total_strategy_types": len(notebooklm_data["analysis"]["strategy_patterns"])
        },
        "visual_ocr_index": {
            "enabled": visual_ocr_available,
            "total_entries": sum(v.get("visual_ocr_insights", {}).get("total_visual_entries", 0) for v in enriched_videos),
            "chart_types": list(chart_types_detected),
            "summary": {
                chart_type: sum(1 for v in enriched_videos 
                              if v.get("visual_ocr_insights", {}).get("chart_summary", {}).get(chart_type, {}).get("count", 0) > 0)
                for chart_type in chart_types_detected
            }
        } if visual_ocr_available else None
    }
    
    # Save final KB
    output_file = OUTPUT_DIR / "smb_final_kb_v3.json"
    with open(output_file, "w") as f:
        json.dump(final_kb, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print("Merge Complete!")
    print("=" * 60)
    print(f"Output: {output_file}")
    print(f"Total videos: {len(enriched_videos)}")
    print(f"Strategy patterns: {len(notebooklm_data['analysis']['strategy_patterns'])}")
    print(f"Visual OCR enriched: {visual_ocr_count} videos")
    print(f"Total visual entries: {final_kb['metadata']['total_visual_entries']}")
    print(f"Chart types detected: {final_kb['metadata']['chart_types_detected']}")
    print(f"Enrichment completed at: {datetime.utcnow().isoformat()}")
    
    return final_kb


def main():
    parser = argparse.ArgumentParser(
        description="Merge NotebookLM, Whisper, and Visual OCR for SMB Capital"
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
        print(f"  Enriched with NotebookLM: {len(sample.get('notebooklm_analysis', {}).get('strategy_patterns', []))} patterns")
        
        visual_ocr = sample.get("visual_ocr_insights", {})
        if visual_ocr.get("visual_ocr_enabled"):
            print(f"  Visual OCR enabled: YES")
            print(f"    Chart types: {list(visual_ocr.get('chart_summary', {}).keys())}")
            print(f"    Total entries: {visual_ocr.get('total_visual_entries', 0)}")
        else:
            print(f"  Visual OCR enabled: NO")


if __name__ == "__main__":
    main()
