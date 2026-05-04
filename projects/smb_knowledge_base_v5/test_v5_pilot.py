"""Test script for v5.0 end-to-end testing with 5 pilot videos."""

import asyncio
import sys
sys.path.insert(0, '/home/ml/youtube_trading_kb/projects/smb_knowledge_base_v5')

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
    
    print("=== SMB Knowledge Base v5.0 Pilot Test ===")
    print()
    
    client = TemporalClient()
    await client.connect()
    
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
            print(f"[{video_id}] PASS Workflow started: {wf_id}")
        except Exception as e:
            results.append({
                "video_id": video_id,
                "status": "error",
                "error": str(e)
            })
            print(f"[{video_id}] FAIL Error: {e}")
    
    print()
    print("=== Summary ===")
    passed = sum(1 for r in results if r.get("status") == "started")
    print(f"Started: {passed}/{len(results)}")
    
    for r in results:
        status_icon = "PASS" if r["status"] == "started" else "FAIL"
        print(f"{status_icon} {r['video_id']}: {r['status']}")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_v5_with_pilot_videos())
