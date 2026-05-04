"""
SMB Knowledge Base v4.0 - Multi-Store Database Connections

Provides connection helpers for:
- PostgreSQL (metadata, provenance)
- Neo4j (Knowledge Graph)
- Qdrant (Vector Store)
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime
import logging

from neo4j import GraphDatabase, Driver
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from pydantic import BaseModel, Field
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine,.Field as SQLField

# Configure logging
logger = logging.getLogger(__name__))


class DatabaseConfig(BaseModel):
    """Database connection configuration."""
    model_config = {"extra": "allow"}
    
    # PostgreSQL
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="smb_kb_v4")
    postgres_user: str = Field(default="smb_user")
    postgres_password: str = Field(default="smb_password")
    
    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="neo4j_password")
    
    # Qdrant
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_api_key: Optional[str] = Field(default=None)


class MultiStoreConnection:
    """Manages connections to all three storage systems."""
    
    _postgres_pool: Optional[asyncpg.Pool] = None
    _neo4j_driver: Optional[Driver] = None
    _qdrant_client: Optional[QdrantClient] = None
    _config: DatabaseConfig
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self._config = config or DatabaseConfig()
    
    async def connect(self) -> None:
        """Establish connections to all stores."""
        # PostgreSQL connection
        try:
            self._postgres_pool = await asyncpg.create_pool(
                host=self._config.postgres_host,
                port=self._config.postgres_port,
                database=self._config.postgres_db,
                user=self._config.postgres_user,
                password=self._config.postgres_password,
                min_size=1,
                max_size=10
            )
            logger.info("PostgreSQL connection established")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
        
        # Neo4j connection
        try:
            self._neo4j_driver = GraphDatabase.driver(
                self._config.neo4j_uri,
                auth=(self._config.neo4j_user, self._config.neo4j_password)
            )
            logger.info("Neo4j connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
        
        # Qdrant connection
        try:
            self._qdrant_client = QdrantClient(
                host=self._config.qdrant_host,
                port=self._config.qdrant_port,
                api_key=self._config.qdrant_api_key
            )
            logger.info("Qdrant connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close all connections."""
        if self._postgres_pool:
            await self._postgres_pool.close()
            logger.info("PostgreSQL connection closed")
        
        if self._neo4j_driver:
            self._neo4j_driver.close()
            logger.info("Neo4j connection closed")
        
        if self._qdrant_client:
            self._qdrant_client.close()
            logger.info("Qdrant connection closed")
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all connections."""
        results = {}
        
        # PostgreSQL health
        try:
            async with self._postgres_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            results["postgres"] = True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            results["postgres"] = False
        
        # Neo4j health
        try:
            with self._neo4j_driver.session() as session:
                session.run("RETURN 1")
            results["neo4j"] = True
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            results["neo4j"] = False
        
        # Qdrant health
        try:
            self._qdrant_client.get_collections()
            results["qdrant"] = True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            results["qdrant"] = False
        
        return results
    
    # PostgreSQL methods
    async def execute_postgres(self, query: str, *args) -> Any:
        """Execute PostgreSQL query."""
        async with self._postgres_pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def create_postgres_tables(self) -> None:
        """Create PostgreSQL schema."""
        async with self._postgres_pool.acquire() as conn:
            # Strategies table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS strategies (
                    id UUID PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    trading_style TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_updated TIMESTAMP DEFAULT NOW(),
                    edge_score INTEGER,
                    validation_status TEXT
                )
            """)
            
            # Videos table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id UUID PRIMARY KEY,
                   youtube_url TEXT NOT NULL,
                    video_id TEXT UNIQUE NOT NULL,
                    title TEXT,
                    description TEXT,
                    published_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Evidence table (link strategies to videos)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS evidence (
                    id UUID PRIMARY KEY,
                    strategy_id UUID REFERENCES strategies(id),
                    video_id TEXT,
                    timestamp_start FLOAT,
                    timestamp_end FLOAT,
                    confidence FLOAT,
                    context_snippet TEXT
                )
            """)
            
            logger.info("PostgreSQL tables created")
    
    # Neo4j methods
    def execute_neo4j(self, query: str, **params) -> Any:
        """Execute Neo4j Cypher query."""
        with self._neo4j_driver.session() as session:
            return session.run(query, **params)
    
    async def create_neo4j_constraints(self) -> None:
        """Create Neo4j indexes and constraints."""
        constraints = [
            "CREATE CONSTRAINT strategy_id IF NOT EXISTS FOR (s:Strategy) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT video_id IF NOT EXISTS FOR (v:Video) REQUIRE v.id IS UNIQUE",
            "CREATE CONSTRAINT strategy_name IF NOT EXISTS FOR (s:Strategy) REQUIRE s.name IS UNIQUE",
            "CREATE INDEX strategy_trading_style IF NOT EXISTS FOR (s:Strategy) ON (s.trading_style)",
            "CREATE INDEX video_published_at IF NOT EXISTS FOR (v:Video) ON (v.published_at)",
        ]
        
        for constraint in constraints:
            try:
                self.execute_neo4j(constraint)
                logger.info(f"Created constraint/index: {constraint}")
            except Exception as e:
                logger.warning(f"Constraint already exists or failed: {e}")
        
        # Create vector index for embeddings
        try:
            self.execute_neo4j("""
                CALL db.index.vector.createNodeIndex('strategy_embedding', 'Strategy', 'embedding', 768, 'cosine')
            """)
            logger.info("Neo4j vector index created")
        except Exception as e:
            logger.warning(f"Vector index already exists or failed: {e}")
    
    # Qdrant methods
    def create_qdrant_collection(self, collection_name: str, vector_size: int = 768) -> None:
        """Create Qdrant collection if it doesn't exist."""
        try:
            self._qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            logger.info(f"Qdrant collection '{collection_name}' created")
        except Exception as e:
            logger.info(f"Qdrant collection '{collection_name}' already exists or error: {e}")
    
    def upsert_qdrant_points(self, collection_name: str, points: list) -> None:
        """Upsert points into Qdrant collection."""
        self._qdrant_client.upsert(collection_name=collection_name, points=points)
        logger.info(f"Upserted {len(points)} points to '{collection_name}'")


# Factory function for singleton pattern
_connections: MultiStoreConnection = None


def get_db_connection() -> MultiStoreConnection:
    """Get or create database connection singleton."""
    global _connections
    if _connections is None:
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        config = DatabaseConfig(
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=int(os.getenv("POSTGRES_PORT", 5432)),
            postgres_db=os.getenv("POSTGRES_DB", "smb_kb_v4"),
            postgres_user=os.getenv("POSTGRES_USER", "smb_user"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", "smb_password"),
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "neo4j_password"),
            qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
            qdrant_port=int(os.getenv("QDRANT_PORT", 6333)),
            qdrant_api_key=os.getenv("QDRANT_API_KEY")
        )
        
        _connections = MultiStoreConnection(config)
    
    return _connections


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        db = get_db_connection()
        await db.connect()
        
        health = await db.health_check()
        print(f"Health check: {health}")
        
        await db.create_postgres_tables()
        await db.create_neo4j_constraints()
        db.create_qdrant_collection("strategies")
        
        await db.disconnect()
    
    asyncio.run(main())
