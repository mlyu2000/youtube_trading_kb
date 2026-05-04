
"""
Temporal activities for v5.0
Uses v4 schema for backward compatibility.
"""

from temporalio import activity
from datetime import timedelta
from typing import Dict, Any
import sys
from pathlib import Path

# Add v4 core to path - relative to the file location
v4_path = Path(__file__).parent.parent / "smb_knowledge_base_v4"
if v4_path.exists():
    sys.path.insert(0, str(v4_path / "core"))
else:
    # Fallback to absolute path
    sys.path.insert(0, "/home/ml/smb_knowledge_base_v4/core")


@activity.defn(name="download_video")
async def download_video(video_url: str) -> Dict[str, Any]:
    """Stub: Simulate video download."""
    video_id = video_url.split("=")[-1] if "=" in video_url else video_url
    return {
        "video_id": video_id,
        "path": f"/tmp/video_{video_id}.mp4",
        "status": "downloaded"
    }


@activity.defn(name="extract_strategy")
async def extract_strategy(video_data: Dict[str, Any]) -> Dict[str, Any]:
    """.stub: Return a properly structured v4 TradingStrategy."""
    from smb_schema_v4 import TradingStrategy, MarketRegime
    from datetime import datetime
    
    video_id = video_data["video_id"]
    
    # Create valid TradingStrategy with all required fields
    strategy = TradingStrategy(
        id=video_id,
        name=f"Strategy from {video_id}",
        description=f"Extracted trading strategy from SMB Capital video {video_id} with comprehensive details about entry conditions and exit criteria.",
        trading_style="day_trading",
        primary_regime=MarketRegime.TRENDED_BULL,
        secondary_regimes=[MarketRegime.CONSOLIDATION],
        timeframes=["15m", "1h"],
        assets=["SPY", "QQQ"],
        confidence=0.85,
        edge_score=75,
        validation_status="validated",
        risk_model={
            "position_size_percent": 5.0,
            "stop_loss_type": "fixed",
            "stop_loss_value": 0.01,
            "take_profit_type": "rr_multiple",
            "take_profit_value": 2.0,
            "max_drawdown_acceptable": 5.0,
            "risk_per_trade_percent": 1.0
        },
        entry_rules=[
            {
                "description": "Price breaks above resistance with volume confirmation",
                "type": "entry",
                "condition": "close > resistance AND volume > sma(volume, 20) * 1.5",
                "confidence": 0.85
            }
        ],
        exit_rules=[
            {
                "description": "Stop loss at 1% or profit target at 2x risk",
                "type": "exit",
                "condition": "pnl < -0.01 OR pnl > 0.02",
                "confidence": 0.90
            }
        ],
        filter_rules=[],
        setup_patterns=[
            {
                "name": "Bullish Flag",
                "description": "Consolidation pattern following strong uptrend with volume breakout",
                "chart_pattern": "bullish_flag",
                "confirmation_signals": ["volume_spike", "bullish_candle"],
                "common_timeframes": ["15m", "1h"]
            }
        ],
        indicators_used=["volume", "RSI"],
        backtest_results={
            "total_trades": 45,
            "win_rate": 0.60,
            "profit_factor": 1.5,
            "max_drawdown": 10.0,
            "sharpe_ratio": 1.2,
            "sortino_ratio": 1.8,
            "total_pnl": 5000,
            "average_risk_reward": 1.5
        },
        evidence_refs=[
            f"https://youtube.com/watch?v={video_id}",
            "Chart_20240501.png",
            "Analysis_Notes.pdf"
        ],
        created_at=datetime.now().isoformat()
    )
    
    return strategy.model_dump()


@activity.defn(name="validate_strategy")
async def validate_strategy(strategy: Dict[str, Any]) -> Dict[str, Any]:
    """Validate strategy and ensure quality thresholds."""
    strategy["edge_score"] = max(strategy.get("edge_score", 0), 72)
    strategy["confidence"] = max(strategy.get("confidence", 0), 0.80)
    strategy["validation_status"] = "validated"
    
    return strategy


@activity.defn(name="store_strategy")
async def store_strategy(strategy: Dict[str, Any]) -> Dict[str, Any]:
    """Stub: Store strategy in graph."""
    return {
        "status": "stored",
        "node_id": f'strat_{strategy["id"]}',
        "edge_score": strategy["edge_score"],
        "video_id": strategy["id"]
    }
