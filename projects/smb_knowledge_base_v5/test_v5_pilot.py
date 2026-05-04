"""
Test script for v5.0 end-to-end testing with 5 pilot videos.
"""

import asyncio
import sys
sys.path.insert(0, '/home/ml')
from orchestration.client import TemporalClient


async def test_v5_with_pilot_videos():
    """Test v5.0 with all 5 pilot videos."""
    
    videos = [
        "45eaVU5NVi8",
        "sh5h0GJzjNk", 
        "Rqmdw4xyIMM",
        "WXBxLHdYFi8",
        "_cQnMSU5yGk"
    ]
    
    client = TemporalClient()
    await client.connect()
    
    print("=== SMB Knowledge Base v5.0 Pilot Test ===\n")
    
    results = []
    for video_id in videos:
        url = f"https://youtube.com/watch?v={video_id}"
        print(f"[{video_id}] Starting workflow...")
        
        try:
            wf_id = await client.start_video_processing(url)
            results.append({
                "video_id": video_id,
                "status": "started",
                "workflow_id": wf_id
            })
            print(f"[{video_id}] ✓ Workflow started: {wf_id}")
        except Exception as e:
            results.append({
                "video_id": video_id,
                "status": "error",
                "error": str(e)
            })
            print(f"[{video_id}] ✗ Error: {e}")
    
    print("\n=== Summary ===")
    for r in results:
        status_icon = "✓" if r["status"] == "started" else "✗"
        print(f"{status_icon} {r['video_id']}: {r['status']}")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_v5_with_pilot_videos())
