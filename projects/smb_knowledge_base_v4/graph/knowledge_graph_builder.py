"""
SMB Knowledge Base v4.0 - Knowledge Graph Builder

Builds Neo4j knowledge graph from TradingStrategy objects.

Nodes: Trader, Strategy, SetupPattern, Indicator, RiskRule, Video, MarketRegime
Edges: HAS_STRATEGY, USES_INDICATOR, HAS_SETUP, EVIDENCED_BY, REGIME_FAVORABLE, etc.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

from neo4j import GraphDatabase, Driver
from smb_schema_v4 import TradingStrategy, MarketRegime

# Configure logging
logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    """Builds and manages the Neo4j knowledge graph for trading strategies."""
    
    def __init__(self, driver: Optional[Driver] = None):
        self._driver = driver
        self._establish_connection()
    
    def _establish_connection(self):
        """Connect to Neo4j."""
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "neo4j_password")
        
        self._driver = GraphDatabase.driver(
            uri,
            auth=(user, password)
        )
        logger.info("Neo4j connection established")
    
    def close(self):
        """Close Neo4j connection."""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j connection closed")
    
    # ==================== NODE CREATION ====================
    
    def create_trader_node(self, trader_name: str, trader_description: str = None) -> str:
        """Create or merge a Trader node."""
        query = """
        MERGE (t:Trader {name: $trader_name})
        ON CREATE SET t.description = $description, t.created_at = datetime()
        ON MATCH SET t.last_updated = datetime()
        RETURN t.name AS name, t.id AS id
        """
        
        with self._driver.session() as session:
            result = session.run(query, trader_name=trader_name, description=trader_description)
            return result.single()
    
    def create_strategy_node(self, strategy: TradingStrategy) -> str:
        """Create or merge a Strategy node."""
        query = """
        MERGE (s:Strategy {id: $strategy_id})
        ON CREATE SET 
            s.name = $name,
            s.description = $description,
            s.trading_style = $trading_style,
            s.confidence = $confidence,
            s.edge_score = $edge_score,
            s.validation_status = $validation_status,
            s.created_at = $created_at,
            s.last_updated = $last_updated
        ON MATCH SET 
            s.last_updated = datetime(),
            s.confidence = $confidence,
            s.edge_score = $edge_score
        RETURN s.id AS id, s.name AS name
        """
        
        with self._driver.session() as session:
            result = session.run(query, **{
                "strategy_id": strategy.id,
                "name": strategy.name,
                "description": strategy.description,
                "trading_style": strategy.trading_style,
                "confidence": strategy.confidence,
                "edge_score": strategy.edge_score,
                "validation_status": strategy.validation_status,
                "created_at": strategy.created_at.isoformat(),
                "last_updated": strategy.last_updated.isoformat()
            })
            return result.single()
    
    def create_setup_pattern_node(self, pattern: SetupPattern, strategy_id: str) -> str:
        """Create or merge a SetupPattern node."""
        query = """
        MERGE (p:SetupPattern {name: $pattern_name, strategy_id: $strategy_id})
        ON CREATE SET 
            p.description = $description,
            p.chart_pattern = $chart_pattern,
            p.confirmation_signals = $confirmation_signals,
            p.common_timeframes = $common_timeframes,
            p.created_at = datetime()
        ON MATCH SET p.last_updated = datetime()
        RETURN p.name AS name, p.id AS id
        """
        
        with self._driver.session() as session:
            result = session.run(query, **{
                "pattern_name": pattern.name,
                "strategy_id": strategy_id,
                "description": pattern.description,
                "chart_pattern": pattern.chart_pattern,
                "confirmation_signals": pattern.confirmation_signals,
                "common_timeframes": pattern.common_timeframes
            })
            return result.single()
    
    def create_indicator_node(self, indicator_name: str, description: str = None) -> str:
        """Create or merge an Indicator node."""
        query = """
        MERGE (i:Indicator {name: $indicator_name})
        ON CREATE SET i.description = $description, i.created_at = datetime()
        ON MATCH SET i.last_updated = datetime()
        RETURN i.name AS name, i.id AS id
        """
        
        with self._driver.session() as session:
            result = session.run(query, indicator_name=indicator_name, description=description)
            return result.single()
    
    def create_risk_rule_node(self, risk_model, strategy_id: str) -> str:
        """Create or merge a RiskRule node."""
        query = """
        MERGE (r:RiskRule {strategy_id: $strategy_id})
        ON CREATE SET 
            r.position_size_percent = $position_size_percent,
            r.stop_loss_type = $stop_loss_type,
            r.stop_loss_value = $stop_loss_value,
            r.take_profit_type = $take_profit_type,
            r.take_profit_value = $take_profit_value,
            r.max_drawdown_acceptable = $max_drawdown_acceptable,
            r.risk_per_trade_percent = $risk_per_trade_percent,
            r.created_at = datetime()
        ON MATCH SET r.last_updated = datetime()
        RETURN r.strategy_id AS strategy_id, r.id AS id
        """
        
        with self._driver.session() as session:
            result = session.run(query, **{
                "strategy_id": strategy_id,
                "position_size_percent": risk_model.position_size_percent,
                "stop_loss_type": risk_model.stop_loss_type,
                "stop_loss_value": risk_model.stop_loss_value,
                "take_profit_type": risk_model.take_profit_type,
                "take_profit_value": risk_model.take_profit_value,
                "max_drawdown_acceptable": risk_model.max_drawdown_acceptable,
                "risk_per_trade_percent": risk_model.risk_per_trade_percent
            })
            return result.single()
    
    def create_video_node(self, video_id: str, title: str = None, description: str = None) -> str:
        """Create or merge a Video node."""
        query = """
        MERGE (v:Video {id: $video_id})
        ON CREATE SET 
            v.title = $title,
            v.description = $description,
            v.created_at = datetime()
        ON MATCH SET v.last_updated = datetime()
        RETURN v.id AS id, v.title AS title
        """
        
        with self._driver.session() as session:
            result = session.run(query, video_id=video_id, title=title, description=description)
            return result.single()
    
    def create_market_regime_node(self, regime: MarketRegime) -> str:
        """Create or merge a MarketRegime node."""
        query = """
        MERGE (m:MarketRegime {name: $regime_name})
        ON CREATE SET 
            m.description = $description,
            m.created_at = datetime()
        ON MATCH SET m.last_updated = datetime()
        RETURN m.name AS name, m.id AS id
        """
        
        descriptions = {
            MarketRegime.TRENDED_BULL: "Uptrend with strong momentum",
            MarketRegime.TRENDED_BEAR: "Downtrend with strong momentum",
            MarketRegime.CONSOLIDATION: "Range-bound, sideways trading",
            MarketRegime.HIGH_VOLATILITY: "High volatility, large price swings",
            MarketRegime.LOW_VOLATILITY: "Low volatility, tight ranges",
            MarketRegime.GAP_UP: "Gapping up after market open",
            MarketRegime.GAP_DOWN: "Gapping down after market open"
        }
        
        with self._driver.session() as session:
            result = session.run(query, 
                               regime_name=regime.value,
                               description=descriptions[regime])
            return result.single()
    
    # ==================== EDGE CREATION ====================
    
    def create_has_strategy_edge(self, trader_name: str, strategy_id: str) -> None:
        """CREATE (Trader)-[:HAS_STRATEGY]->(Strategy)"""
        query = """
        MATCH (t:Trader {name: $trader_name})
        MATCH (s:Strategy {id: $strategy_id})
        MERGE (t)-[:HAS_STRATEGY]->(s)
        """
        
        with self._driver.session() as session:
            session.run(query, trader_name=trader_name, strategy_id=strategy_id)
    
    def create_uses_indicator_edge(self, strategy_id: str, indicator_name: str) -> None:
        """CREATE (Strategy)-[:USES_INDICATOR]->(Indicator)"""
        query = """
        MATCH (s:Strategy {id: $strategy_id})
        MATCH (i:Indicator {name: $indicator_name})
        MERGE (s)-[:USES_INDICATOR]->(i)
        """
        
        with self._driver.session() as session:
            session.run(query, strategy_id=strategy_id, indicator_name=indicator_name)
    
    def create_has_setup_edge(self, strategy_id: str, pattern_name: str) -> None:
        """CREATE (Strategy)-[:HAS_SETUP]->(SetupPattern)"""
        query = """
        MATCH (s:Strategy {id: $strategy_id})
        MATCH (p:SetupPattern {name: $pattern_name, strategy_id: $strategy_id})
        MERGE (s)-[:HAS_SETUP]->(p)
        """
        
        with self._driver.session() as session:
            session.run(query, strategy_id=strategy_id, pattern_name=pattern_name)
    
    def create_evidenced_by_edge(self, strategy_id: str, video_id: str, confidence: float) -> None:
        """CREATE (Strategy)-[:EVIDENCED_BY {confidence: $confidence}]->(Video)"""
        query = """
        MATCH (s:Strategy {id: $strategy_id})
        MATCH (v:Video {id: $video_id})
        MERGE (s)-[:EVIDENCED_BY {confidence: $confidence}]->(v)
        """
        
        with self._driver.session() as session:
            session.run(query, strategy_id=strategy_id, video_id=video_id, confidence=confidence)
    
    def create_favorable_regime_edge(self, strategy_id: str, regime_name: str, confidence: float) -> None:
        """CREATE (Strategy)-[:FAVORABLE_IN {confidence: $confidence}]->(MarketRegime)"""
        query = """
        MATCH (s:Strategy {id: $strategy_id})
        MATCH (m:MarketRegime {name: $regime_name})
        MERGE (s)-[:FAVORABLE_IN {confidence: $confidence}]->(m)
        """
        
        with self._driver.session() as session:
            session.run(query, 
                       strategy_id=strategy_id, 
                       regime_name=regime_name,
                       confidence=confidence)
    
    def create_has_risk_rule_edge(self, strategy_id: str) -> None:
        """CREATE (Strategy)-[:HAS_RISK_RULE]->(RiskRule)"""
        query = """
        MATCH (s:Strategy {id: $strategy_id})
        MATCH (r:RiskRule {strategy_id: $strategy_id})
        MERGE (s)-[:HAS_RISK_RULE]->(r)
        """
        
        with self._driver.session() as session:
            session.run(query, strategy_id=strategy_id)
    
    # ==================== FULL STRATEGY INGESTION ====================
    
    def ingest_strategy(self, strategy: TradingStrategy, video_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ingest a complete TradingStrategy into the knowledge graph.
        
        Creates all nodes and edges for the strategy.
        Returns summary of created entities.
        """
        logger.info(f"Ingesting strategy: {strategy.name} (ID: {strategy.id})")
        
        created = {
            "strategies": 0,
            "setups": 0,
            "indicators": 0,
            "risk_rules": 0,
            "videos": 0,
            "regimes": 0
        }
        
        with self._driver.session() as session:
            # Transaction for atomicity
            def create_strategy_tx(tx):
                results = {}
                
                # 1. Create strategy node
                strategy_result = tx.run("""
                    MERGE (s:Strategy {id: $strategy_id})
                    ON CREATE SET 
                        s.name = $name,
                        s.description = $description,
                        s.trading_style = $trading_style,
                        s.confidence = $confidence,
                        s.edge_score = $edge_score,
                        s.validation_status = $validation_status,
                        s.created_at = $created_at,
                        s.last_updated = $last_updated
                    ON MATCH SET 
                        s.last_updated = datetime(),
                        s.confidence = $confidence,
                        s.edge_score = $edge_score
                    RETURN s.id AS id, s.name AS name
                """, **{
                    "strategy_id": strategy.id,
                    "name": strategy.name,
                    "description": strategy.description,
                    "trading_style": strategy.trading_style,
                    "confidence": strategy.confidence,
                    "edge_score": strategy.edge_score,
                    "validation_status": strategy.validation_status,
                    "created_at": strategy.created_at.isoformat(),
                    "last_updated": strategy.last_updated.isoformat()
                })
                results["strategy"] = strategy_result.single()
                created["strategies"] += 1
                
                # 2. Create risk rule node
                risk_result = tx.run("""
                    MERGE (r:RiskRule {strategy_id: $strategy_id})
                    ON CREATE SET 
                        r.position_size_percent = $position_size_percent,
                        r.stop_loss_type = $stop_loss_type,
                        r.stop_loss_value = $stop_loss_value,
                        r.take_profit_type = $take_profit_type,
                        r.take_profit_value = $take_profit_value,
                        r.max_drawdown_acceptable = $max_drawdown_acceptable,
                        r.risk_per_trade_percent = $risk_per_trade_percent,
                        r.created_at = datetime()
                    ON MATCH SET r.last_updated = datetime()
                    RETURN r.strategy_id AS strategy_id
                """, **{
                    "strategy_id": strategy.id,
                    **strategy.risk_model.model_dump()
                })
                results["risk_rule"] = risk_result.single()
                created["risk_rules"] += 1
                
                # 3. Create setup pattern nodes
                for pattern in strategy.setup_patterns:
                    setup_result = tx.run("""
                        MERGE (p:SetupPattern {name: $pattern_name, strategy_id: $strategy_id})
                        ON CREATE SET 
                            p.description = $description,
                            p.chart_pattern = $chart_pattern,
                            p.confirmation_signals = $confirmation_signals,
                            p.common_timeframes = $common_timeframes,
                            p.created_at = datetime()
                        ON MATCH SET p.last_updated = datetime()
                        RETURN p.name AS name
                    """, **{
                        "pattern_name": pattern.name,
                        "strategy_id": strategy.id,
                        **pattern.model_dump()
                    })
                    results[f"setup_{pattern.name}"] = setup_result.single()
                    created["setups"] += 1
                
                # 4. Create indicator nodes
                for indicator in strategy.indicators_used:
                    indicator_result = tx.run("""
                        MERGE (i:Indicator {name: $indicator_name})
                        ON CREATE SET i.created_at = datetime()
                        ON MATCH SET i.last_updated = datetime()
                        RETURN i.name AS name
                    """, indicator_name=indicator)
                    results[f"indicator_{indicator}"] = indicator_result.single()
                    created["indicators"] += 1
                
                # 5. Create market regime nodes
                for regime in [strategy.primary_regime] + strategy.secondary_regimes:
                    regime_result = tx.run("""
                        MERGE (m:MarketRegime {name: $regime_name})
                        ON CREATE SET 
                            m.description = $description,
                            m.created_at = datetime()
                        ON MATCH SET m.last_updated = datetime()
                        RETURN m.name AS name
                    """, 
                        regime_name=regime.value,
                        description=f"{regime.value.replace('_', ' ')} market condition"
                    )
                    results[f"regime_{regime.value}"] = regime_result.single()
                    created["regimes"] += 1
                
                # 6. Create video nodes and evidence edges
                for evidence in strategy.evidence_refs:
                    video_result = tx.run("""
                        MERGE (v:Video {id: $video_id})
                        ON CREATE SET 
                            v.created_at = datetime(),
                            v.youtube_url = 'https://www.youtube.com/watch?v=' + $video_id
                        ON MATCH SET v.last_updated = datetime()
                        RETURN v.id AS id
                    """, video_id=evidence.video_id)
                    results[f"video_{evidence.video_id}"] = video_result.single()
                    created["videos"] += 1
                
                return results
            
            results = session.execute_write(create_strategy_tx)
        
        # Create edges in separate transaction
        self._create_edges(strategy)
        
        logger.info(f"Strategy {strategy.name} ingested successfully")
        return {"status": "success", "created": created, "strategy_id": strategy.id}
    
    def _create_edges(self, strategy: TradingStrategy) -> None:
        """Create all relationships for a strategy."""
        logger.info(f"Creating edges for strategy: {strategy.name}")
        
        with self._driver.session() as session:
            # Strategy has risk rule
            session.run("""
                MATCH (s:Strategy {id: $strategy_id})
                MERGE (s)-[:HAS_RISK_RULE]->(r:RiskRule {strategy_id: $strategy_id})
            """, strategy_id=strategy.id)
            
            # Strategy has setups
            for pattern in strategy.setup_patterns:
                session.run("""
                    MATCH (s:Strategy {id: $strategy_id})
                    MATCH (p:SetupPattern {name: $pattern_name, strategy_id: $strategy_id})
                    MERGE (s)-[:HAS_SETUP]->(p)
                """, strategy_id=strategy.id, pattern_name=pattern.name)
            
            # Strategy uses indicators
            for indicator in strategy.indicators_used:
                session.run("""
                    MATCH (s:Strategy {id: $strategy_id})
                    MATCH (i:Indicator {name: $indicator_name})
                    MERGE (s)-[:USES_INDICATOR]->(i)
                """, strategy_id=strategy.id, indicator_name=indicator)
            
            # Strategy is favorable in market regimes
            for regime in [strategy.primary_regime] + strategy.secondary_regimes:
                session.run("""
                    MATCH (s:Strategy {id: $strategy_id})
                    MATCH (m:MarketRegime {name: $regime_name})
                    MERGE (s)-[:FAVORABLE_IN {confidence: 0.85}]->(m)
                """, strategy_id=strategy.id, regime_name=regime.value)
            
            # Strategy is evidenced by videos
            for evidence in strategy.evidence_refs:
                session.run("""
                    MATCH (s:Strategy {id: $strategy_id})
                    MATCH (v:Video {id: $video_id})
                    MERGE (s)-[:EVIDENCED_BY {confidence: $confidence}]->(v)
                """, 
                    strategy_id=strategy.id,
                    video_id=evidence.video_id,
                    confidence=evidence.confidence
                )
        
        logger.info(f"Edges created for strategy: {strategy.name}")
    
    # ==================== QUERIES ====================
    
    def get_strategy_by_id(self, strategy_id: str) -> Dict[str, Any]:
        """Get a strategy with all related nodes."""
        query = """
        MATCH (s:Strategy {id: $strategy_id})
        OPTIONAL MATCH (s)-[:HAS_RISK_RULE]->(r:RiskRule)
        OPTIONAL MATCH (s)-[:HAS_SETUP]->(p:SetupPattern)
        OPTIONAL MATCH (s)-[:USES_INDICATOR]->(i:Indicator)
        OPTIONAL MATCH (s)-[:FAVORABLE_IN]->(m:MarketRegime)
        OPTIONAL MATCH (s)-[:EVIDENCED_BY]->(v:Video)
        RETURN s, collect(DISTINCT r) AS risk_rules, 
               collect(DISTINCT p) AS setups, 
               collect(DISTINCT i) AS indicators,
               collect(DISTINCT m) AS regimes,
               collect(DISTINCT v) AS videos
        """
        
        with self._driver.session() as session:
            result = session.run(query, strategy_id=strategy_id)
            return result.single()
    
    def get_strategies_by_regime(self, regime_name: str) -> List[Dict[str, Any]]:
        """Get all strategies favorable in a specific market regime."""
        query = """
        MATCH (s:Strategy)-[:FAVORABLE_IN]->(m:MarketRegime {name: $regime_name})
        RETURN s, m.name AS regime_name
        ORDER BY s.edge_score DESC
        """
        
        with self._driver.session() as session:
            results = session.run(query, regime_name=regime_name)
            return [record.data() for record in results]
    
    def search_strategies(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Full-text search on strategies."""
        # This would use Neo4j full-text search index
        # For now, returns all strategies sorted by edge score
        query = """
        MATCH (s:Strategy)
        RETURN s
        ORDER BY s.edge_score DESC
        LIMIT $limit
        """
        
        with self._driver.session() as session:
            results = session.run(query, limit=limit)
            return [record.data()["s"] for record in results]


# Example usage
if __name__ == "__main__":
    import asyncio
    from smb_schema_v4 import TradingStrategy
    
    async def main():
        builder = KnowledgeGraphBuilder()
        
        # Load a strategy from v3 JSON
        # (For demo, we'll create a simple one)
        strategy = TradingStrategy(
            name="Demo Strategy",
            description="Demonstration strategy for knowledge graph ingestion",
            trading_style="day_trading",
            primary_regime=MarketRegime.TRENDED_BULL,
            confidence=0.85,
            edge_score=80,
            validation_status="validated",
            timeframes=["15m", "1h"],
            assets=["SPY", "QQQ"],
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
            indicators_used=["volume", "RSI"],
            backtest_results={
                "total_trades": 100,
                "win_rate": 0.60,
                "profit_factor": 1.5,
                "max_drawdown": 10.0,
                "sharpe_ratio": 1.2,
                "sortino_ratio": 1.8,
                "total_pnl": 15000,
                "average_risk_reward": 1.5,
                "regime_specific_metrics": {},
                "statistical_significance": 0.05
            },
            evidence_refs=[],
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        # Ingest strategy
        result = builder.ingest_strategy(strategy)
        print(f"Strategy ingested: {result}")
        
        # Query strategy
        strategy_doc = builder.get_strategy_by_id(strategy.id)
        print(f"Recovered strategy: {strategy_doc['s'].get('name')}")
        
        builder.close()
    
    asyncio.run(main())
