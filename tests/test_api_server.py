"""
API Server Endpoint Tests.
Project: AI Startup Idea Validator
"""

import sys
import unittest
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.models import RawStartupSubmission, AdvisorChatRequest
from src.server import (
    health_check,
    get_presets,
    validate_startup_idea,
    get_workspaces_list,
    get_workspace_session,
    chat_with_advisor
)


class TestAPIServer(unittest.TestCase):

    def test_health_endpoint(self):
        """Test GET /api/health."""
        data = health_check()
        self.assertEqual(data["status"], "online")
        self.assertIn("mode", data)

    def test_presets_endpoint(self):
        """Test GET /api/presets."""
        presets = get_presets()
        self.assertIsInstance(presets, list)
        self.assertEqual(len(presets), 1)
        self.assertEqual(presets[0]["startup_name"], "SmartPantry AI")

    def test_validate_endpoint(self):
        """Test POST /api/validate logic."""
        sub = RawStartupSubmission(
            startup_name="AgriSense Drone",
            description="Autonomous drone scouting paired with sub-surface IoT soil probes to deliver real-time multispectral crop health intelligence.",
            industry="AgriTech & Robotics",
            target_customers="Commercial crop producers managing 500+ acres"
        )
        dossier = validate_startup_idea(sub)
        self.assertEqual(dossier.idea_name, "AgriSense Drone")
        self.assertGreaterEqual(dossier.feasibility_score, 0)
        self.assertTrue(len(dossier.pillar_scores) == 4)
        self.assertIsNotNone(dossier.market_analysis)
        self.assertIsNotNone(dossier.competitor_analysis)
        self.assertIsNotNone(dossier.swot_and_risk)
        self.assertIsNotNone(dossier.mvp_recommendation)
        self.assertIsNotNone(dossier.gtm_strategy)

    def test_validate_rejects_short_description(self):
        """Test POST /api/validate rejects description below 2-3 lines."""
        from fastapi import HTTPException
        sub = RawStartupSubmission(
            startup_name="Tiny App",
            description="Just a food app.",  # Below 2-3 lines
            industry="Food"
        )
        with self.assertRaises(HTTPException) as ctx:
            validate_startup_idea(sub)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("below 2-3 lines", ctx.exception.detail)

    def test_workspaces_list_and_get_session(self):
        """Test GET /api/workspaces and GET /api/workspace/{id}."""
        workspaces = get_workspaces_list()
        self.assertIsInstance(workspaces, list)
        if len(workspaces) > 0:
            sid = workspaces[0]["session_id"]
            session_data = get_workspace_session(sid)
            self.assertEqual(session_data["session_id"], sid)

    def test_advisor_chat_endpoint(self):
        """Test POST /api/advisor/chat logic."""
        req = AdvisorChatRequest(
            session_id="test-orchestrator-session-001",
            message="How do I defend against copycat competitors in phase 1?",
            history=[]
        )
        resp = chat_with_advisor(req)
        self.assertTrue(len(resp.response) > 30)
        self.assertTrue(len(resp.suggested_followups) >= 1)


if __name__ == "__main__":
    unittest.main()
