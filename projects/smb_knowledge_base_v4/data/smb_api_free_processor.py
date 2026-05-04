#!/usr/bin/env python3
"""
SMB Capital YouTube Knowledge Base Builder - API-Free Approach
Uses yt-dlp alone (no API key required) + Whisper for transcription
"""

import json
import os
import time
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("ERROR: yt_dlp not installed")
    exit(1)

try:
    from whisper import load_model
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Warning: whisper not available")


def extract_url_metadata(video_url):
    """Extract video metadata using yt-dlp (no API key needed)"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'discard',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return {
                'id': info.get('id'),
                'title': info.get('title'),
                'description': info.get('description'),
                'publishedAt': info.get('upload_date', '') if info.get('upload_date') else '',
                'duration': info.get('duration_string', ''),
                'viewCount': info.get('view_count', 0),
                'likeCount': info.get('like_count', 0),
            }
    except Exception as e:
        print(f"  Metadata extraction error: {e}")
        return None


def download_audio(video_url, output_dir, video_id):
    """Download audio using yt-dlp"""
    output_pattern = f"{output_dir}/{video_id}.%(ext)s"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_pattern,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        for ext in ['wav', 'mp3']:
            files = list(Path(output_dir).glob(f"{video_id}*.{ext}"))
            if files:
                return str(files[0])
    except Exception as e:
        print(f"  Download error: {e}")
    return None


def transcribe_with_whisper(audio_path):
    """Transcribe audio using Whisper"""
    if not WHISPER_AVAILABLE:
        return None
    
    try:
        model = load_model("base")
        result = model.transcribe(audio_path, fp16=False)
        return result['segments']
    except Exception as e:
        print(f"  Transcribe error: {e}")
    return None


def extract_visual_timestamps(segments):
    """Extract visual content timestamps using rule-based detection"""
    visual_entries = []
    visual_patterns = {
        'chart': ['chart', 'chart pattern', 'technical analysis'],
        'options_chain': ['options chain', 'options strategies'],
        'volume_plot': ['volume', 'volume analysis'],
        'moving_averages': ['moving average', 'ma', 'sma', 'ema'],
        'price_chart': ['price action', 'candlestick'],
        'risk_management': ['risk', 'position size', 'stop loss'],
    }
    
    for segment in segments:
        start = segment['start']
        text = segment['text'].lower()
        for visual_type, keywords in visual_patterns.items():
            if any(k in text for k in keywords):
                confidence = min(0.7 + sum(1 for k in keywords if k in text) * 0.05, 0.95)
                visual_entries.append({
                    'timestamp': round(start, 2),
                    'timecode': f"{int(start//60):02d}:{int(start%60):02d}",
                    'visual_type': visual_type,
                    'description': f"Visual: {text[:60]}",
                    'confidence': round(confidence, 2),
                    'transcript_context': segment['text']
                })
    return visual_entries


def process_video(video_id, download_dir, loaded_ids):
    """Process single video using yt-dlp + Whisper"""
    if video_id in loaded_ids:
        return None
    
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    print(f"  Processing: {video_id}")
    
    metadata = extract_url_metadata(video_url)
    if not metadata:
        return None
    
    audio_path = download_audio(video_url, download_dir, video_id) if download_dir else None
    
    segments = transcribe_with_whisper(audio_path) if audio_path else []
    
    visual_entries = extract_visual_timestamps(segments) if segments else []
    
    if audio_path and Path(audio_path).exists():
        try:
            Path(audio_path).unlink()
        except:
            pass
    
    video_entry = {
        'id': metadata['id'],
        'title': metadata['title'],
        'description': metadata['description'],
        'publishedAt': metadata['publishedAt'],
        'duration': metadata['duration'],
        'views': metadata.get('viewCount', 0),
        'likes': metadata.get('likeCount', 0),
        'transcript_segments': segments,
        'visual_entries': visual_entries
    }
    
    return video_entry


def main():
    video_ids_file = Path('/home/ml/smb_all_video_ids.txt')
    
    if not video_ids_file.exists():
        print("ERROR: Video IDs file not found")
        return
    
    with open(video_ids_file) as f:
        video_ids = [line.strip() for line in f if line.strip()]
    
    print(f"Processing {len(video_ids)} videos (API-free approach)...")
    
    output_dir = '/home/ml/smb_processor'
    Path(output_dir).mkdir(exist_ok=True)
    kb_path = Path(output_dir) / 'smb_knowledge_base_multi_modal.json'
    stats_path = Path(output_dir) / 'smb_knowledge_base_stats.json'
    
    download_dir = '/home/ml/video_downloads'
    Path(download_dir).mkdir(exist_ok=True)
    
    kb = []
    loaded_ids = set()
    if kb_path.exists():
        with open(kb_path) as f:
            kb = json.load(f)
            for v in kb:
                loaded_ids.add(v['id'])
        print(f"Loaded {len(loaded_ids)} existing videos")
    
    batch_size = 25
    for i in range(0, len(video_ids), batch_size):
        batch = video_ids[i:i+batch_size]
        print(f"\n=== Batch {i//batch_size + 1}: {i} to {i+len(batch)} ===")
        
        for vid_id in batch:
            try:
                result = process_video(vid_id, download_dir, loaded_ids)
                if result:
                    kb.append(result)
                    loaded_ids.add(vid_id)
                    print(f"    processed: {vid_id} ({len(result['transcript_segments'])} segments, {len(result['visual_entries'])} visuals)")
                time.sleep(0.5)
            except Exception as e:
                print(f"    error: {vid_id}")
        
        with open(kb_path, 'w') as f:
            json.dump(kb, f, indent=2, default=str)
        
        total_segments = sum(len(v.get('transcript_segments', [])) for v in kb)
        total_visuals = sum(len(v.get('visual_entries', [])) for v in kb)
        
        visual_types = {}
        for v in kb:
            for entry in v.get('visual_entries', []):
                t = entry.get('visual_type', 'unknown')
                visual_types[t] = visual_types.get(t, 0) + 1
        
        stats = {
            'total_videos': len(kb),
            'total_transcript_segments': total_segments,
            'total_visual_entries': total_visuals,
            'visual_type_distribution': visual_types
        }
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"Saved: {len(kb)} videos, {total_segments} segments, {total_visuals} visuals")


if __name__ == '__main__':
    main()
