# GraphRAG A/B Test: Neo4j vs Graphify

## Overview
Testing two graph-based retrieval backends for the SMB Knowledge Base.

## Neo4j Backend (Current)
- **Status**: Running on localhost:7474
- **Data**: 5 strategies, 31 relationships
- **Query Language**: Cypher
- **Docker**: neo4j container

## Graphify Backend (New)
- **Status**: Hermes skill installed
- **Location**: ~/.hermes/skills/graphify/SKILL.md
- **Usage**: /graphify <directory>
- **Features**:
  - Builds knowledge graph from documents
  - Leiden clustering for communities
  - Interactive graph.html visualization
  - Exports graph.json and cypher.txt
  - Supports code + docs + PDFs + images

## Usage
```bash
# Run Graphify on strategy documents
/home/ml/graphify_venv/bin/graphify /path/to/strategies

# This creates:
# - graphify-out/graph.json (knowledge graph)
# - graphify-out/graph.html (interactive viz)
# - graphify-out/obsidian/ (Obsidian vault)
# - graphify-out/GRAPH_REPORT.md (summary)
# - graphify-out/cypher.txt (Neo4j import)

# Import into Neo4j
cat graphify-out/cypher.txt | docker exec -i neo4j cypher-shell -u neo4j -p neo4j
```

## Comparison Points
1. **Query speed**: Neo4j Cypher vs Graphify BFS traversal
2. **Indexing**: Manual cypher vs auto-document extraction
3. **Maintenance**: Manual updates vs auto-sync on changes
4. **Visualization**: Neo4j Browser vs graph.html

## Status
✓ Graphify skill installed for Hermes
✓ Neo4j running with test data
✓ Ready for A/B comparative testing
