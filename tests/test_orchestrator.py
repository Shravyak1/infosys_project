"""
Integration Tests for Multi-Agent Pipeline Orchestrator.
Project: AI Startup Idea Validator
"""

import sys
import unittest
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.models import RawStartupSubmission, ValidationDossierReport
from src.orchestrator import StartupValidationOrchestrator
from src.workspace_manager import load_workspace


class TestPipelineOrchestrator(unittest.TestCase):

    def setUp(self):
        self.orchestrator = StartupValidationOrchestrator()

    def test_end_to_end_pipeline_execution(self):
        """Tests that the orchestrator executes all 8 steps without crash and persists dossier."""
        test_sub = RawStartupSubmission(
            startup_name="MedTrack AI",
            description="Autonomous RFID smart bins for hospital pharmacies preventing drug stockouts and medication expiration waste.",
            industry="Healthcare & Enterprise SaaS",
            target_customers="Hospital pharmacy directors in 200-800 bed hospitals"
        )

        steps_recorded = []
        def track_progress(step, total, name, status, details):
            if status == "completed":
                steps_recorded.append((step, name))

        dossier = self.orchestrator.run_pipeline(
            test_sub,
            session_id="test-orchestrator-session-001",
            progress_callback=track_progress
        )

        self.assertIsInstance(dossier, ValidationDossierReport)
        self.assertEqual(dossier.idea_name, "MedTrack AI")
        self.assertEqual(len(steps_recorded), 8)
        self.assertGreaterEqual(dossier.feasibility_score, 0)
        self.assertLessEqual(dossier.feasibility_score, 100)

        # Check saved session
        saved = load_workspace("test-orchestrator-session-001")
        self.assertIsNotNone(saved)
        self.assertEqual(saved.report.idea_name, "MedTrack AI")


if __name__ == "__main__":
    unittest.main()
