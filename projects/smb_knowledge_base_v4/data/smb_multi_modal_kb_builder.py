#!/usr/bin/env python3
"""
SMB Capital YouTube Knowledge Base Builder - Multi-Modal Approach
"""

import json
import os
import time
from pathlib import Path
from googleapiclient.discovery import build

try:
    from whisper import load_model
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False


class SMBKnowledgeBaseBuilder:
    def __init__(self, api_key, output_dir='/home/ml/smb_processor'):
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.youtube = build("youtube", "v3", developerKey=api_key)
        self.kb = []
        self.kb_path = Path(output_dir) / 'smb_knowledge_base_multi_modal.json'
        self.stats_path = Path(output_dir) / 'smb_knowledge_base_stats.json'
        self.whisper_model = None
        self.loaded_video_ids = set()
        
        if self.kb_path.exists():
            with open(self.kb_path) as f:
                existing_kb = json.load(f)
                self.kb = existing_kb
                for video in self.kb:
                    self.loaded_video_ids.add(video['id'])
                print(f"Loaded {len(self.loaded_video_ids)} existing videos")
    
    def _load_whisper_model(self):
        if self.whisper_model is None and WHISPER_AVAILABLE:
            self.whisper_model = load_model("base")
        return self.whisper_model
    
    def get_video_metadata(self, video_id):
        try:
            request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics", id=video_id
            )
            response = request.execute()
            if response['items']:
                item = response['items'][0]
                return {
                    'id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'publishedAt': item['snippet']['publishedAt'],
                    'duration': item['contentDetails']['duration'],
                    'viewCount': item['statistics'].get('viewCount', 0),
                    'likeCount': item['statistics'].get('likeCount', 0)
                }
        except Exception as e:
            print(f"Error for {video_id}: {e}")
        return None
    
    def download_video_with_yt_dlp(self, video_id, output_dir):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f"{output_dir}/{video_id}.%(ext)s",
            'postprocessors': [{'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav', 'preferredquality': '192'}],
            'quiet': True, 'no_warnings': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
            for ext in ['wav', 'mp3']:
                files = list(Path(output_dir).glob(f"{video_id}*.{ext}"))
                if files:
                    return str(files[0])
        except Exception as e:
            print(f"Download error for {video_id}: {e}")
        return None
    
    def transcribe_with_whisper(self, audio_path):
        model = self._load_whisper_model()
        if model is None:
            return None
        try:
            result = model.transcribe(audio_path, fp16=False)
            return result['segments']
        except Exception as e:
            print(f"Transcribe error: {e}")
        return None
    
    def extract_visual_timestamps(self, segments):
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
    
    def process_video(self, video_id, download_dir):
        if video_id in self.loaded_video_ids:
            return None
        
        metadata = self.get_video_metadata(video_id)
        if not metadata:
            return None
        
        segments = []
        visual_entries = []
        
        if download_dir and YT_DLP_AVAILABLE:
            audio_path = self.download_video_with_yt_dlp(video_id, download_dir)
            if audio_path:
                segments = self.transcribe_with_whisper(audio_path)
                try:
                    Path(audio_path).unlink(missing_ok=True)
                except:
                    pass
        
        if segments:
            visual_entries = self.extract_visual_timestamps(segments)
        
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
        
        self.kb.append(video_entry)
        self.loaded_video_ids.add(video_id)
        return video_entry
    
    def save_kb(self):
        with open(self.kb_path, 'w') as f:
            json.dump(self.kb, f, indent=2, default=str)
        
        total_segments = sum(len(v.get('transcript_segments', [])) for v in self.kb)
        total_visuals = sum(len(v.get('visual_entries', [])) for v in self.kb)
        
        visual_types = {}
        for v in self.kb:
            for entry in v.get('visual_entries', []):
                t = entry.get('visual_type', 'unknown')
                visual_types[t] = visual_types.get(t, 0) + 1
        
        stats = {
            'total_videos': len(self.kb),
            'total_transcript_segments': total_segments,
            'total_visual_entries': total_visuals,
            'visual_type_distribution': visual_types
        }
        with open(self.stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"Saved: {len(self.kb)} videos, {total_segments} segments, {total_visuals} visuals")


def main():
    api_key = os.environ.get('YOUTUBE_API_KEY', 'AIzaSy...1eMo')
    video_ids_file = Path('/home/ml/smb_all_video_ids.txt')
    
    if not video_ids_file.exists():
        print("ERROR: Video IDs file not found")
        return
    
    with open(video_ids_file) as f:
        video_ids = [line.strip() for line in f if line.strip()]
    
    print(f"Processing {len(video_ids)} videos...")
    
    builder = SMBKnowledgeBaseBuilder(api_key)
    download_dir = '/home/ml/video_downloads'
    Path(download_dir).mkdir(exist_ok=True)
    
    batch_size = 25
    for i in range(0, len(video_ids), batch_size):
        batch = video_ids[i:i+batch_size]
        print(f"\n=== Batch {i//batch_size + 1} ===")
        
        for vid_id in batch:
            try:
                result = builder.process_video(vid_id, download_dir)
                if result:
                    print(f"  processed: {vid_id} ({len(result['transcript_segments'])} segments, {len(result['visual_entries'])} visuals)")
                time.sleep(0.5)
            except Exception as e:
                print(f"  error: {vid_id}")
        
        builder.save_kb()


if __name__ == '__main__':
    main()
