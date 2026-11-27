"""
Multi-Agent Pipeline Orchestrator
Project: AI Startup Idea Validator

Coordinates the autonomous multi-agent pipeline from raw idea submission
to executive validation dossier and conversational advisor readiness:
- Step 1: Idea Structuring & Normalization
- Step 2: Real-Time Web Intelligence Gathering (Tavily)
- Step 3: Market Opportunity & Customer Segmentation Analysis
- Step 4: Competitor Discovery & Whitespace Benchmarking
- Step 5: SWOT & Categorized Risk Evaluation
- Step 6: Lean MVP MoSCoW Backlog & Tech Stack Architecture
- Step 7: Go-To-Market Playbook & Tiered Pricing Formulation
- Step 8: Executive Dossier Compilation & Feasibility Index Scoring
- Step 9: Workspace Persistence & Conversational Advisor Initialization
"""

import sys
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Dict, Any

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.models import (
    RawStartupSubmission,
    WorkspaceSession,
    ValidationDossierReport
)
from src.idea_extractor import extract_idea_structure
from src.web_search_agent import WebSearchAgent
from src.market_analysis_agent import MarketAnalysisAgent
from src.competitor_analysis_agent import CompetitorAnalysisAgent
from src.swot_risk_agent import SWOTRiskAgent
from src.mvp_agent import MVPAgent
from src.gtm_agent import GTMAgent
from src.report_generator_agent import ReportGeneratorAgent
from src.workspace_manager import save_workspace

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PipelineOrchestrator")


class StartupValidationOrchestrator:
    """End-to-end multi-agent pipeline orchestrator."""

    def __init__(self):
        self.web_search_agent = WebSearchAgent()
        self.market_agent = MarketAnalysisAgent()
        self.competitor_agent = CompetitorAnalysisAgent()
        self.swot_risk_agent = SWOTRiskAgent()
        self.mvp_agent = MVPAgent()
        self.gtm_agent = GTMAgent()
        self.report_agent = ReportGeneratorAgent()

    def run_pipeline(
        self,
        raw_submission: RawStartupSubmission,
        session_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str, str, Dict[str, Any]], None]] = None
    ) -> ValidationDossierReport:
        """
        Executes the full 8-step agentic pipeline.
        Invokes progress_callback at each phase for live UI/terminal streaming.
        """
        sid = session_id or str(uuid.uuid4())
        total_steps = 8

        def notify(step: int, name: str, status: str, details: Optional[Dict[str, Any]] = None):
            logger.info(f"Pipeline [{step}/{total_steps}] {name} -> {status}")
            if progress_callback:
                progress_callback(step, total_steps, name, status, details or {})

        # Step 1: Idea Ingestion & Structuring
        notify(1, "Idea Ingestion & LLM Structuring", "processing", {"description": raw_submission.description[:80]})
        structured_idea = extract_idea_structure(raw_submission)
        notify(1, "Idea Ingestion & LLM Structuring", "completed", {
            "idea_name": structured_idea.idea_name,
            "industry": structured_idea.industry,
            "features_count": len(structured_idea.key_features)
        })

        # Step 2: Web Search Intelligence (Tavily)
        notify(2, "Web Search & Market Data Retrieval", "processing", {"query": structured_idea.search_queries[0] if structured_idea.search_queries else structured_idea.idea_name})
        search_intel = self.web_search_agent.search_and_synthesize(structured_idea)
        notify(2, "Web Search & Market Data Retrieval", "completed", {
            "mode": search_intel.mode,
            "sources_count": len(search_intel.market_results) + len(search_intel.competitor_results)
        })

        # Step 3: Market Opportunity & Customer Segmentation
        notify(3, "Market Sizing & Customer Segmentation", "processing", {})
        market_rep = self.market_agent.analyze(structured_idea, search_intel)
        notify(3, "Market Sizing & Customer Segmentation", "completed", {
            "tam": market_rep.market_size.tam_value,
            "sam": market_rep.market_size.sam_value,
            "cagr": market_rep.cagr_growth_rate,
            "readiness_score": market_rep.market_readiness_score
        })

        # Step 4: Competitor Discovery & Whitespace Benchmarking
        notify(4, "Competitor Discovery & Comparison", "processing", {})
        competitor_rep = self.competitor_agent.analyze(structured_idea, search_intel)
        notify(4, "Competitor Discovery & Comparison", "completed", {
            "direct_competitors": [c.name for c in competitor_rep.direct_competitors],
            "defensibility": competitor_rep.defensibility_rating
        })

        # Step 5: SWOT & Risk Analysis
        notify(5, "SWOT & Risk Assessment", "processing", {})
        swot_rep = self.swot_risk_agent.analyze(structured_idea, market_rep, competitor_rep)
        notify(5, "SWOT & Risk Assessment", "completed", {
            "overall_risk": swot_rep.overall_risk_level,
            "strengths_count": len(swot_rep.swot_analysis.strengths),
            "risks_count": len(swot_rep.startup_risks)
        })

        # Step 6: MVP Feature Recommendation (MoSCoW Backlog)
        notify(6, "MVP Feature Scoping & Roadmap", "processing", {})
        mvp_rep = self.mvp_agent.analyze(structured_idea, swot_rep, competitor_rep)
        notify(6, "MVP Feature Scoping & Roadmap", "completed", {
            "features_count": len(mvp_rep.features),
            "timeline": mvp_rep.estimated_mvp_timeline
        })

        # Step 7: Go-To-Market Playbook & Pricing
        notify(7, "Go-To-Market Strategy Formulation", "processing", {})
        gtm_rep = self.gtm_agent.analyze(structured_idea, market_rep, competitor_rep, mvp_rep)
        notify(7, "Go-To-Market Strategy Formulation", "completed", {
            "channels_count": len(gtm_rep.acquisition_channels),
            "pricing_tiers_count": len(gtm_rep.pricing_tiers)
        })

        # Step 8: Final Dossier Compilation & Scoring
        notify(8, "Validation Dossier Compilation & Scoring", "processing", {})
        dossier = self.report_agent.compile_dossier(
            session_id=sid,
            idea=structured_idea,
            search_intel=search_intel,
            market=market_rep,
            comp=competitor_rep,
            swot=swot_rep,
            mvp=mvp_rep,
            gtm=gtm_rep
        )
        notify(8, "Validation Dossier Compilation & Scoring", "completed", {
            "score": dossier.feasibility_score,
            "verdict": dossier.verdict
        })

        # Step 9: Persist to Workspace Store
        session = WorkspaceSession(
            session_id=sid,
            raw_input=raw_submission,
            status="completed",
            report=dossier
        )
        save_workspace(session)
        logger.info(f"Pipeline completed successfully. Session ID: {sid} saved to workspace store.")

        return dossier


def run_pipeline_cli():
    """Terminal interactive test runner."""
    print("\n" + "=" * 80)
    print("      AI STARTUP IDEA VALIDATOR — END-TO-END MULTI-AGENT PIPELINE")
    print("=" * 80)

    sample = RawStartupSubmission(
        startup_name="FleetPulse EV",
        description="Smart EV route optimization and depot charging management for delivery fleets.",
        industry="Logistics & CleanTech"
    )

    def progress(step, total, name, status, details):
        status_symbol = "[..]" if status == "processing" else "[OK]"
        print(f"  [{step}/{total}] {status_symbol} {name}: {status.upper()} {details if status == 'completed' else ''}")

    orchestrator = StartupValidationOrchestrator()
    dossier = orchestrator.run_pipeline(sample, progress_callback=progress)

    print("\n" + "=" * 80)
    print(f"  VALIDATION COMPLETED: {dossier.idea_name}")
    print(f"  FEASIBILITY SCORE   : {dossier.feasibility_score} / 100")
    print(f"  STRATEGIC VERDICT   : {dossier.verdict}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_pipeline_cli()
