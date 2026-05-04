"""
Temporal Client Interface for v5.0

For Temporal SDK 1.27.x - synchronous workflow pattern.
Programmatically start workflow executions.
Used by YouTube monitor and external triggers.
"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from temporalio.client import Client
from orchestration.workflows import ProcessNewVideo


class TemporalClient:
    """Client for starting and managing Temporal workflows."""
    
    def __init__(self, host: str = "localhost:7233", namespace: str = "default"):
        self.host = host
        self.namespace = namespace
        self._client = None
    
    async def connect(self):
        """Establish connection to Temporal Server."""
        self._client = await Client.connect(
            self.host,
            namespace=self.namespace
        )
        return self._client
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._client is not None
    
    async def start_video_processing(self, video_url: str) -> str:
        """
        Start ProcessNewVideo workflow for a YouTube URL.
        
        Args:
            video_url: YouTube URL (e.g., "https://youtube.com/watch?v=abc123")
            
        Returns:
            str: Workflow execution ID
        """
        if not self._client:
            await self.connect()
        
        video_id = video_url.split('=')[-1] if '=' in video_url else video_url
        workflow_id = f"process-{video_id}"
        
        handle = await self._client.start_workflow(
            ProcessNewVideo.run,
            video_url,
            id=workflow_id,
            task_queue="smb-knowledge-base-v5",
        )
        
        print(f"Started workflow {workflow_id} for {video_url}")
        return workflow_id
    
    async def get_workflow_result(self, workflow_id: str) -> dict:
        """Get result from a completed workflow."""
        if not self._client:
            await self.connect()
        
        handle = self._client.get_workflow_handle(workflow_id)
        result = await handle.result()
        return result
    
    async def list_workflows(self, state: str = "running") -> list:
        """List workflows by state."""
        if not self._client:
            await self.connect()
        
        workflows = []
        async for workflow in self._client.list_workflows():
            workflows.append({
                'id': workflow.id,
                'status': str(workflow.status),
                'start_time': workflow.start_time
            })
        
        return workflows


async def main():
    """CLI interface for Temporal client."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Temporal Client for SMB Knowledge Base")
    parser.add_argument("command", choices=["start", "result", "list"])
    parser.add_argument("--url", help="YouTube URL for start command")
    parser.add_argument("--id", help="Workflow ID for result command")
    parser.add_argument("--host", default="localhost:7233")
    
    args = parser.parse_args()
    
    client = TemporalClient(host=args.host)
    await client.connect()
    
    if args.command == "start":
        if not args.url:
            print("Error: --url is required for start command")
            return
        workflow_id = await client.start_video_processing(args.url)
        print(f"Workflow started: {workflow_id}")
    
    elif args.command == "result":
        if not args.id:
            print("Error: --id is required for result command")
            return
        result = await client.get_workflow_result(args.id)
        print(f"Result: {result}")
    
    elif args.command == "list":
        workflows = await client.list_workflows()
        for wf in workflows[:10]:
            print(f"[{wf['status']}] {wf['id']}")


if __name__ == "__main__":
    asyncio.run(main())
