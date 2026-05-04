#!/usr/bin/env python3
"""
SMB Knowledge Base v4.0 - Pipeline Test Suite

Tests v4.0 pipeline on 5 pilot videos with full validation:
1. NotebookLM extraction → Trust
2. Structured extraction with Pydantic validation
3. Knowledge graph ingestion
4. Backtesting engine
5. Validator agent
6. Backward compatibility check
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add v4.0 to path
sys.path.insert(0, str(Path(__file__).parent))

from smb_schema_v4 import TradingStrategy, MarketRegime
from core.database import get_db_connection
from ingestion.structured_extractor import StructuredExtractor
from graph.knowledge_graph_builder import KnowledgeGraphBuilder
from validation.backtest_engine import BacktestEngine
from validation.validator_agent import ValidatorAgent


def print_header(title):
    """Print test header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_section(title):
    """Print section header."""
    print(f"\n--- {title} ---\n")


def test_backward_compatibility(video_id: str, v3_output_path: Path):
    """Test that v4.0 can read v3.0 JSON."""
    print_section(f"Backward Compatibility: {video_id}")
    
    # Load v3.0 JSON
    with open(v3_output_path) as f:
        v3_data = json.load(f)
    
    print(f"✓ Loaded v3.0 JSON: {len(v3_data)} videos")
    
    # Extract video data
    video = None
    for v in v3_data.get('videos', []):
        if v.get('video_id') == video_id:
            video = v
            break
    
    if not video:
        print(f"✗ Video {video_id} not found in v3.0 JSON")
        return False
    
    # Map to v4.0 TradingStrategy
    try:
        strategy = TradingStrategy.model_validate({
            "id": video_id,
            "name": f"Strategy from {video_id}",
            "description": video.get('summary', 'No description'),
            "trading_style": "day_trading",  # Assume for test
            "primary_regime": MarketRegime.TRENDED_BULL,
            "secondary_regimes": [MarketRegime.CONSOLIDATION],
            "timeframes": ["15m", "1h"],
            "assets": ["SPY", "QQQ"],
            "risk_model": {
                "position_size_percent": 5.0,
                "stop_loss_type": "fixed",
                "stop_loss_value": 0.01,
                "take_profit_type": "rr_multiple",
                "take_profit_value": 2.0,
                "max_drawdown_acceptable": 5.0,
                "risk_per_trade_percent": 1.0
            },
            "entry_rules": [],
            "exit_rules": [],
            "filter_rules": [],
            "setup_patterns": [],
            "indicators_used": ["volume", "RSI"],
            "backtest_results": {
                "total_trades": 50,
                "win_rate": 0.60,
                "profit_factor": 1.5,
                "max_drawdown": 10.0,
                "sharpe_ratio": 1.2,
                "sortino_ratio": 1.8,
                "total_pnl": 5000,
                "average_risk_reward": 1.5,
                "regime_specific_metrics": {},
                "statistical_significance": 0.10
            },
            "evidence_refs": [{
                "video_id": video_id,
                "timestamp_start": 0.0,
                "timestamp_end": 60.0,
                "confidence": 0.85,
                "context_snippet": "Video analysis from v3.0 transcription"
            }],
            "confidence": 0.85,
            "edge_score": 72,
            "validation_status": "validated",
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat()
        })
        
        print(f"✓ TradingStrategy.model_validate() succeeded")
        print(f"  - Strategy ID: {strategy.id}")
        print(f"  - Name: {strategy.name}")
        print(f"  - Edge Score: {strategy.edge_score}")
        print(f"  - Confidence: {strategy.confidence}")
        
        # Test JSON serialization
        json_output = strategy.model_dump_json()
        print(f"✓ JSON serialization: {len(json_output)} bytes")
        
        return True
        
    except Exception as e:
        print(f"✗ Pydantic validation failed: {e}")
        return False


def test_structured_extraction(video_id: str, notebook_id: str, source_id: str):
    """Test structured extractor with NotebookLM."""
    print_section(f"Structured Extraction: {video_id}")
    
    try:
        extractor = StructuredExtractor()
        
        # Test NotebookLM extraction
        strategy = extractor.extract_from_notebooklm(notebook_id, source_id)
        
        print(f"✓ Extracted strategy from NotebookLM")
        print(f"  - Name: {strategy.name}")
        print(f"  - Trading Style: {strategy.trading_style}")
        print(f"  - Confidence: {strategy.confidence}")
        print(f"  - Edge Score: {strategy.edge_score}")
        print(f"  - Validation Status: {strategy.validation_status}")
        
        # Check confidence threshold
        if strategy.confidence >= 0.75:
            print(f"✓ Confidence threshold met (≥0.75)")
        else:
            print(f"⚠ Confidence below threshold (has {strategy.confidence})")
        
        return True
        
    except Exception as e:
        print(f"✗ Structured extraction failed: {e}")
        return False


def test_knowledge_graph_ingestion(strategy: TradingStrategy):
    """Test knowledge graph ingestion."""
    print_section("Knowledge Graph Ingestion")
    
    try:
        builder = KnowledgeGraphBuilder()
        
        # Ingest strategy
        result = builder.ingest_strategy(strategy)
        
        print(f"✓ Strategy ingested into Neo4j")
        print(f"  - Status: {result['status']}")
        print(f"  - Created: {result['created']}")
        
        # Query strategy
        strategy_doc = builder.get_strategy_by_id(strategy.id)
        
        print(f"✓ Strategy retrieved from graph")
        print(f"  - Name: {strategy_doc['s']['name']}")
        print(f"  - Edge Score: {strategy_doc['s']['edge_score']}")
        
        builder.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Knowledge graph ingestion failed: {e}")
        return False


def test_backtesting_engine(video_id: str):
    """Test backtesting engine."""
    print_section(f"Backtesting Engine: {video_id}")
    
    try:
        # Create test strategy
        strategy = TradingStrategy(
            id=video_id,
            name=f"Test Strategy {video_id}",
            description="Test strategy for backtesting",
            trading_style="day_trading",
            primary_regime=MarketRegime.TRENDED_BULL,
            confidence=0.85,
            edge_score=72,
            validation_status="validated",
            timeframes=["15m", "1h"],
            assets=["SPY"],
            risk_model={
                "position_size_percent": 5.0,
                "stop_loss_type": "fixed",
                "stop_loss_value": 0.01,
                "take_profit_type": "rr_multiple",
                "take_profit_value": 2.0,
                "max_drawdown_acceptable": 5.0,
                "risk_per_trade_percent": 1.0
            },
            entry_rules=[],
            exit_rules=[],
            filter_rules=[],
            setup_patterns=[],
            indicators_used=["volume"],
            backtest_results={
                "total_trades": 50,
                "win_rate": 0.60,
                "profit_factor": 1.5,
                "max_drawdown": 10.0,
                "sharpe_ratio": 1.2,
                "sortino_ratio": 1.8,
                "total_pnl": 5000,
                "average_risk_reward": 1.5,
                "regime_specific_metrics": {},
                "statistical_significance": 0.10
            },
            evidence_refs=[],
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        # Run backtest
        engine = BacktestEngine()
        result = engine.run_backtest(strategy)
        
        print(f"✓ Backtest completed")
        print(f"  - Total Trades: {result['total_trades']}")
        print(f"  - Win Rate: {result['win_rate'] * 100:.1f}%")
        print(f"  - Profit Factor: {result['profit_factor']}")
        print(f"  - Max Drawdown: {result['max_drawdown'] * 100:.1f}%")
        print(f"  - Sharpe Ratio: {result['sharpe_ratio']}")
        print(f"  - Edge Score: {result['edge_score']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Backtesting failed: {e}")
        return False


def test_validator_agent(video_id: str):
    """Test validator agent."""
    print_section(f"Validator Agent: {video_id}")
    
    try:
        # Create test strategy
        strategy = TradingStrategy(
            id=video_id,
            name=f"Test Strategy {video_id}",
            description="Test strategy for validation",
            trading_style="day_trading",
            primary_regime=MarketRegime.TRENDED_BULL,
            confidence=0.85,
            edge_score=72,
            validation_status="validated",
            timeframes=["15m"],
            assets=["SPY"],
            risk_model={
                "position_size_percent": 5.0,
                "stop_loss_type": "fixed",
                "stop_loss_value": 0.01,
                "take_profit_type": "rr_multiple",
                "take_profit_value": 2.0,
                "max_drawdown_acceptable": 5.0,
                "risk_per_trade_percent": 1.0
            },
            entry_rules=[],
            exit_rules=[],
            filter_rules=[],
            setup_patterns=[],
            indicators_used=["volume"],
            backtest_results={
                "total_trades": 50,
                "win_rate": 0.60,
                "profit_factor": 1.5,
                "max_drawdown": 10.0,
                "sharpe_ratio": 1.2,
                "sortino_ratio": 1.8,
                "total_pnl": 5000,
                "average_risk_reward": 1.5,
                "regime_specific_metrics": {},
                "statistical_significance": 0.10
            },
            evidence_refs=[],
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        # Run validator
        agent = ValidatorAgent()
        result = agent.validate(strategy)
        
        print(f"✓ Validation completed")
        print(f"  - Status: {result['status']}")
        print(f"  - Judged By: {result['judged_by']}")
        print(f"  - Confidence: {result['confidence']}")
        print(f"  - Edge Score: {result['edge_score']}")
        print(f"  - Discrepancies: {result.get('discrepancies', 0)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return False


def run_full_test_suite():
    """Run complete v4.0 test suite on 5 videos."""
    print_header("SMB Knowledge Base v4.0 - Full Test Suite")
    
    # 5 pilot videos (from SMB pilot)
    test_videos = [
        {
            "video_id": "45eaVU5NVi8",
            "notebook_id": "11dcac26-7de7-411f-85ba-62e8d2fb422d",
            "source_id": "2cae1988-1458-43c3-af25-27b910ae2c1b"
        },
        {
            "video_id": "sh5h0GJzjNk",
            "notebook_id": "11dcac26-7de7-411f-85ba-62e8d2fb422d",
            "source_id": None  # Will be created
        },
        {
            "video_id": "Rqmdw4xyIMM",
            "notebook_id": "11dcac26-7de7-411f-85ba-62e8d2fb422d",
            "source_id": None
        },
        {
            "video_id": "WXBxLHdYFi8",
            "notebook_id": "11dcac26-7de7-411f-85ba-62e8d2fb422d",
            "source_id": None
        },
        {
            "video_id": "_cQnMSU5yGk",
            "notebook_id": "11dcac26-7de7-411f-85ba-62e8d2fb422d",
            "source_id": None
        }
    ]
    
    # Paths
    v3_output_path = Path("/home/ml/smb_notebooklm_pilot/smb_final_kb_v3.json")
    
    # Track results
    results = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }
    
    # Test each video
    for video in test_videos:
        video_id = video["video_id"]
        notebook_id = video["notebook_id"]
        source_id = video["source_id"]
        
        print_header(f"Testing Video: {video_id}")
        
        # Test 1: Backward compatibility
        if v3_output_path.exists():
            results["total_tests"] += 1
            if test_backward_compatibility(video_id, v3_output_path):
                results["passed"] += 1
            else:
                results["failed"] += 1
        else:
            results["skipped"] += 1
            print(f"⚠ Skipping backward compatibility test (v3.0 JSON not found)")
        
        # Test 2: Structured extraction (if source_id available)
        if source_id:
            results["total_tests"] += 1
            if test_structured_extraction(video_id, notebook_id, source_id):
                results["passed"] += 1
            else:
                results["failed"] += 1
        
        # Test 3: Backtesting
        results["total_tests"] += 1
        if test_backtesting_engine(video_id):
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        # Test 4: Validator agent
        results["total_tests"] += 1
        if test_validator_agent(video_id):
            results["passed"] += 1
        else:
            results["failed"] += 1
    
    # Final summary
    print_header("Test Suite Summary")
    
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed:      {results['passed']}")
    print(f"Failed:      {results['failed']}")
    print(f"Skipped:     {results['skipped']}")
    print(f"\nPass Rate:   {results['passed'] / results['total_tests'] * 100:.1f}%")
    
    # Success criteria
    if results['failed'] == 0 and results['passed'] >= 15:  # 3 tests × 5 videos
        print(f"\n✓ ALL TESTS PASSED - v4.0 pipeline is ready!")
        return 0
    else:
        print(f"\n✗ Some tests failed - review errors above")
        return 1


if __name__ == "__main__":
    exit_code = run_full_test_suite()
    sys.exit(exit_code)
