#!/usr/bin/env python3
"""
SMB Capital Video Processor
Processes videos without transcripts using local Whisper
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import hashlib
import time

from PIL import Image
import whisper

class SMBVideoProcessor:
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
            print(f"  Already downloaded: {video_id}")
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
            print(f"  Extracting audio...")
            result = subprocess.run([
                'ffmpeg', '-i', str(video_path), '-vn', '-acodec', 'libmp3lame',
                '-ar', '16000', '-ac', '1', str(audio_path)
            ], capture_output=True, text=True)
        
        print(f"  Transcribing with Whisper (base model)...")
        start_time = time.time()
        result = self.model.transcribe(str(audio_path), language='en', task='transcribe')
        elapsed = time.time() - start_time
        print(f"  Transcribed in {elapsed:.1f}s, {len(result['segments'])} segments")
        
        return [{'start': s['start'], 'end': s['end'], 'text': s['text']}
                for s in result['segments']]
                
    def capture_frames(self, video_path: Path, interval=10.0) -> List[Dict]:
        print(f"  Capturing frames every {interval}s...")
        result = subprocess.run([
            'ffmpeg', '-i', str(video_path),
            '-vf', f'fps=1/{interval}',
            '-start_number', '0',
            str(self.frames_dir / f"{video_path.stem}_%04d.jpg")
        ], capture_output=True, text=True)
        if result.returncode != 0:
            return []
        frames = sorted(self.frames_dir.glob(f"{video_path.stem}_*.jpg"))
        return [{'frame_num': i, 'timestamp': i * interval, 'path': str(f)}
                for i, f in enumerate(frames)]
                
    def analyze_frame(self, frame_path: str, timestamp: float) -> Dict:
        frame = {'timestamp': timestamp, 'visual_type': 'unknown', 'confidence': 0.0}
        try:
            img = Image.open(frame_path)
            w, h = img.size
            if w > h * 1.5:
                frame['visual_type'] = 'chart_or_diagram'
                frame['description'] = 'Wide-format chart or diagram'
                frame['confidence'] = 0.7
            elif w == h:
                frame['visual_type'] = 'square_preview'
                frame['description'] = 'Square mobile preview'
                frame['confidence'] = 0.8
            else:
                frame['visual_type'] = 'host_explanation'
                frame['description'] = 'Portrait host explanation'
                frame['confidence'] = 0.6
            frame['image_hash'] = hashlib.md5(
                bytes(list(img.getdata())[:1000])
            ).hexdigest()[:16]
        except Exception as e:
            frame['error'] = str(e)
        return frame
        
    def integrate_transcript(self, transcript: List[Dict], frame: Dict) -> Dict:
        ts = frame['timestamp']
        relevant = [t['text'][:200] for t in transcript if t['start'] <= ts <= t['end']]
        return {
            'timestamp': frame['timestamp'],
            'timecode': f"{int(ts//60):02d}:{int(ts%60):02d}",
            'visual_type': frame['visual_type'],
            'description': frame['description'],
            'confidence': frame['confidence'],
            'transcript_context': relevant[0] if relevant else None
        }
        
    def process(self, video_id: str) -> Dict:
        print(f"\n{'='*50}\nProcessing: {video_id}\n{'='*50}")
        result = {'video_id': video_id, 'status': 'pending', 'segments': [], 'visual_entries': []}
        
        video_path = self.download_video(video_id)
        if not video_path:
            result['status'] = 'download_failed'
            return result
            
        transcript = self.transcribe_video(video_path)
        result['segments'] = transcript
        print(f"✓ Transcribed: {len(transcript)} segments, {sum(len(s['text']) for s in transcript)} chars")
        
        frames = self.capture_frames(video_path, interval=10.0)
        for frame in frames:
            analysis = self.analyze_frame(frame['path'], frame['timestamp'])
            entry = self.integrate_transcript(transcript, analysis)
            result['visual_entries'].append(entry)
            
        result['frames_captured'] = len(frames)
        result['status'] = 'completed'
        print(f"✓ Processed: {len(frames)} frames with visual timestamps")
        
        json_path = self.processed_dir / f"{video_id}_processed.json"
        with open(json_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✓ Saved: {json_path}")
        return result


def main():
    test_ids = [
        'sh5h0GJzjNk',
        'K2e1Sdpfv7s',
        'Jniwt90PUS4',
    ]
    
    processor = SMBVideoProcessor()
    
    for i, vid_id in enumerate(test_ids, 1):
        print(f"\n[{i}/{len(test_ids)}] Processing {vid_id}")
        result = processor.process(vid_id)
        print(f"Status: {result['status']}")
        time.sleep(2)


if __name__ == "__main__":
    main()
