#!/usr/bin/env python3
"""
SMB Capital Batch Video Processor
Processes multiple videos in batch with progress tracking
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import time

from PIL import Image
import whisper


class SMBBatchProcessor:
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
        
    def download_video(self, video_id: str) -> Optional[Path]:
        output = self.raw_dir / f"{video_id}.mp4"
        if output.exists():
            return output
        print(f"  Downloading {video_id}...")
        url = f"https://www.youtube.com/watch?v={video_id}"
        result = subprocess.run([
            'yt-dlp', '-f', 'best[ext=mp4]', '-o', str(output), url
        ], capture_output=True, text=True, timeout=300)
        return output if result.returncode == 0 else None
        
    def transcribe_video(self, video_path: Path) -> List[Dict]:
        audio_path = self.raw_dir / f"{video_path.stem}.mp3"
        if not audio_path.exists():
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
        frames_path = self.frames_dir / video_path.stem
        frames_path.mkdir(parents=True, exist_ok=True)
        
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', str(video_path)
        ], capture_output=True, text=True)
        duration = float(result.stdout.strip()) if result.stdout.strip() else 0
        
        num_frames = int(duration // interval)
        if num_frames == 0:
            return []
            
        print(f"  Extracting {num_frames} frames (1 per {interval}s)...")
        
        timestamp_pattern = str(frames_path / "frame_%04d.jpg")
        subprocess.run([
            'ffmpeg', '-i', str(video_path), '-vf', f'fps=1/{interval}',
            '-q:v', '2', timestamp_pattern
        ], capture_output=True, text=True)
        
        visual_entries = []
        frames_found = list(frames_path.glob("frame_*.jpg"))
        
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
            
        print(f"  Extracted {len(visual_entries)} visual timestamps")
        return visual_entries
    
    def get_video_metadata(self, video_id: str) -> Dict:
        url = f"https://www.youtube.com/watch?v={video_id}"
        result = subprocess.run([
            'yt-dlp', '--dump-json', url
        ], capture_output=True, text=True)
        try:
            return json.loads(result.stdout)
        except:
            return {"id": video_id, "title": "Unknown", "duration": 0}
    
    def process_single_video(self, video_id: str) -> Dict:
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
        
        result["metadata"] = self.get_video_metadata(video_id)
        print(f"  Title: {result['metadata'].get('title', 'Unknown')}")
        
        segments = self.transcribe_video(video_path)
        result["segments"] = segments
        result["segments_count"] = len(segments)
        result["transcript_length"] = sum(len(s['text']) for s in segments)
        
        visual_content = self.extract_visual_timestamps(video_path)
        result["visual_content"] = visual_content
        result["num_visual_entries"] = len(visual_content)
        
        output_file = self.processed_dir / f"{video_id}_processed.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"  OK: segments={result['segments_count']}, visuals={result['num_visual_entries']}")
        return result
    
    def process_batch(self, video_ids: List[str]) -> Dict:
        batch_result = {
            "total": len(video_ids),
            "processed": 0,
            "failed": 0,
            "videos": []
        }
        
        for i, video_id in enumerate(video_ids, 1):
            print(f"\n--- Batch {i}/{len(video_ids)} ---")
            try:
                result = self.process_single_video(video_id)
                batch_result["videos"].append(result)
                batch_result["processed"] += 1
            except Exception as e:
                print(f"  FAILED: {e}")
                batch_result["failed"] += 1
        
        return batch_result


if __name__ == "__main__":
    batch_file = "/home/ml/smb_batch_5_to_process.txt"
    with open(batch_file, 'r') as f:
        video_ids = [line.strip() for line in f if line.strip()]
    
    print(f"Batch processing {len(video_ids)} videos...")
    
    processor = SMBBatchProcessor()
    result = processor.process_batch(video_ids)
    
    print(f"\n\n=== BATCH COMPLETE ===")
    print(f"Total: {result['total']}")
    print(f"Processed: {result['processed']}")
    print(f"Failed: {result['failed']}")
    
    with open("/home/ml/smb_batch_2_results.json", 'w') as f:
        json.dump(result, f, indent=2)
    print("Results saved to /home/ml/smb_batch_2_results.json")
