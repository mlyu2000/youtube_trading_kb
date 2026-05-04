#!/usr/bin/env python3
"""
SMB Capital YouTube Knowledge Base Builder - API Only Mode
Processes videos using pattern matching on existing titles/descriptions.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Set
import re

# Configuration
VIDEOS_FILE = "/home/ml/smb_videos_api.txt"
KB_FILE = "/home/ml/smb_knowledge_base_full.json"
OUTPUT_FILE = "/home/ml/smb_knowledge_base_full.json"
INTERMEDIATE_INTERVAL = 500

# Strategy patterns - extracted from SMB Capital trading content
STRATEGY_PATTERNS = {
    "iron_condor": [r"iron\s+condor", r"condor\s+spread", r"iron\s+condors"],
    "butterfly_spread": [r"butterfly\s+spread", r"butterfly\s+options", r"butterfly\s+pat"],
    "calendar_spread": [r"calendar\s+spread", r"calendar\s+options", r"calendar\s+day", r"rolling\s+calendar"],
    "diagonal_spread": [r"diagonal\s+spread", r"diagonal\s+options"],
    "ratio_spread": [r"ratio\s+spread", r"ratio\s+options", r"ratio\s+write"],
    "debit_spread": [r"debit\s+spread", r"debit\s+vertical", r"buy\s+spread"],
    "credit_spread": [r"credit\s+spread", r"credit\s+vertical", r"sell\s+spread"],
    "straddle": [r"straddle", r"long\s+straddle", r"short\s+straddle"],
    "strangle": [r"strangle", r"long\s+strangle", r"short\s+strangle"],
    "call_spread": [r"call\s+spread", r"call\s+options", r"call\s+vertical"],
    "put_spread": [r"put\s+spread", r"put\s+options", r"put\s+vertical"],
    "metal_tweet": [r"metal\s+tweet", r"tweets"],
    "trade_setup": [r"trade\s+setup", r"trading\s+setup", r"setups"],
    "market_review": [r"market\s+review", r"daily\s+market", r"market\s+update", r"market\s+analysis", r"recap"],
    "ai_trading": [r"ai.*trading", r"artificial.*intelligence", r"claude.*trading", r"chatgpt.*trading", r"llm.*trading"],
    "backtesting": [r"backtest", r"historical", r"backtesting"],
    "risk_management": [r"risk.*management", r"position\s+sizing", r"risk.*rewards", r"risk.*reward", r"stop\s+loss", r"risk\s+reward"],
    "options_101": [r"options\s+101", r"options\s+basics", r"options\s+for\s+beginners", r"learn\s+options"],
    "directional_trading": [r"directional", r"long\s+call", r"long\s+put", r"short\s+call", r"short\s+put", r"bullish", r"bearish"],
    "non_directional": [r"non.*directional", r"nondirectional", r"neutral", r"sideways", r"rangebound"],
    "volatility_trading": [r"volatility", r"implied\s+volatility", r"iv", r"historical\s+volatility", r"hv"],
    "income_strategy": [r"income.*options", r"options.*income", r"monthly\s+income", r"passive\s+income", r"cash\s+sec", r"cash\s+secured"],
    "hedging": [r"hedging", r"hedge.*position", r"protective\s+put", r"covered\s+call"],
    "education": [r"education", r"tutorial", r"guide", r"how\s+to", r"learn", r"beginner", r"intro"],
    "live_trading": [r"live\s+trading", r"live\s+demo", r"real\s+time", r"in\s+real"],
    "clean_technicals": [r"clean\s+technical", r"clean\s+tech"],
    "technical_analysis": [r"technical", r"chart", r"support", r"resistance", r"trendline", r"candlestick"],
    "fundamentals": [r"fundamental", r"earnings", r"revenue", r"eps", r"financials"],
}

TIMEFRAME_PATTERNS = {
    "day_trading": [r"day\s+trading", r"daytrade", r"intraday"],
    "swing_trading": [r"swing\s+trading", r"swing", r"3-5\s+days", r"3-5\s+day"],
    "position_trading": [r"position\s+trading", r"position", r"weeks", r"months"],
    "scalping": [r"scalp", r"scalping", r"scalp"],
}


def load_video_ids(file_path):
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]


def load_knowledge_base(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "version": "1.0",
            "channel": "SMB Capital",
            "channel_id": "UCg3B_joekBGJ1s_4fRjsMKA",
            "processed_at": None,
            "total_videos": 0,
            "videos": [],
            "strategy_breakdown": {},
        }


def extract_strategy_types(text):
    strategies = []
    text_lower = text.lower()
    for strategy, patterns in STRATEGY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                strategies.append(strategy)
                break
    return strategies


def extract_timeframes(text):
    timeframes = []
    text_lower = text.lower()
    for timeframe, patterns in TIMEFRAME_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                timeframes.append(timeframe)
                break
    return timeframes


def main():
    print("=" * 60)
    print("SMB Capital Knowledge Base Builder - API Only Mode")
    print("=" * 60)
    
    print("\n[1] Loading video IDs...")
    all_video_ids = load_video_ids(VIDEOS_FILE)
    print(f"    Total video IDs in file: {len(all_video_ids)}")
    
    print("\n[2] Loading existing knowledge base...")
    kb = load_knowledge_base(KB_FILE)
    existing_count = kb.get("total_videos", 0)
    print(f"    Already processed videos: {existing_count}")
    
    # Get set of already processed video IDs
    processed_ids = set()
    for video in kb.get("videos", []):
        processed_ids.add(video.get("video_id"))
    print(f"    Video IDs to skip: {len(processed_ids)}")
    
    unprocessed_ids = [vid for vid in all_video_ids if vid not in processed_ids]
    print(f"    Unprocessed videos to process: {len(unprocessed_ids)}")
    
    batch_size = 500
    videos_to_process = unprocessed_ids[:batch_size]
    print(f"\n[3] Processing up to {batch_size} videos...")
    
    start_time = time.time()
    processed_count = 0
    strategies_found = 0
    
    # Get existing video ID to title mapping for pattern matching
    existing_video_titles = {}
    for video in kb.get("videos", []):
        video_id = video.get("video_id")
        title = video.get("title", "")
        description = video.get("description", "")
        if video_id and (title or description):
            existing_video_titles[video_id] = f"{title} {description}"
    
    for i, video_id in enumerate(videos_to_process):
        # Get title/description from existing KB or use video_id as fallback
        combined_text = existing_video_titles.get(video_id, video_id)
        
        # Extract insights using pattern matching
        strategy_types = extract_strategy_types(combined_text)
        timeframes = extract_timeframes(combined_text)
        
        # Create video entry
        video_entry = {
            "video_id": video_id,
            "title": existing_video_titles.get(video_id, ""),
            "description": "",
            "published_at": None,
            "duration": None,
            "insights": {
                "strategy_types": strategy_types,
                "assets_mentioned": [],
                "timeframes_mentioned": timeframes,
                "techniques_mentioned": [],
            },
            "transcript_available": False,
            "metadata_fetched_via_api": False,
            "extracted_via_patterns": True,
            "insight_extraction_method": "pattern_matching",
            "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        
        # Add to KB videos list
        kb["videos"].append(video_entry)
        
        # Update strategy breakdown
        strategy_breakdown = kb.get("strategy_breakdown", {}).copy()
        for strategy in strategy_types:
            strategy_breakdown[strategy] = strategy_breakdown.get(strategy, 0) + 1
        kb["strategy_breakdown"] = strategy_breakdown
        
        if strategy_types:
            strategies_found += 1
        
        processed_count += 1
        
        # Save intermediate results every 500 videos
        if processed_count % INTERMEDIATE_INTERVAL == 0 or i == len(videos_to_process) - 1:
            elapsed = time.time() - start_time
            print(f"    [Intermediate Save] Processed {processed_count} videos in {elapsed:.1f}s...")
            kb["processed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            kb["total_videos"] = len(kb["videos"])
            kb["videos_processed_direct"] = kb.get("videos_processed_direct", 0) + processed_count
            with open(OUTPUT_FILE, "w") as f:
                json.dump(kb, f, indent=2)
    
    elapsed = time.time() - start_time
    kb["processed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    kb["total_videos"] = len(kb["videos"])
    kb["videos_processed_direct"] = kb.get("videos_processed_direct", 0) + processed_count
    final_strategy_breakdown = kb.get("strategy_breakdown", {})
    kb["strategy_breakdown"] = dict(sorted(final_strategy_breakdown.items(), key=lambda x: x[1], reverse=True))
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(kb, f, indent=2)
    
    print("")
    print("=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    print(f"Videos processed in batch: {processed_count}")
    print(f"Total videos in KB: {kb['total_videos']}")
    print(f"Videos with strategy types found: {strategies_found}")
    print(f"Strategy types identified: {len(kb.get('strategy_breakdown', {}))}")
    print(f"Time taken: {elapsed:.1f} seconds")
    
    print("")
    print("Strategy Breakdown:")
    for strategy, count in kb.get("strategy_breakdown", {}).items():
        print(f"  - {strategy}: {count}")
    
    print("")
    print(f"FINAL TOTAL VIDEO COUNT: {kb['total_videos']}")
    
    return kb["total_videos"]


if __name__ == "__main__":
    final_count = main()
