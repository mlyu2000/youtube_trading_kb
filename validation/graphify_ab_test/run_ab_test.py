#!/usr/bin/env python3
import yaml
import time
import json

def test_neo4j_query(query: str) -> dict:
    import urllib.request
    import json as json_lib
    
    cypher_query = {
        "statements": [{"statement": query}]
    }
    
    req = urllib.request.Request(
        "http://localhost:7474/db/data/transaction/commit",
        data=json_lib.dumps(cypher_query).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Basic bmVvNGo6dGVtcG9yYWwxMjM="
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json_lib.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def ab_test():
    queries = [
        "MATCH (s:Strategy) RETURN s.video_id AS video, s.trading_style AS style LIMIT 5",
        "MATCH (s:Strategy)-[:HAS_ENTRY_PATTERN]->(e:EntryPattern) RETURN DISTINCT e.description LIMIT 5",
        "MATCH (s:Strategy {trading_style: 'scalping'})-[:HAS_SETUP_PATTERN]->(p) RETURN p.name",
        "MATCH (c:StrategyCluster)<-[:CLUSTERED]-(s:Strategy) RETURN c.cluster_id, collect(s.video_id) AS videos"
    ]
    
    start_time = time.time()
    results = []
    
    for q in queries:
        q_start = time.time()
        resp = test_neo4j_query(q)
        q_time = (time.time() - q_start) * 1000
        results.append({"query": q[:50], "latency_ms": q_time, "success": "error" not in resp})
    
    total_time = (time.time() - start_time) * 1000
    
    return {
        "backend": "neo4j",
        "total_queries": len(queries),
        "total_latency_ms": total_time,
        "results": results
    }

if __name__ == "__main__":
    result = ab_test()
    print(json.dumps(result, indent=2))
    
    with open("results_neo4j.json", "w") as f:
        json.dump(result, f, indent=2)
