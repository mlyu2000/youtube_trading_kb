#!/usr/bin/env python3
"""Minimal test: process 2 videos, verify Whisper + visual extraction"""

import yt_dlp
import whisper
import json
from pathlib import Path

print("Starting SMB Capital test processing...")

# Process first 2 videos from the list
test_ids = ["45eaVU5NVi8", "sh5h0GJzjNk"]
output_dir = Path("/home/ml/smb_processor")
output_dir.mkdir(exist_ok=True)
downloads_dir = Path("/home/ml/video_downloads")
downloads_dir.mkdir(exist_ok=True)

# Load any existing KB
kb_path = output_dir / "smb_knowledge_base_multi_modal.json"
kb = []
if kb_path.exists():
    with open(kb_path) as f:
        try:
            kb = json.load(f)
        except:
            kb = []
existing_ids = {v.get("id") or v.get("video_id") for v in kb}

print(f"Existing KB videos: {len(kb)}")

for vid_id in test_ids:
    if vid_id in existing_ids:
        print(f"  Already processed: {vid_id}")
        continue
        
    print(f"Processing: {vid_id}")
    video_url = f"https://www.youtube.com/watch?v={vid_id}"
    
    # Download audio with yt-dlp
    audio_path = downloads_dir / f"{vid_id}.wav"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(downloads_dir / f"{vid_id}"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav"}],
        "quiet": True,
        "no_warnings": True,
    }
    
    print("  Downloading audio...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
    
    print(f"  Title: {info.get('title', 'N/A')}")
    
    # Transcribe with Whisper
    print("  Transcribing with Whisper base model...")
    model = whisper.load_model("base")
    result = model.transcribe(str(audio_path), fp16=False)
    
    segments = result["segments"]
    print(f"  Segments: {len(segments)}")
    
    # Visual extraction
    visual_patterns = {
        "chart": ["chart", "technical analysis"],
        "options_chain": ["options chain"],
        "volume_plot": ["volume"],
        "moving_averages": ["moving average", "sma", "ema"],
    }
    
    visuals = []
    for seg in segments:
        text = seg["text"].lower()
        for vtype, keywords in visual_patterns.items():
            if any(k in text for k in keywords):
                conf = min(0.7 + sum(1 for k in keywords if k in text) * 0.05, 0.95)
                visuals.append({
                    "timestamp": round(seg["start"], 2),
                    "timecode": f"{int(seg['start']//60):02d}:{int(seg['start']%60):02d}",
                    "visual_type": vtype,
                    "description": f"Visual: {seg['text'][:60]}",
                    "confidence": round(conf, 2),
                    "transcript_context": seg["text"],
                })
    
    print(f"  Visual entries: {len(visuals)}")
    
    # Add to KB
    kb.append({
        "id": vid_id,
        "title": info.get("title", ""),
        "description": info.get("description", ""),
        "publishedAt": info.get("upload_date", ""),
        "duration": info.get("duration_string", ""),
        "views": info.get("view_count", 0),
        "likes": info.get("like_count", 0),
        "transcript_segments": segments,
        "visual_entries": visuals,
    })
    
    # Clean up audio (to save disk space)
    if audio_path.exists():
        audio_path.unlink()
    
    # Save progress after each video
    with open(kb_path, "w") as f:
        json.dump(kb, f, indent=2, default=str)
    
    print(f"  Saved to {kb_path}")

# Final summary
total_segments = sum(len(v.get("transcript_segments", [])) for v in kb)
total_visuals = sum(len(v.get("visual_entries", [])) for v in kb)

print()
print("=== Final Test Results ===")
print(f"Videos processed: {len(kb)}")
print(f"Transcript segments: {total_segments}")
print(f"Visual entries: {total_visuals}")
print(f"KB size: {(Path(kb_path).stat().st_size / 1024):.1f} KB")

# Visual type distribution
visual_types = {}
for v in kb:
    for entry in v.get("visual_entries", []):
        t = entry.get("visual_type", "unknown")
        visual_types[t] = visual_types.get(t, 0) + 1
print(f"Visual types: {visual_types}")
