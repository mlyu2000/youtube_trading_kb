#!/home/ml/.hermes/hermes-agent/venv/bin/python
"""
SMB Capital YouTube Knowledge Base Pipeline
- Downloads videos with yt-dlp
- Transcribes with Whisper
- Extracts visual timestamps
- Builds comprehensive knowledge base
"""

import os
import json
import glob
import time
from typing import List, Dict, Any

import yt_dlp
from whisper import load_model

# Configuration
OUTPUT_DIR = "/home/ml/smb_processor"
DOWNLOADS_DIR = f"{OUTPUT_DIR}/downloads"
PROCESSED_DIR = f"{OUTPUT_DIR}/output"
KB_PATH = f"{OUTPUT_DIR}/smb_knowledge_base_final.json"
VIDEO_IDS_FILE = "/home/ml/smb_all_video_ids.txt"

# Ensure directories exist
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Load Whisper model (base for faster processing)
print("Loading Whisper model...")
whisper_model = load_model("base")


def load_video_ids() -> List[str]:
    """Load video IDs from file."""
    with open(VIDEO_IDS_FILE, 'r') as f:
        return [line.strip() for line in f if line.strip()]


def get_processed_video_ids() -> set:
    """Get IDs of already processed videos."""
    processed_files = glob.glob(f"{PROCESSED_DIR}/*.json")
    processed_ids = set()
    for f in processed_files:
        try:
            with open(f, 'r') as fp:
                data = json.load(fp)
                processed_ids.add(data.get('video_id'))
        except:
            pass
    return processed_ids


def download_video(video_id: str) -> str:
    """Download a single video. Returns path to downloaded file."""
    output_path = f"{DOWNLOADS_DIR}/{video_id}.%(ext)s"
    
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
    }
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            files = glob.glob(f"{DOWNLOADS_DIR}/{video_id}.*")
            if files:
                return files[0]
    except Exception as e:
        print(f"Error downloading {video_id}: {e}")
        return None


def transcribe_video(audio_path: str) -> List[Dict[str, Any]]:
    """Transcribe audio using Whisper. Returns list of segments."""
    try:
        result = whisper_model.transcribe(audio_path, word_timestamps=True)
        segments = []
        for seg in result['segments']:
            segments.append({
                'timestamp': seg['start'],
                'end_timestamp': seg['end'],
                'text': seg['text'].strip(),
            })
        return segments
    except Exception as e:
        print(f"Error transcribing {audio_path}: {e}")
        return []


def extract_visual_timestamps(segments: List[Dict]) -> List[Dict[str, Any]]:
    """Extract visual timestamps from transcript segments."""
    visual_entries = []
    
    visual_keywords = [
        'chart', 'diagram', 'graph', 'plot', 'candle', 'candlestick',
        'pattern', 'indicator', 'moving average', 'rsi', 'macd', 'bollinger',
        'volume', 'support', 'resistance', 'trend', 'scan', 'setup'
    ]
    
    for seg in segments:
        timestamp = seg['timestamp']
        text = seg['text'].lower()
        
        if any(kw in text for kw in visual_keywords):
            visual_type = 'chart_or_diagram'
            if 'volume' in text:
                visual_type = 'volume_chart'
            elif 'option' in text or 'chain' in text:
                visual_type = 'options_chain'
            
            minute = int(timestamp // 60)
            second = int(timestamp % 60)
            timecode = f"{minute:02d}:{second:02d}"
            
            visual_entries.append({
                'timestamp': timestamp,
                'timecode': timecode,
                'visual_type': visual_type,
                'description': f"Visual content at {timecode}",
                'confidence': 0.75,
                'transcript_context': seg['text'][:200]
            })
    
    return visual_entries


def process_video(video_id: str) -> Dict[str, Any]:
    """Process a single video: download, transcribe, extract visual content."""
    print(f"Processing video: {video_id}")
    
    audio_path = download_video(video_id)
    if not audio_path:
        return None
    
    print(f"Downloaded: {audio_path}")
    
    segments = transcribe_video(audio_path)
    if not segments:
        return None
    
    print(f"Transcribed {len(segments)} segments")
    
    visual_entries = extract_visual_timestamps(segments)
    print(f"Extracted {len(visual_entries)} visual entries")
    
    return {
        'video_id': video_id,
        'segments': segments,
        'visual_entries': visual_entries,
        'download_path': audio_path,
        'processed_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }


def save_processed_video(video_entry: Dict[str, Any], video_id: str):
    """Save processed video data to JSON file."""
    output_path = f"{PROCESSED_DIR}/{video_id}_processed.json"
    with open(output_path, 'w') as f:
        json.dump(video_entry, f, indent=2)
    print(f"Saved: {output_path}")


def merge_into_kb(video_entry: Dict[str, Any], kb: Dict[str, Any]) -> Dict[str, Any]:
    """Merge a processed video into the knowledge base."""
    video_id = video_entry['video_id']
    
    existing_idx = None
    for i, v in enumerate(kb['videos']):
        if v['video_id'] == video_id:
            existing_idx = i
            break
    
    if existing_idx is not None:
        kb['videos'][existing_idx] = video_entry
    else:
        kb['videos'].append(video_entry)
        kb['total_videos'] = len(kb['videos'])
    
    return kb


def main():
    """Main pipeline execution."""
    print("=" * 60)
    print("SMB Capital YouTube Knowledge Base Pipeline")
    print("=" * 60)
    
    all_video_ids = load_video_ids()
    print(f"Total video IDs: {len(all_video_ids)}")
    
    processed_ids = get_processed_video_ids()
    print(f"Already processed: {len(processed_ids)}")
    
    remaining_ids = [vid for vid in all_video_ids if vid not in processed_ids]
    print(f"Remaining to process: {len(remaining_ids)}")
    
    if os.path.exists(KB_PATH):
        with open(KB_PATH, 'r') as f:
            kb = json.load(f)
        print(f"Loaded KB with {kb['total_videos']} videos")
    else:
        kb = {
            'version': '1.0',
            'channel': 'SMB Capital',
            'channel_id': 'UCg3B_joekBGJ1s_4fRjsMKA',
            'processed_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'total_videos': 0,
            'videos': [],
            'summary': {'total_segments': 0, 'total_visual': 0}
        }
    
    batch_size = 2
    start_idx = 0
    
    # TEST MODE: process only 2 videos first
    while start_idx < min(2, len(remaining_ids)):
        end_idx = min(start_idx + batch_size, len(remaining_ids))
        batch = remaining_ids[start_idx:end_idx]
        
        print(f"\n--- Batch {start_idx}-{end_idx} ---")
        
        for video_id in batch:
            video_entry = process_video(video_id)
            if video_entry:
                save_processed_video(video_entry, video_id)
                kb = merge_into_kb(video_entry, kb)
        
        kb['summary']['total_segments'] = sum(len(v.get('segments', [])) for v in kb['videos'])
        kb['summary']['total_visual'] = sum(len(v.get('visual_entries', [])) for v in kb['videos'])
        
        with open(KB_PATH, 'w') as f:
            json.dump(kb, f, indent=2)
        
        print(f"Total: {kb['total_videos']} videos, "
              f"{kb['summary']['total_segments']} segs, "
              f"{kb['summary']['total_visual']} visual")
        
        start_idx = end_idx
        
        if start_idx < len(remaining_ids):
            time.sleep(5)
    
    print("\n=== Complete ===")
    print(f"KB: {KB_PATH}")
    print(f"Videos: {kb['total_videos']}, Segments: {kb['summary']['total_segments']}, Visual: {kb['summary']['total_visual']}")


if __name__ == '__main__':
    main()
