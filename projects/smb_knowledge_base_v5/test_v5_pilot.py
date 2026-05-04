"""Test script for v5.0 end-to-end testing with 5 pilot videos."""

import asyncio
import sys
sys.path.insert(0, '/home/ml/youtube_trading_kb/projects/smb_knowledge_base_v5')

from orchestration.simple_workflow import run_simple_pipeline


async def test_v5_with_pilot_videos():
    """Test v5.0 with all 5 pilot videos."""
    
    videos = [
        "45eaVU5NVi8",
        "sh5h0GJzjNk", 
        "Rqmdw4xyIMM",
        "WXBxLHdYFi8",
        "_cQnMSU5yGk"
    ]
    
    print("=== SMB Knowledge Base v5.0 Pilot Test (Simple Pipeline) ===")
    print()
    
    results = []
    for video_id in videos:
        url = f"https://youtube.com/watch?v={video_id}"
        print(f"[{video_id}] Starting pipeline...")
        
        try:
            result = await run_simple_pipeline(url)
            status = result.get("status", "error")
            edge_score = result.get("edge_score", "N/A")
            
            results.append({
                "video_id": video_id,
                "status": status,
                "edge_score": edge_score,
                "result": result
            })
            
            status_icon = "PASS" if status == "completed" else "FAIL"
            print(f"[{video_id}] {status_icon} Status: {status}, Edge Score: {edge_score}")
        except Exception as e:
            results.append({
                "video_id": video_id,
                "status": "error",
                "error": str(e)
            })
            print(f"[{video_id}] FAIL Error: {e}")
    
    print()
    print("=== Summary ===")
    passed = sum(1 for r in results if r.get("status") == "completed")
    print(f"Passed: {passed}/{len(results)}")
    
    for r in results:
        status_icon = "PASS" if r["status"] == "completed" else "FAIL"
        print(f"{status_icon} {r['video_id']}: {r['status']} (edge_score: {r.get('edge_score', 'N/A')})")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_v5_with_pilot_videos())
