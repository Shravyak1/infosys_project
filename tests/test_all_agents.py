"""
Comprehensive Unit & Integration Tests for All 9 Modules and Agents.
Project: AI Startup Idea Validator
"""

import sys
import unittest
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.models import (
    RawStartupSubmission,
    StructuredIdeaOutput,
    WebSearchIntelligence,
    MarketOpportunityReport,
    CompetitorAnalysisReport,
    SWOTAndRiskReport,
    MVPRecommendationReport,
    GTMStrategyReport,
    ValidationDossierReport,
    AdvisorChatRequest,
    AdvisorChatResponse,
    WorkspaceSession
)
from src.idea_extractor import extract_idea_structure
from src.web_search_agent import WebSearchAgent
from src.market_analysis_agent import MarketAnalysisAgent
from src.competitor_analysis_agent import CompetitorAnalysisAgent
from src.swot_risk_agent import SWOTRiskAgent
from src.mvp_agent import MVPAgent
from src.gtm_agent import GTMAgent
from src.report_generator_agent import ReportGeneratorAgent, export_to_markdown
from src.conversational_advisor import ConversationalAdvisorAgent
from src.workspace_manager import save_workspace, load_workspace, list_workspaces, get_default_presets


class TestAllAgents(unittest.TestCase):

    def setUp(self):
        self.raw_sub = RawStartupSubmission(
            startup_name="FleetPulse EV",
            description="AI dynamic route optimization, battery state-of-health management, and smart charging scheduling for commercial fleets.",
            industry="Logistics & CleanTech",
            target_customers="Commercial delivery fleets (15-250 electric vans)"
        )

    def test_module_1_idea_extractor(self):
        """Module 1: Test idea extraction into StructuredIdeaOutput."""
        idea = extract_idea_structure(self.raw_sub)
        self.assertIsInstance(idea, StructuredIdeaOutput)
        self.assertEqual(idea.idea_name, "FleetPulse EV")
        self.assertIn("Logistics", idea.industry)
        self.assertTrue(len(idea.key_features) >= 3)
        self.assertTrue(len(idea.search_queries) >= 1)

    def test_module_2_web_search_agent(self):
        """Module 2: Test Web Search Agent data retrieval and categorization."""
        idea = extract_idea_structure(self.raw_sub)
        agent = WebSearchAgent()
        intel = agent.search_and_synthesize(idea)
        self.assertIsInstance(intel, WebSearchIntelligence)
        self.assertTrue(len(intel.ai_synthesis) > 20)
        self.assertTrue(len(intel.market_results) >= 1)
        self.assertTrue(len(intel.competitor_results) >= 1)

    def test_module_3_market_analysis_agent(self):
        """Module 3: Test Market Opportunity Sizing, Personas, and Readiness Score."""
        idea = extract_idea_structure(self.raw_sub)
        agent = MarketAnalysisAgent()
        rep = agent.analyze(idea)
        self.assertIsInstance(rep, MarketOpportunityReport)
        self.assertTrue("Billion" in rep.market_size.tam_value or "Million" in rep.market_size.tam_value)
        self.assertTrue("Billion" in rep.market_size.sam_value or "Million" in rep.market_size.sam_value)
        self.assertGreaterEqual(rep.market_readiness_score, 1)
        self.assertLessEqual(rep.market_readiness_score, 10)
        self.assertTrue(len(rep.personas) >= 1)
        self.assertTrue(len(rep.personas[0].acute_pain_points) >= 1)

    def test_module_4_competitor_analysis_agent(self):
        """Module 4: Test Competitor Benchmarking, 5-Dimension Matrix, and UVP."""
        idea = extract_idea_structure(self.raw_sub)
        agent = CompetitorAnalysisAgent()
        rep = agent.analyze(idea)
        self.assertIsInstance(rep, CompetitorAnalysisReport)
        self.assertTrue(len(rep.direct_competitors) >= 2)
        self.assertTrue(len(rep.feature_comparison_matrix) >= 4)
        self.assertTrue(len(rep.uncontested_white_space) > 15)
        self.assertTrue(len(rep.unique_value_proposition) > 15)

    def test_module_5_swot_risk_agent(self):
        """Module 5: Test 2x2 SWOT Matrix and Categorized Risks with Mitigations."""
        idea = extract_idea_structure(self.raw_sub)
        market = MarketAnalysisAgent().analyze(idea)
        comp = CompetitorAnalysisAgent().analyze(idea)
        agent = SWOTRiskAgent()
        rep = agent.analyze(idea, market, comp)
        self.assertIsInstance(rep, SWOTAndRiskReport)
        self.assertTrue(len(rep.swot_analysis.strengths) >= 3)
        self.assertTrue(len(rep.swot_analysis.weaknesses) >= 3)
        self.assertTrue(len(rep.swot_analysis.opportunities) >= 3)
        self.assertTrue(len(rep.swot_analysis.threats) >= 3)
        self.assertTrue(len(rep.startup_risks) >= 3)
        self.assertTrue(len(rep.historical_case_studies) >= 1)
        for r in rep.startup_risks:
            self.assertTrue(len(r.mitigation_strategy) > 10)
            self.assertIsNotNone(r.historical_precedent)

    def test_module_6_mvp_agent(self):
        """Module 6: Test MoSCoW Backlog, Tech Stack, and 8-Week Sprints."""
        idea = extract_idea_structure(self.raw_sub)
        comp = CompetitorAnalysisAgent().analyze(idea)
        swot = SWOTRiskAgent().analyze(idea)
        agent = MVPAgent()
        rep = agent.analyze(idea, swot, comp)
        self.assertIsInstance(rep, MVPRecommendationReport)
        self.assertTrue(len(rep.core_value_hypothesis) > 10)
        categories = {f.moscow_category for f in rep.features}
        self.assertIn("Must-Have", categories)
        self.assertTrue(len(rep.tech_stack) >= 4)
        self.assertTrue(len(rep.roadmap_sprints) >= 3)
        self.assertTrue(len(rep.validation_experiments) >= 1)

    def test_module_7_gtm_agent(self):
        """Module 7: Test Go-To-Market Channels, Pricing Tiers, and Launch Phases."""
        idea = extract_idea_structure(self.raw_sub)
        agent = GTMAgent()
        rep = agent.analyze(idea)
        self.assertIsInstance(rep, GTMStrategyReport)
        self.assertTrue(len(rep.positioning_headline) > 10)
        self.assertTrue(len(rep.acquisition_channels) >= 2)
        self.assertTrue(len(rep.pricing_tiers) >= 2)
        self.assertTrue(len(rep.launch_phases) >= 2)

    def test_module_8_report_generator_and_markdown(self):
        """Module 8: Test Executive Dossier Compilation, Feasibility Index, and Exports."""
        idea = extract_idea_structure(self.raw_sub)
        search = WebSearchAgent().search_and_synthesize(idea)
        market = MarketAnalysisAgent().analyze(idea, search)
        comp = CompetitorAnalysisAgent().analyze(idea, search)
        swot = SWOTRiskAgent().analyze(idea, market, comp)
        mvp = MVPAgent().analyze(idea, swot, comp)
        gtm = GTMAgent().analyze(idea, market, comp, mvp)

        agent = ReportGeneratorAgent()
        dossier = agent.compile_dossier("test-session-123", idea, search, market, comp, swot, mvp, gtm)
        self.assertIsInstance(dossier, ValidationDossierReport)
        self.assertGreaterEqual(dossier.feasibility_score, 0)
        self.assertLessEqual(dossier.feasibility_score, 100)
        self.assertTrue(any(v in dossier.verdict for v in ["PROCEED", "PIVOT", "ABANDON"]))
        self.assertEqual(len(dossier.pillar_scores), 4)

        # Markdown Export test
        md = export_to_markdown(dossier)
        self.assertIn("# Executive Startup Validation Dossier", md)
        self.assertIn("FleetPulse EV", md)
        self.assertIn("Feasibility Index Breakdown", md)

    def test_module_9_conversational_advisor(self):
        """Module 9: Test Conversational Advisor grounding and responses."""
        idea = extract_idea_structure(self.raw_sub)
        search = WebSearchAgent().search_and_synthesize(idea)
        market = MarketAnalysisAgent().analyze(idea, search)
        comp = CompetitorAnalysisAgent().analyze(idea, search)
        swot = SWOTRiskAgent().analyze(idea, market, comp)
        mvp = MVPAgent().analyze(idea, swot, comp)
        gtm = GTMAgent().analyze(idea, market, comp, mvp)
        dossier = ReportGeneratorAgent().compile_dossier("test-session-chat", idea, search, market, comp, swot, mvp, gtm)

        advisor = ConversationalAdvisorAgent()
        req = AdvisorChatRequest(session_id="test-session-chat", message="How should I price the initial commercial pilot?")
        res = advisor.chat(req, dossier)
        self.assertIsInstance(res, AdvisorChatResponse)
        self.assertTrue(len(res.response) > 50)
        self.assertTrue(len(res.suggested_followups) >= 2)
        self.assertIn("Go-To-Market", res.grounded_in_modules)

    def test_workspace_manager(self):
        """Module 1/Workspace: Test persistence and presets."""
        presets = get_default_presets()
        self.assertEqual(len(presets), 1)
        self.assertEqual(presets[0]["startup_name"], "SmartPantry AI")
        
        session = WorkspaceSession(
            session_id="test-save-session-001",
            raw_input=self.raw_sub,
            status="completed"
        )
        saved_path = save_workspace(session)
        self.assertTrue(saved_path.exists())

        loaded = load_workspace("test-save-session-001")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.session_id, "test-save-session-001")

    def test_rag_past_startup_knowledge(self):
        """RAG Test: Test hybrid retrieval of past startup post-mortems and groundings."""
        from src.rag_startup_knowledge import rag_engine
        cases = rag_engine.retrieve_relevant_cases(
            query_text="A smart mobile app that tracks grocery expiration dates and suggests recipes from fridge items to prevent food waste.",
            industry="Consumer Tech & FoodTech",
            target_customers="Everyday households and college students",
            top_k=3
        )
        self.assertTrue(len(cases) >= 2)
        names = [c.startup_name for c in cases]
        self.assertTrue(any(n in names for n in ["CozZo", "Juicero", "Too Good To Go", "SuperCook", "Webvan"]))
        for c in cases:
            self.assertTrue(len(c.warning_for_founder) > 10)
            self.assertTrue(len(c.fatal_mistake_or_key_lesson) > 10)
            self.assertGreaterEqual(c.relevance_score, 0.0)


if __name__ == "__main__":
    unittest.main()
