"""
Simple workflow for pilot testing without Temporal server.
Direct execution version of Phase 2 pipeline.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.activities import (
    download_video, extract_strategy, validate_strategy, store_strategy
)


async def run_simple_pipeline(video_url: str) -> dict:
    """
    Run simple pipeline without Temporal server.
    For local testing of Phase 2 components.
    """
    print(f"[Pipeline] Starting: {video_url}")
    
    # Step 1: Download/transcribe
    video_data = await download_video(video_url)
    print(f"[Pipeline] Downloaded: {video_data.get('status')}")
    
    if video_data.get("status") != "transcribed":
        return {"error": "Failed to transcribe video", "video_data": video_data}
    
    # Step 2: Extract strategy
    strategy = await extract_strategy(video_data)
    print(f"[Pipeline] Strategy extracted: {strategy.get('id')}")
    
    # Step 3: Validate strategy
    validated = await validate_strategy(strategy)
    print(f"[Pipeline] Validation: {validated.get('validation_status')}")
    
    if not validated.get("quality_gates_passed"):
        return {"error": "Quality gates not passed", "validation": validated}
    
    # Step 4: Store strategy
    stored = await store_strategy(validated)
    print(f"[Pipeline] Stored: {stored.get('status')}")
    
    return {
        "status": "completed",
        "video_url": video_url,
        "video_id": strategy.get("id"),
        "edge_score": strategy.get("edge_score"),
        "confidence": strategy.get("confidence"),
        "validation_status": validated.get("validation_status")
    }


async def main():
    """Main test function."""
    videos = [
        "https://youtube.com/watch?v=45eaVU5NVi8",
        "https://youtube.com/watch?v=sh5h0GJzjNk",
        "https://youtube.com/watch?v=Rqmdw4xyIMM",
        "https://youtube.com/watch?v=WXBxLHdYFi8",
        "https://youtube.com/watch?v=_cQnMSU5yGk"
    ]
    
    print("=== SMB Knowledge Base v5.0 Pilot Test ===")
    print()
    
    for url in videos:
        result = await run_simple_pipeline(url)
        status_icon = "PASS" if result.get("status") == "completed" else "FAIL"
        print(f"[{status_icon}] {url}")
        print(f"    Status: {result.get('status')}")
        if result.get("error"):
            print(f"    Error: {result.get('error')}")
        print()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
