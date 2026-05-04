
"""Edge score calculation for trading strategies"""


def calculate_edge_score(backtest_results: Dict[str, Any]) -> float:
    """
    Calculate edge score based on backtest metrics.
    
    Edge score factors:
    - Win rate (40%)
    - Profit factor (20%)
    - Sharpe ratio (20%)
    - Max drawdown (20%)
    
    Returns:
        Edge score from 0-100
    """
    if not backtest_results:
        return 50  # Default neutral score
    
    # Extract metrics
    win_rate = backtest_results.get('win_rate', 0.5)
    profit_factor = backtest_results.get('profit_factor', 1.0)
    sharpe_ratio = backtest_results.get('sharpe_ratio', 0)
    max_drawdown = backtest_results.get('max_drawdown', 0)
    
    # Calculate component scores (normalized 0-100)
    win_rate_score = win_rate * 100
    profit_factor_score = min(profit_factor * 50, 100)  # PF 2.0 = 100
    sharpe_score = min((sharpe_ratio + 3) / 6 * 100, 100)  # Sharpe 3+ = 100
    drawdown_penalty = max(0, (max_drawdown - 10) / 5 * -20)  # High DD reduces score
    
    # Weighted combination
    edge_score = (
        win_rate_score * 0.40 +
        profit_factor_score * 0.20 +
        sharpe_score * 0.20 +
        drawdown_penalty * 0.20
    )
    
    return max(0, min(100, edge_score))


def calculate_edge_score_v2(backtest_results: Dict[str, Any]) -> float:
    """Alternative edge score calculation using expectancy."""
    if not backtest_results:
        return 50
    
    expectancy = backtest_results.get('average_risk_reward', 1.0)
    win_rate = backtest_results.get('win_rate', 0.5)
    
    # Higher expectancy + reasonable win rate = higher edge
    edge = (expectancy * 20) + (win_rate * 40) + 20
    
    return max(0, min(100, edge))
