#!/usr/bin/env python3
"""
SMB Capital Video Processor - Alternative Method
1. Scrape YouTube channel for video IDs
2. Download videos directly with yt-dlp
3. Transcribe with Whisper
4. Extract visual timestamps
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import time
import re
import urllib.request

from PIL import Image
import whisper


class SMBAlternativeProcessor:
    def __init__(self, output_dir="/home/ml/smb_processor"):
        self.output_dir = Path(output_dir)
        self.raw_dir = self.output_dir / "videos" / "raw"
        self.frames_dir = self.output_dir / "frames"
        self.processed_dir = self.output_dir / "output"
        for d in [self.raw_dir, self.frames_dir, self.processed_dir]:
            d.mkdir(parents=True, exist_ok=True)
        print("Loading Whisper base model...")
        self.model = whisper.load_model("base")
        print("✓ Whisper loaded")
        
    def scrape_channel(self, channel_url: str) -> List[str]:
        """Scrape YouTube channel for video IDs"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        req = urllib.request.Request(channel_url, headers=headers)
        try:
            response = urllib.request.urlopen(req, timeout=30)
            content = response.read().decode('utf-8', errors='ignore')
            
            vid_pattern = r'/watch\?v=([a-zA-Z0-9_-]{11})'
            vids = re.findall(vid_pattern, content)
            unique_vids = list(set(vids))
            
            print(f"Scraped {len(vids)} video IDs, {len(unique_vids)} unique")
            return unique_vids
        except Exception as e:
            print(f"Scraping error: {e}")
            return []
    
    def download_video(self, video_id: str) -> Optional[Path]:
        """Download video using yt-dlp"""
        output = self.raw_dir / f"{video_id}.mp4"
        
        if output.exists():
            return output
            
        print(f"  Downloading {video_id}...")
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        result = subprocess.run([
            'yt-dlp', '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '-o', str(output),
            '--no-warnings',
            '--no-playlist',
            url
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"  Retrying with --no-check-certificates...")
            result = subprocess.run([
                'yt-dlp', '-f', 'best[ext=mp4]',
                '-o', str(output),
                '--no-check-certificates',
                '--no-warnings',
                '--no-playlist',
                url
            ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0 and output.exists():
            size = output.stat().st_size
            if size > 1000:
                return output
        
        return None
        
    def transcribe_video(self, video_path: Path) -> List[Dict]:
        """Transcribe video with Whisper"""
        audio_path = self.raw_dir / f"{video_path.stem}.mp3"
        
        if not audio_path.exists():
            print(f"  Extracting audio...")
            result = subprocess.run([
                'ffmpeg', '-i', str(video_path), '-vn', '-acodec', 'libmp3lame',
                '-ar', '16000', '-ac', '1', str(audio_path)
            ], capture_output=True, text=True)
        
        print(f"  Transcribing with Whisper...")
        start_time = time.time()
        result = self.model.transcribe(str(audio_path), language='en', task='transcribe')
        elapsed = time.time() - start_time
        print(f"  Transcription complete in {elapsed:.1f}s, {len(result['segments'])} segments")
        return result['segments']
    
    def extract_visual_timestamps(self, video_path: Path, interval: int = 5) -> List[Dict]:
        """Extract visual content timestamps from video"""
        frames_path = self.frames_dir / video_path.stem
        frames_path.mkdir(parents=True, exist_ok=True)
        
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', str(video_path)
        ], capture_output=True, text=True)
        
        duration = float(result.stdout.strip()) if result.stdout.strip() else 0
        num_frames = max(1, int(duration // interval))
        
        print(f"  Extracting {num_frames} frames (1 per {interval}s)...")
        
        timestamp_pattern = str(frames_path / "frame_%04d.jpg")
        subprocess.run([
            'ffmpeg', '-i', str(video_path), '-vf', f'fps=1/{interval}',
            '-q:v', '2', timestamp_pattern
        ], capture_output=True, text=True)
        
        visual_entries = []
        frames_found = sorted(frames_path.glob("frame_*.jpg"))
        
        for i, frame_path in enumerate(frames_found):
            timestamp = i * interval
            minutes = timestamp // 60
            secs = timestamp % 60
            timecode = f"{int(minutes):02d}:{int(secs):02d}"
            
            with Image.open(frame_path) as img:
                width, height = img.size
                aspect_ratio = width / height if height > 0 else 0
                
                if width < height:
                    visual_type = "host_explanation"
                    confidence = 0.75
                elif aspect_ratio > 1.5:
                    visual_type = "chart_or_diagram"
                    confidence = 0.85
                else:
                    visual_type = "square_preview"
                    confidence = 0.7
                    
            visual_entries.append({
                "timestamp": timestamp,
                "timecode": timecode,
                "visual_type": visual_type,
                "description": f"Video frame at {timecode}",
                "confidence": confidence
            })
            
        return visual_entries
    
    def process_single_video(self, video_id: str) -> Dict:
        """Process single video"""
        print(f"\n=== Processing {video_id} ===")
        
        result = {
            "video_id": video_id,
            "segments": [],
            "visual_content": [],
            "transcript_length": 0,
            "metadata": {}
        }
        
        video_path = self.download_video(video_id)
        if not video_path:
            print(f"  FAILED: Could not download {video_id}")
            return result
        
        print(f"  Video size: {video_path.stat().st_size:,} bytes")
        
        segments = self.transcribe_video(video_path)
        result["segments"] = segments
        result["segments_count"] = len(segments)
        result["transcript_length"] = sum(len(s.get('text', '')) for s in segments)
        
        visual_content = self.extract_visual_timestamps(video_path)
        result["visual_content"] = visual_content
        result["num_visual_entries"] = len(visual_content)
        
        output_file = self.processed_dir / f"{video_id}_processed.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"  OK: segments={result['segments_count']}, visuals={result['num_visual_entries']}")
        return result
    
    def process_batch(self, video_ids: List[str]) -> Dict:
        """Process batch of videos"""
        batch_result = {
            "total": len(video_ids),
            "processed": 0,
            "failed": 0,
            "videos": []
        }
        
        for i, video_id in enumerate(video_ids, 1):
            print(f"\n--- [{i}/{len(video_ids)}] ---")
            try:
                result = self.process_single_video(video_id)
                batch_result["videos"].append(result)
                batch_result["processed"] += 1
            except Exception as e:
                print(f"  FAILED: {e}")
                batch_result["failed"] += 1
        
        return batch_result


if __name__ == "__main__":
    output_dir = "/home/ml/smb_processor"
    channel_url = "https://www.youtube.com/@smbcapital/videos"
    
    processor = SMBAlternativeProcessor(output_dir)
    
    print("=" * 60)
    print("STEP 1: Scraping YouTube channel for video IDs")
    print("=" * 60)
    all_video_ids = processor.scrape_channel(channel_url)
    
    processed_ids = set()
    for f in processor.processed_dir.glob("*_processed.json"):
        vid = f.name.replace('_processed.json', '')
        processed_ids.add(vid)
    
    print(f"\nAlready processed: {len(processed_ids)}")
    to_process = [vid for vid in all_video_ids if vid not in processed_ids]
    print(f"To process: {len(to_process)}")
    
    batch_size = min(20, len(to_process))
    batch_to_process = to_process[:batch_size]
    print(f"\nProcessing batch of {batch_size} videos...")
    
    result = processor.process_batch(batch_to_process)
    
    print(f"\n{'=' * 60}")
    print("BATCH COMPLETE")
    print(f"{'=' * 60}")
    print(f"Processed: {result['processed']}")
    print(f"Failed: {result['failed']}")
