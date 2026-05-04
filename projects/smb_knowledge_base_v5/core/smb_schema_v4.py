"""
Pydantic v2 schema for TradingStrategy - v4.0 compatible
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MarketRegime(str, Enum):
    TRENDED_BULL = "trended_bull"
    TRENDED_BEAR = "trended_bear"
    CONSOLIDATION = "consolidation"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    GAP_UP = "gap_up"
    GAP_DOWN = "gap_down"


class RiskModel(BaseModel):
    position_size_percent: float = Field(..., ge=0.0, le=100.0)
    stop_loss_type: str
    stop_loss_value: float
    take_profit_type: str
    take_profit_value: float
    max_drawdown_acceptable: float
    risk_per_trade_percent: float


class Rule(BaseModel):
    description: str
    type: str  # "entry", "exit", "filter", "risk"
    condition: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class SetupPattern(BaseModel):
    name: str
    description: str
    chart_pattern: str
    confirmation_signals: List[str]
    common_timeframes: List[str]


class BacktestResult(BaseModel):
    total_trades: int
    win_rate: float
    profit_factor: float
    max_drawdown: float
    Sharpe_ratio: float
    Sortino_ratio: float
    total_pnl: float
    average_risk_reward: float
    regime_specific_metrics: Dict[MarketRegime, Dict[str, float]]
    statistical_significance: float  # Monte Carlo p-value


class EvidenceRef(BaseModel):
    video_id: str
    timestamp_start: float
    timestamp_end: float
    confidence: float
    context_snippet: str


class TradingStrategy(BaseModel):
    """Primary data model for v4.0 - fully structured and validated"""
    
    id: str = Field(alias="strategy_id")
    name: str
    description: str
    trading_style: str
    primary_regime: MarketRegime
    secondary_regimes: List[MarketRegime]
    timeframes: List[str]
    assets: List[str]
    risk_model: RiskModel
    entry_rules: List[Rule]
    exit_rules: List[Rule]
    filter_rules: List[Rule]
    setup_patterns: List[SetupPattern]
    indicators_used: List[str]
    backtest_results: Optional[BacktestResult] = None
    evidence_refs: List[EvidenceRef]
    confidence: float = Field(..., ge=0.0, le=1.0)
    edge_score: int = Field(..., ge=0, le=100)
    validation_status: str  # "unverified", "validated", "flagged"
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: Optional[datetime] = None


def model_validate_strategy(data: Dict[str, Any]) -> TradingStrategy:
    """Validate and convert dict to TradingStrategy"""
    return TradingStrategy.model_validate(data)
