# Graphify A/B Test

Compares Neo4j vs Graphify-RS backends for SMB Knowledge Base GraphRAG.

## Run

```bash
cd /home/ml/graphify_ab_test
python3 run_ab_test.py
```

## Files

- `config.yaml` - Backend configuration
- `run_ab_test.py` - A/B test runner
- `tests/` - Test queries and expected results

## Backends

1. **Neo4j** (current) - Running on localhost:7474
2. **Graphify-RS** - Future addition
