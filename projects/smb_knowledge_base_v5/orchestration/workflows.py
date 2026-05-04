"""
Temporal.io Workflows for SMB Knowledge Base v5.0

For Temporal SDK 1.27.x - synchronous workflow pattern.
Orchestrates strategy extraction using NotebookLM and validation.
All workflows are observable in Temporal UI.
"""

from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
from typing import List, Optional, Dict, Any


@workflow.defn
class ProcessNewVideo:
    """Process a single YouTube video through the full pipeline."""
    
    @workflow.run
    async def run(self, video_url: str) -> dict:
        """
        Main entry point for video processing.
        
        Args:
            video_url: YouTube URL to process
            
        Returns:
            dict: Processing results with strategy and metrics
        """
        # Import activities
        from .activities import download_video, extract_strategy, validate_strategy, store_strategy
        
        # Step 1: Download/transcribe video
        video_data = await workflow.execute_activity(
            download_video,
            video_url,
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        # Step 2: Extract strategy
        strategy = await workflow.execute_activity(
            extract_strategy,
            video_data,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )
        
        # Step 3: Validate strategy
        validated = await workflow.execute_activity(
            validate_strategy,
            strategy,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )
        
        # Step 4: Store in graph
        graph_result = await workflow.execute_activity(
            store_strategy,
            validated,
            start_to_close_timeout=timedelta(minutes=3),
            retry_policy=RetryPolicy(maximum_attempts=2)
        )
        
        return {
            **validated,
            "graph_status": graph_result
        }
    
    @workflow.signal
    async def cancel_processing(self):
        """Signal to cancel ongoing processing."""
        self._cancelled = True
    
    @workflow.query
    def processing_status(self) -> str:
        """Query current processing status."""
        return getattr(self, '_status', 'idle')


@workflow.defn
class ExtractAndValidateStrategy:
    """Extract strategy and validate with backtesting."""
    
    @workflow.run
    async def run(self, video_path: str) -> dict:
        """Extract strategy from video, validate, return backtest results."""
        from ..ingestion.structured_extractor import extract_strategy
        
        strategy = await workflow.execute_activity(
            extract_strategy,
            video_path,
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        validated = await workflow.execute_activity(
            validate_strategy,
            strategy,
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        return {
            'strategy': validated.model_dump(),
            'edge_score': validated.edge_score,
            'confidence': validated.confidence
        }


@workflow.defn
class RunBacktest:
    """Run backtest on existing strategy."""
    
    @workflow.run
    async def run(self, strategy_dict: Dict[str, Any]) -> dict:
        """
        Run vectorbt backtest on a stored strategy.
        
        Args:
            strategy_dict: Serialized TradingStrategy from v4 schema
            
        Returns:
            dict: Backtest metrics including expectancy, Sharpe ratio, max drawdown
        """
        from ..core.smb_schema_v4 import TradingStrategy
        
        strategy = TradingStrategy.model_validate(strategy_dict)
        
        result = await workflow.execute_activity(
            self._run_backtest,
            strategy,
            start_to_close_timeout=timedelta(minutes=30)
        )
        
        return result
    
    async def _run_backtest(self, strategy: 'TradingStrategy') -> dict:
        """Internal backtest method - will be implemented in Phase 3."""
        # Phase 3 will implement the actual backtest with vectorbt
        return {
            "status": "pending_phase3",
            "strategy_id": strategy.id
        }


@workflow.defn
class UpdateKnowledgeGraph:
    """Update Neo4j graph with new strategy."""
    
    @workflow.run
    async def run(self, strategy_dict: Dict[str, Any]) -> dict:
        """
        Store strategy in Neo4j and Qdrant.
        
        Args:
            strategy_dict: TradingStrategy model dump
            
        Returns:
            dict: Node ID and store results
        """
        store_result = await workflow.execute_activity(
            self._store_strategy,
            strategy_dict,
            start_to_close_timeout=timedelta(minutes=5)
        )
        return store_result
    
    async def _store_strategy(self, strategy_dict: dict) -> dict:
        """Internal store method."""
        from ..core.smb_schema_v4 import TradingStrategy
        strategy = TradingStrategy.model_validate(strategy_dict)
        from orchestration.activities import store_strategy
        return store_strategy(strategy)
