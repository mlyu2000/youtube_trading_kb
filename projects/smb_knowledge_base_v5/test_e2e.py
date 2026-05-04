"""End-to-End Unit Tests for SMB Knowledge Base v5.0"""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, "/home/ml/smb_workspace/projects/smb_knowledge_base_v4/core")

class TestV5Configuration(unittest.TestCase):
    def test_v5_directory_structure(self):
        v5 = Path("/home/ml/smb_workspace/projects/smb_knowledge_base_v5")
        self.assertTrue(v5.exists())
        for d in ["orchestration", "skills", "teams", "validation"]:
            self.assertTrue((v5/d).exists())

    def test_temporal_workflows_exist(self):
        f = Path("/home/ml/smb_workspace/projects/smb_knowledge_base_v5/orchestration/workflows.py")
        self.assertTrue(f.exists())

    def test_temporal_activities_exist(self):
        f = Path("/home/ml/smb_workspace/projects/smb_knowledge_base_v5/orchestration/activities.py")
        self.assertTrue(f.exists())

class TestV5Schemas(unittest.TestCase):
    def test_v4_schema_imports(self):
        from smb_schema_v4 import TradingStrategy, MarketRegime
        self.assertIn("trended_bull", [r.value for r in MarketRegime])

class TestV5NotebookLM(unittest.TestCase):
    def test_notebooklm_activity(self):
        f = Path("/home/ml/smb_workspace/projects/smb_knowledge_base_v5/orchestration/activities.py")
        self.assertIn("add_source", f.read_text())

class TestV5MultiAgent(unittest.TestCase):
    def test_skills_directory(self):
        f = Path("/home/ml/smb_workspace/projects/smb_knowledge_base_v5/skills/trading_skills.py")
        self.assertTrue(f.exists())

    def test_teams_config(self):
        f = Path("/home/ml/smb_workspace/projects/smb_knowledge_base_v5/teams/smb_trading_team.yaml")
        self.assertTrue(f.exists())

class TestV5Pipeline(unittest.TestCase):
    def test_workflow_definitions(self):
        f = Path("/home/ml/smb_workspace/projects/smb_knowledge_base_v5/orchestration/workflows.py")
        c = f.read_text()
        for w in ["ProcessNewVideo", "ExtractAndValidateStrategy"]:
            self.assertIn(w, c)

    def test_quality_gates(self):
        f = Path("/home/ml/smb_workspace/projects/smb_knowledge_base_v5/skills/trading_skills.py")
        self.assertIn("edge_score", f.read_text())

class TestV5Validation(unittest.TestCase):
    def test_validation_module(self):
        f = Path("/home/ml/smb_workspace/projects/smb_knowledge_base_v5/validation")
        self.assertTrue(f.exists())

class TestV5Observability(unittest.TestCase):
    def test_worker_config(self):
        f = Path("/home/ml/smb_workspace/projects/smb_knowledge_base_v5/orchestration/worker.py")
        self.assertTrue(f.exists())

if __name__ == "__main__":
    unittest.main(verbosity=2)
