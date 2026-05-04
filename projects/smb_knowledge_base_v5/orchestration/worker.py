"""
Temporal Worker Configuration for SMB Knowledge Base v5.0

For Temporal SDK 1.27.x - synchronous workflow pattern.
"""

import asyncio
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from temporalio import worker
from temporalio.client import Client

from orchestration.workflows import (
    ProcessNewVideo,
    ExtractAndValidateStrategy,
    RunBacktest,
    UpdateKnowledgeGraph,
    RunSwarmAnalysis,
)


async def main():
    """Main entry point for Temporal worker."""
    
    # Configuration
    temporal_host = "localhost:7233"
    task_queue = "smb-knowledge-base-v5"
    
    # Connect to Temporal Server
    client = await Client.connect(
        temporal_host,
        namespace="default"
    )
    
    # Create worker
    worker_instance = worker.Worker(
        client=client,
        task_queue=task_queue,
        workflows=[
            ProcessNewVideo,
            ExtractAndValidateStrategy,
            RunBacktest,
            UpdateKnowledgeGraph,
            RunSwarmAnalysis,
        ],
        max_concurrent_workflow_tasks=10,
        max_concurrent_activities=20,
        max_cached_workflows=100,
    )
    
    print(f"Starting Temporal worker on {task_queue}")
    print(f"Connected to: {temporal_host}")
    
    # Run worker
    await worker_instance.run()


if __name__ == "__main__":
    asyncio.run(main())
