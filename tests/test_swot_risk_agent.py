"""
Unit & Integration Tests for SWOT and Risk Analysis Agent.
Project: AI Startup Idea Validator
"""

import json
import unittest
from pathlib import Path

from src.models import (
    SWOTItem,
    SWOTAnalysis,
    StartupRisk,
    SWOTAndRiskReport,
    StructuredIdeaOutput,
    RawStartupSubmission
)
from src.swot_risk_agent import SWOTRiskAgent, clean_and_parse_json, run_swot_and_risk_analysis


class TestSWOTRiskAgent(unittest.TestCase):

    def setUp(self):
        self.agent = SWOTRiskAgent()
        self.sample_idea = StructuredIdeaOutput(
            idea_name="MedTrack AI",
            problem_statement="Hospital pharmacies experience stockouts and drug expiration losses due to disconnected inventory tracking.",
            proposed_solution="Automated RFID and computer vision scanning with predictive consumption forecasting for hospital medication supplies.",
            target_customers="Hospital pharmacy directors and supply chain managers in mid-tier hospitals (200-800 beds)",
            industry="Healthcare & Enterprise SaaS",
            key_features=[
                "Automated smart bin weight & RFID continuous inventory tracking",
                "Predictive drug demand forecasting based on patient census",
                "Automated supplier replenishment triggers before expiration",
                "Hospital EHR / ERP integration connectors (Epic, Cerner)"
            ]
        )

    def test_json_sanitizer_with_markdown_fences(self):
        """Tests that markdown fences and surrounding text are cleanly stripped."""
        dirty_input = '```json\n{"status": "ok", "count": 5}\n```'
        parsed = clean_and_parse_json(dirty_input)
        self.assertEqual(parsed["status"], "ok")
        self.assertEqual(parsed["count"], 5)

    def test_json_sanitizer_with_conversational_chatter(self):
        """Tests that regex extracts JSON even if LLM adds conversational preamble."""
        chatter_input = 'Sure! Here is the JSON you requested:\n{"result": "success"}\nHope this helps!'
        parsed = clean_and_parse_json(chatter_input)
        self.assertEqual(parsed["result"], "success")

    def test_swot_item_and_analysis_models(self):
        """Tests SWOT data model instantiation and field validation."""
        strength = SWOTItem(
            point="Proprietary Computer Vision",
            explanation="Custom models trained on medication packaging.",
            strategic_implication="High defensibility against generic barcode systems."
        )
        self.assertEqual(strength.point, "Proprietary Computer Vision")

        swot = SWOTAnalysis(
            strengths=[strength],
            weaknesses=[],
            opportunities=[],
            threats=[]
        )
        self.assertEqual(len(swot.strengths), 1)

    def test_startup_risk_model(self):
        """Tests StartupRisk model validation."""
        risk = StartupRisk(
            risk_id="RISK-01",
            category="Regulatory & Compliance",
            risk_title="FDA / HIPAA Healthcare Data Compliance",
            likelihood="High",
            impact="High",
            overall_severity="High",
            explanation="Handling medication tracking crosses patient health data thresholds.",
            mitigation_strategy="Implement end-to-end encryption and execute Business Associate Agreements (BAAs)."
        )
        self.assertEqual(risk.risk_id, "RISK-01")
        self.assertEqual(risk.overall_severity, "High")

    def test_agent_analyze_structured_input(self):
        """Tests running the agent with a StructuredIdeaOutput object."""
        report = self.agent.analyze(self.sample_idea)
        
        self.assertIsInstance(report, SWOTAndRiskReport)
        self.assertEqual(report.idea_name, "MedTrack AI")
        self.assertGreaterEqual(len(report.swot_analysis.strengths), 1)
        self.assertGreaterEqual(len(report.swot_analysis.weaknesses), 1)
        self.assertGreaterEqual(len(report.swot_analysis.opportunities), 1)
        self.assertGreaterEqual(len(report.swot_analysis.threats), 1)
        self.assertGreaterEqual(len(report.startup_risks), 3)
        self.assertIn(report.overall_risk_level, ["Low", "Moderate", "High", "Critical"])
        self.assertTrue(len(report.key_strategic_recommendation) > 20)

    def test_agent_analyze_to_json(self):
        """Tests that analyze_to_json returns valid, parseable JSON conforming to schema."""
        json_str = self.agent.analyze_to_json(self.sample_idea)
        self.assertIsInstance(json_str, str)
        
        # Verify it can be loaded back into dict and re-validated
        data = json.loads(json_str)
        self.assertEqual(data["idea_name"], "MedTrack AI")
        revalidated = SWOTAndRiskReport.model_validate(data)
        self.assertEqual(revalidated.idea_name, "MedTrack AI")

    def test_agent_analyze_raw_dict_input(self):
        """Tests that raw dictionaries can be passed directly."""
        raw_dict = {
            "idea_name": "AgriDrone",
            "industry": "AgTech",
            "problem_statement": "Manual crop disease scouting is slow and misses localized blights.",
            "proposed_solution": "Autonomous drone fleet with multispectral imaging for early crop disease detection.",
            "target_customers": "Commercial crop growers with >1000 acres",
            "key_features": ["Multispectral aerial imaging", "Automated flight planning", "Blight heatmaps"]
        }
        report = run_swot_and_risk_analysis(raw_dict)
        self.assertEqual(report.idea_name, "AgriDrone")
        self.assertEqual(report.industry, "AgTech")
        self.assertTrue(any("AgriDrone" in s.explanation or "AgTech" in report.industry for s in report.swot_analysis.strengths))

    def test_risk_mitigation_actionability(self):
        """Verifies that all generated risks have non-empty explanations and mitigation strategies."""
        report = self.agent.analyze(self.sample_idea)
        for risk in report.startup_risks:
            self.assertTrue(len(risk.explanation) > 15, f"Risk explanation too short for {risk.risk_id}")
            self.assertTrue(len(risk.mitigation_strategy) > 15, f"Risk mitigation too short for {risk.risk_id}")


if __name__ == "__main__":
    unittest.main()
