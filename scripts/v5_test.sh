#!/bin/bash
# v5_test.sh - Test v5.0 implementation with 5 pilot videos

set -e

echo "=== SMB Knowledge Base v5.0 Pilot Test ==="

# Define videos
VIDEOS=(
    "45eaVU5NVi8"  # "Day Trading Setup - My Favorite Pattern"
    "sh5h0GJzjNk"  # "Swing Trading Strategy - High Edge"
    "Rqmdw4xyIMM"  # "Scalping Techniques - Quick Profits"
    "WXBxLHdYFi8"  # "Position Sizing - Risk Management"
    "_cQnMSU5yGk"  # "Market Regime Analysis"
)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Temporal is accessible
echo "Checking Temporal connectivity..."
if ! nc -z localhost 7233 2>/dev/null; then
    echo -e "${YELLOW}Temporal not running on localhost:7233${NC}"
    echo "Starting Temporal server..."
    docker ps | grep temporal || docker run -d -p 7233:7233 -p 8233:8233 --name temporal temporalio/auto-setup:latest
    sleep 5
fi

echo -e "${GREEN}Temporal is accessible${NC}"

# Check if worker is running
WORKER_PID=$(pgrep -f "orchestration/worker.py" || true)

if [ -z "$WORKER_PID" ]; then
    echo -e "${YELLOW}Temporal worker not running - starting it...${NC}"
    cd /home/ml/smb_knowledge_base_v5
    python orchestration/worker.py > /tmp/temporal_worker.log 2>&1 &
    WORKER_PID=$!
    echo "Worker PID: $WORKER_PID"
    sleep 3
fi

# Create test script
cat > /tmp/v5_test.py << 'PYEOF'
import asyncio
import sys
sys.path.insert(0, '/home/ml')
from orchestration.client import TemporalClient

async def test_videos(videos):
    client = TemporalClient()
    await client.connect()
    
    results = []
    for video_id in videos:
        url = f"https://youtube.com/watch?v={video_id}"
        workflow_id = f"process-{video_id}"
        
        print(f"\nProcessing: {video_id}")
        
        try:
            wf_id = await client.start_video_processing(url)
            print(f"  Workflow ID: {wf_id}")
            results.append({
                "video_id": video_id,
                "status": "started",
                "workflow_id": wf_id
            })
        except Exception as e:
            print(f"  Error: {e}")
            results.append({
                "video_id": video_id,
                "status": "error",
                "error": str(e)
            })
    
    return results

async def main():
    videos = sys.argv[1:] if len(sys.argv) > 1 else [
        "45eaVU5NVi8", "sh5h0GJzjNk", "Rqmdw4xyIMM", "WXBxLHdYFi8", "_cQnMSU5yGk"
    ]
    results = await test_videos(videos)
    print(f"\nResults: {results}")

if __name__ == "__main__":
    asyncio.run(main())
PYEOF

echo "Running test with 5 pilot videos..."
python /tmp/v5_test.py "${VIDEOS[@]}"

# Test clawteam integration
echo ""
echo -e "${GREEN}Testing ClawTeam integration...${NC}"
clawteam --help > /dev/null 2>&1 && echo -e "${GREEN}ClawTeam CLI available${NC}" || echo -e "${RED}ClawTeam CLI not found${NC}"

# Test Temporal client
echo ""
echo -e "${GREEN}Testing Temporal client...${NC}"
cd /home/ml/smb_knowledge_base_v5
python orchestration/client.py --help > /dev/null 2>&1 && echo -e "${GREEN}Temporal client available${NC}" || echo -e "${RED}Temporal client not working${NC}"

echo ""
echo "=== Test Complete ==="
echo ""
echo "To check workflow status:"
echo "  cd ~/smb_knowledge_base_v5 && python orchestration/client.py list"
echo ""
echo "To get specific workflow result:"
echo "  python orchestration/client.py result --id process-45eaVU5NVi8"
