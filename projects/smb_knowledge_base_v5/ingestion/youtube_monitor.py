"""
YouTube Monitor for v5.0

Monitors SMB Capital YouTube channel for new uploads.
Auto-triggers Temporal workflow on new videos.
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys
import time
from typing import Dict, List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestration.client import TemporalClient


# YouTube API constants
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
CHANNEL_ID = "UC_x5XG1OV2P6uZZ5FSM9Ttw"  # SMB Capital channel ID
CHECK_INTERVAL = 1800  # 30 minutes (target latency)


class YouTubeMonitor:
    """Monitors YouTube channel for new uploads."""
    
    def __init__(self, channel_id: str, check_interval: int = 1800):
        self.channel_id = channel_id
        self.check_interval = check_interval
        self.service = None
        self.seen_videos: List[str] = []
        self.temporal_client = None
        
    def authenticate(self) -> bool:
        """Authenticate with YouTube API."""
        creds = None
        
        # Load existing credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        try:
            self.service = build('youtube', 'v3', credentials=creds)
            return True
        except HttpError as e:
            print(f"YouTube API error: {e}")
            return False
    
    def get_latest_video(self) -> Optional[Dict]:
        """Get the most recent video from channel."""
        try:
            # Get uploads playlist
            channels_response = self.service.channels().list(
                part='contentDetails',
                id=self.channel_id
            ).execute()
            
            if not channels_response['items']:
                return None
            
            uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get latest video from playlist
            playlist_response = self.service.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=1
            ).execute()
            
            if not playlist_response['items']:
                return None
            
            video = playlist_response['items'][0]['snippet']
            return {
                'video_id': video['resourceId']['videoId'],
                'title': video['title'],
                'description': video['description'],
                'published_at': video['publishedAt']
            }
        
        except HttpError as e:
            print(f"YouTube API error: {e}")
            return None
    
    def check_new_videos(self) -> List[Dict]:
        """Check for new videos since last check."""
        latest = self.get_latest_video()
        
        if not latest:
            return []
        
        # Deduplication: check if we've seen this video
        if latest['video_id'] in self.seen_videos:
            return []
        
        # Mark as seen
        self.seen_videos.append(latest['video_id'])
        
        return [latest]
    
    async def process_video(self, video: Dict) -> str:
        """Process a new video through Temporal workflow."""
        if not self.temporal_client:
            self.temporal_client = TemporalClient()
            await self.temporal_client.connect()
        
        video_url = f"https://youtube.com/watch?v={video['video_id']}"
        workflow_id = await self.temporal_client.start_video_processing(video_url)
        
        print(f"Started processing: {video['title']}")
        print(f"Workflow ID: {workflow_id}")
        
        return workflow_id
    
    async def run_monitor(self):
        """Run continuous monitoring loop."""
        print(f"Starting YouTube monitor for channel {self.channel_id}")
        print(f"Check interval: {self.check_interval} seconds")
        
        # Authenticate
        if not self.authenticate():
            print("Failed to authenticate with YouTube API")
            return
        
        # Load seen videos from file if exists
        seen_file = Path('seen_videos.pkl')
        if seen_file.exists():
            with open(seen_file, 'rb') as f:
                self.seen_videos = pickle.load(f)
        
        print("Monitor running... Press Ctrl+C to stop")
        
        try:
            while True:
                new_videos = self.check_new_videos()
                
                if new_videos:
                    print(f"Found {len(new_videos)} new video(s)")
                    for video in new_videos:
                        await self.process_video(video)
                        
                        # Save updated seen list
                        with open(seen_file, 'wb') as f:
                            pickle.dump(self.seen_videos, f)
                else:
                    print(f"[{datetime.now().isoformat()}] No new videos. Next check in {self.check_interval}s")
                
                # Wait for next check
                time.sleep(self.check_interval)
        
        except KeyboardInterrupt:
            print("\nMonitor stopped by user")
        
        finally:
            # Save final state
            with open(seen_file, 'wb') as f:
                pickle.dump(self.seen_videos, f)


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="YouTube Monitor for SMB Knowledge Base")
    parser.add_argument("--channel-id", default="UC_x5XG1OV2P6uZZ5FSM9Ttw")
    parser.add_argument("--interval", type=int, default=1800)
    parser.add_argument("--once", action="store_true", help="Check once and exit")
    
    args = parser.parse_args()
    
    monitor = YouTubeMonitor(args.channel_id, args.interval)
    
    if not monitor.authenticate():
        print("Authentication failed")
        return 1
    
    if args.once:
        new_videos = monitor.check_new_videos()
        if new_videos:
            print(f"Found {len(new_videos)} new videos")
            for v in new_videos:
                print(f"  - {v['title']} (https://youtube.com/watch?v={v['video_id']})")
        else:
            print("No new videos")
        return 0
    else:
        await monitor.run_monitor()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
