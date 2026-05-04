"""
SMB Knowledge Base v4.0 - Core Data Models

Pydantic v2 schema with proper validationconstraints,
JSON serialization, and Neo4j compatibility.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class MarketRegime(str, Enum):
    """Market regimes that affect strategy performance."""
    TRENDED_BULL = "trended_bull"
    TRENDED_BEAR = "trended_bear"
    CONSOLIDATION = "consolidation"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    GAP_UP = "gap_up"
    GAP_DOWN = "gap_down"


class RiskModel(BaseModel):
    """Risk parameters for a trading strategy."""
    model_config = ConfigDict(extra='forbid')
    
    position_size_percent: float = Field(
        ..., 
        ge=0.0, 
        le=100.0,
        description="Percent of portfolio allocated per position"
    )
    stop_loss_type: str = Field(
        ..., 
        description="Type of stop loss (fixed, trailing, ATR-based)"
    )
    stop_loss_value: float = Field(
        ..., 
        ge=0.0,
        description="Stop loss value (percent or price level)"
    )
    take_profit_type: str = Field(
        ..., 
        description="Type of take profit (fixed, trailing, RR multiple)"
    )
    take_profit_value: float = Field(
        ..., 
        ge=0.0,
        description="Take profit value (percent or price level)"
    )
    max_drawdown_acceptable: float = Field(
        ..., 
        ge=0.0, 
        le=100.0,
        description="Maximum acceptable drawdown threshold"
    )
    risk_per_trade_percent: float = Field(
        ..., 
        ge=0.0, 
        le=100.0,
        description="Percent of portfolio risked per trade"
    )


class Rule(BaseModel):
    """A single trading rule (entry, exit, or filter)."""
    model_config = ConfigDict(extra='forbid')
    
    description: str = Field(
        ..., 
        description="Natural language description of the rule"
    )
    type: str = Field(
        ..., 
        pattern="^(entry|exit|filter|risk)$",
        description="Rule type"
    )
    condition: str = Field(
        ..., 
        description="Executable condition (pseudocode or Telegram/TradingView syntax)"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confidence that this rule works consistently"
    )


class SetupPattern(BaseModel):
    """A specific chart pattern or setup that triggers entries."""
    model_config = ConfigDict(extra='forbid')
    
    name: str = Field(
        ..., 
        description="Name of the pattern (e.g., ' Bullish Flag', 'Double Bottom')"
    )
    description: str = Field(
        ..., 
        description="Detailed description of the pattern"
    )
    chart_pattern: str = Field(
        ..., 
        description="Standard chart pattern name"
    )
    confirmation_signals: List[str] = Field(
        ..., 
        min_length=1,
        description="Signals that confirm the pattern (volume, RSI, candlestick, etc.)"
    )
    common_timeframes: List[str] = Field(
        ..., 
        min_length=1,
        description="Timeframes where this pattern is most reliable"
    )


class BacktestResult(BaseModel):
    """Complete backtest results for a strategy."""
    model_config = ConfigDict(extra='forbid')
    
    total_trades: int = Field(
        ..., 
        ge=1,
        description="Total number of trades in backtest"
    )
    win_rate: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Percentage of winning trades"
    )
    profit_factor: float = Field(
        ..., 
        ge=0.0,
        description="Gross profit / Gross loss"
    )
    max_drawdown: float = Field(
        ..., 
        ge=0.0, 
        le=100.0,
        description="Maximum drawdown in the backtest"
    )
    sharpe_ratio: float = Field(
        ..., 
        description="Sharpe ratio of returns"
    )
    sortino_ratio: float = Field(
        ..., 
        description="Sortino ratio (downside deviation)"
    )
    total_pnl: float = Field(
        ..., 
        description="Total profit/loss in backtest"
    )
    average_risk_reward: float = Field(
        ..., 
        description="Average R:R ratio of trades"
    )
    regime_specific_metrics: Dict[MarketRegime, Dict[str, float]] = Field(
        ..., 
        description="Backtest metrics segmented by market regime"
    )
    statistical_significance: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Monte Carlo p-value (lower = more significant)"
    )


class EvidenceRef(BaseModel):
    """Reference to the original video evidence for a strategy component."""
    model_config = ConfigDict(extra='forbid')
    
    video_id: str = Field(
        ..., 
        description="YouTube video ID where this is discussed"
    )
    timestamp_start: float = Field(
        ..., 
        ge=0.0,
        description="Start timestamp in seconds"
    )
    timestamp_end: float = Field(
        ..., 
        ge=0.0,
        description="End timestamp in seconds"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confidence in the extracted information"
    )
    context_snippet: str = Field(
        ..., 
        description="Short excerpt from transcript or chart"
    )


class TradingStrategy(BaseModel):
    """
    Primary data model for v4.0 - fully structured and validated trading strategy.
    
    This model replaces the free-text JSON from v3.0 with rigorously validated
    Pydantic schemas that can serialize to JSON and Neo4j.
    """
    model_config = ConfigDict(extra='forbid')
    
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique strategy identifier"
    )
    name: str = Field(
        ..., 
        min_length=3, 
        max_length=100,
        description="Strategy name"
    )
    description: str = Field(
        ..., 
        min_length=50,
        description="Comprehensive strategy description"
    )
    trading_style: str = Field(
        ..., 
        pattern="^(day_trading|swing_trading|position_trading|scalping|momentum|mean_reversion)$",
        description="High-level trading approach"
    )
    primary_regime: MarketRegime = Field(
        ..., 
        description="Primary market regime where strategy shines"
    )
    secondary_regimes: List[MarketRegime] = Field(
        ..., 
        min_length=0,
        max_length=6,
        description="Other regimes where strategy performs adequately"
    )
    timeframes: List[str] = Field(
        ..., 
        min_length=1,
        max_length=5,
        description="Timeframes where strategy operates (e.g., '1m', '5m', '15m', '1h', 'daily')"
    )
    assets: List[str] = Field(
        ..., 
        min_length=1,
        max_length=20,
        description="Assets traded (e.g., 'SPY', 'QQQ', 'TSLA', 'BTC-USD')"
    )
    risk_model: RiskModel = Field(
        ..., 
        description="Risk parameters and rules"
    )
    entry_rules: List[Rule] = Field(
        ..., 
        min_length=1,
        max_length=10,
        description="Entry conditions"
    )
    exit_rules: List[Rule] = Field(
        ..., 
        min_length=1,
        max_length=10,
        description="Exit conditions"
    )
    filter_rules: List[Rule] = Field(
        ..., 
        min_length=0,
        max_length=5,
        description="Pre-entry filters (market context, volume, etc.)"
    )
    setup_patterns: List[SetupPattern] = Field(
        ..., 
        min_length=1,
        max_length=5,
        description="Chart patterns that trigger entries"
    )
    indicators_used: List[str] = Field(
        ..., 
        min_length=0,
        max_length=20,
        description="Indicators used (technical, volume, sentiment)"
    )
    backtest_results: BacktestResult = Field(
        ..., 
        description="Complete backtest results"
    )
    evidence_refs: List[EvidenceRef] = Field(
        ..., 
        min_length=1,
        description="References to source videos"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Overall confidence in strategy validity"
    )
    edge_score: int = Field(
        ..., 
        ge=0, 
        le=100,
        description="Strategy health score (0-100)"
    )
    validation_status: str = Field(
        ..., 
        pattern="^(unverified|validated|flagged|production_ready)$",
        description="Current validation state"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp"
    )
    
    def model_post_init(self, __context):
        """Post-init hook to update timestamps and validate consistency."""
        self.last_updated = datetime.utcnow()
        # Add more post-init validation if needed
        return self


# Factory function for creating strategy from v3 JSON
def create_strategy_from_v3(v3_data: dict) -> TradingStrategy:
    """Convert v3 JSON data to v4 TradingStrategy model."""
    # This will be implemented in migration/migrate_v3_to_v4.py
    # For now, returns empty with example structure
    raise NotImplementedError("Use migration/migrate_v3_to_v4.py")


# Validation tests
if __name__ == "__main__":
    # Test 1: Valid strategy creation
    sample_data = {
        "name": "Support/Resistance Breakout",
        "description": "Day trading strategy focusing on support/resistance breakouts with volume confirmation.进入具有成交量确认的支持/阻力突破。",
        "trading_style": "day_trading",
        "primary_regime": MarketRegime.TRENDED_BULL,
        "secondary_regimes": [MarketRegime.TRENDED_BEAR, MarketRegime.CONSOLIDATION],
        "timeframes": ["15m", "1h"],
        "assets": ["SPY", "QQQ"],
        "risk_model": {
            "position_size_percent": 5.0,
            "stop_loss_type": "fixed",
            "stop_loss_value": 0.01,  # 1%
            "take_profit_type": "rr_multiple",
            "take_profit_value": 2.0,
            "max_drawdown_acceptable": 5.0,
            "risk_per_trade_percent": 1.0
        },
        "entry_rules": [
            {
                "description": "Price breaks above resistance with volume spike",
                "type": "entry",
                "condition": "close > resistance AND volume > SMA(volume, 20) * 1.5",
                "confidence": 0.85
            }
        ],
        "exit_rules": [
            {
                "description": "Stop loss at support or 1% loss",
                "type": "exit",
                "condition": "low < stop_loss_level OR pnl < -0.01",
                "confidence": 0.90
            }
        ],
        "filter_rules": [],
        "setup_patterns": [
            {
                "name": " Bullish Flag",
                "description": "Consolidation after strong uptrend",
                "chart_pattern": "bullish_flag",
                "confirmation_signals": ["volume_spike", "bullish_candle"],
                "common_timeframes": ["15m", "1h"]
            }
        ],
        "indicators_used": ["volume", "RSI", "support_resistance", "SMA"],
        "backtest_results": {
            "total_trades": 150,
            "win_rate": 0.65,
            "profit_factor": 1.8,
            "max_drawdown": 8.5,
            "sharpe_ratio": 1.5,
            "sortino_ratio": 2.1,
            "total_pnl": 25000,
            "average_risk_reward": 1.5,
            "regime_specific_metrics": {
                "trended_bull": {"win_rate": 0.72, "sharpe_ratio": 1.8},
                "trended_bear": {"win_rate": 0.58, "sharpe_ratio": 0.9}
            },
            "statistical_significance": 0.01
        },
        "evidence_refs": [
            {
                "video_id": "45eaVU5NVi8",
                "timestamp_start": 120.0,
                "timestamp_end": 180.0,
                "confidence": 0.90,
                "context_snippet": "Key support/resistance levels with volume confirmation"
            }
        ],
        "confidence": 0.88,
        "edge_score": 75,
        "validation_status": "validated"
    }
    
    strategy = TradingStrategy.model_validate(sample_data)
    print("✓ Test 1 PASSED: Valid strategy created")
    
    # Test 2: JSON serialization
    json_output = strategy.model_dump_json(indent=2)
    print(f"✓ Test 2 PASSED: JSON serialization ({len(json_output)} bytes)")
    
    # Test 3: Nested model access
    assert strategy.risk_model.stop_loss_value == 0.01
    assert strategy.entry_rules[0].confidence == 0.85
    print("✓ Test 3 PASSED: Nested model access works")
    
    print("\n=== ALL TESTS PASSED ===")
    print(f"Strategy ID: {strategy.id}")
    print(f"Strategy Name: {strategy.name}")
    print(f"Edge Score: {strategy.edge_score}")
    print(f"Validation Status: {strategy.validation_status}")
