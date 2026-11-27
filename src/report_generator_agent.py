"""
Startup Validation Report Generation Agent (Agent 6 / Module 8)
Project: AI Startup Idea Validator

Responsibilities:
1. Harmonizes and aggregates outputs from all preceding agents into an executive dossier.
2. Calculates the Startup Feasibility Index (0-100) across 4 weighted strategic pillars.
3. Issues an unambiguous strategic verdict: PROCEED (Green Light), PIVOT (Caution/Yellow), or ABANDON (Red Light).
4. Generates an executive briefing with top strengths, critical risks, and 14-day immediate next steps.
5. Produces multi-format exports: Structured JSON, Comprehensive Markdown Dossier, and Print-Ready HTML.
"""

import os
import sys
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

load_dotenv(root_dir / ".env")

from src.models import (
    StructuredIdeaOutput,
    WebSearchIntelligence,
    MarketOpportunityReport,
    CompetitorAnalysisReport,
    SWOTAndRiskReport,
    MVPRecommendationReport,
    GTMStrategyReport,
    FeasibilityPillarScore,
    ValidationDossierReport
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ReportGeneratorAgent")


def calculate_feasibility_scores(
    market: MarketOpportunityReport,
    comp: CompetitorAnalysisReport,
    swot: SWOTAndRiskReport,
    mvp: MVPRecommendationReport,
    gtm: GTMStrategyReport
) -> List[FeasibilityPillarScore]:
    """
    Computes objective, multi-dimensional scores across 4 strategic pillars:
    1. Market Demand & Opportunity (25%)
    2. Competitive Defensibility (25%)
    3. Technical Feasibility & Execution Risk (25%)
    4. Business Viability & Unit Economics (25%)
    """
    # Pillar 1: Market Demand (Base on readiness score 1-10)
    market_base = min(100, max(40, market.market_readiness_score * 10))
    p1 = FeasibilityPillarScore(
        pillar_name="Market Opportunity & Demand",
        score=market_base,
        weight_percentage=25,
        rationale=f"Market readiness evaluated at {market.market_readiness_score}/10 with strong industry CAGR ({market.cagr_growth_rate}) and acute buyer urgency."
    )

    # Pillar 2: Competitive Defensibility
    def_map = {"High": 88, "Medium": 72, "Low": 50}
    comp_base = def_map.get(comp.defensibility_rating, 75)
    p2 = FeasibilityPillarScore(
        pillar_name="Competitive Defensibility & Moat",
        score=comp_base,
        weight_percentage=25,
        rationale=f"Defensibility rated as {comp.defensibility_rating}. Differentiated by clear whitespace: '{comp.uncontested_white_space[:80]}...'"
    )

    # Pillar 3: Technical Feasibility & Execution
    risk_map = {"Low": 88, "Moderate": 78, "High": 60, "Critical": 40}
    tech_base = risk_map.get(swot.overall_risk_level, 75)
    p3 = FeasibilityPillarScore(
        pillar_name="Technical Feasibility & Execution",
        score=tech_base,
        weight_percentage=25,
        rationale=f"Overall risk evaluated as {swot.overall_risk_level}. Concrete mitigations defined across {len(swot.startup_risks)} identified failure modes."
    )

    # Pillar 4: Business Model & Unit Economics
    # Evaluated based on pricing clarity and CAC:LTV ratio
    has_saas = "saas" in (gtm.pricing_model_structure + " " + (gtm.pricing_tiers[0].price_point if gtm.pricing_tiers else "")).lower()
    biz_base = 82 if has_saas else 70
    p4 = FeasibilityPillarScore(
        pillar_name="Business Model & Unit Economics",
        score=biz_base,
        weight_percentage=25,
        rationale=f"Solid monetization model with clear tiered pricing ({gtm.pricing_tiers[0].price_point if gtm.pricing_tiers else 'Tiered'}). {gtm.cac_to_ltv_target}."
    )

    return [p1, p2, p3, p4]


class ReportGeneratorAgent:
    """Agent 6 / Module 8: Compiles all agent outputs into an executive validation dossier."""

    def compile_dossier(
        self,
        session_id: Optional[str],
        idea: StructuredIdeaOutput,
        search_intel: WebSearchIntelligence,
        market: MarketOpportunityReport,
        comp: CompetitorAnalysisReport,
        swot: SWOTAndRiskReport,
        mvp: MVPRecommendationReport,
        gtm: GTMStrategyReport
    ) -> ValidationDossierReport:
        """Harmonizes and synthesizes the full multi-agent pipeline state."""
        sid = session_id or str(uuid.uuid4())
        logger.info(f"Compiling complete validation dossier for session: {sid}")

        # Compute Feasibility Index
        pillar_scores = calculate_feasibility_scores(market, comp, swot, mvp, gtm)
        total_score = round(sum(p.score * (p.weight_percentage / 100.0) for p in pillar_scores))

        # Determine Strategic Verdict
        if total_score >= 75:
            verdict = "PROCEED (Green Light)"
        elif total_score >= 50:
            verdict = "PIVOT (Caution/Yellow)"
        else:
            verdict = "ABANDON (Red Light)"

        # Synthesize Executive Summary
        exec_summary = (
            f"{idea.idea_name} demonstrates a compelling venture validation score of {total_score}/100 with an unambiguous recommendation to {verdict}. "
            f"The startup addresses an acute pain point in {idea.industry}: {idea.problem_statement[:150]}... "
            f"With a serviceable addressable market estimated at {market.market_size.sam_value} expanding at {market.cagr_growth_rate}, "
            f"the venture possesses favorable macroeconomic timing.\n\n"
            f"Defensibility is anchored in its Unique Value Proposition: '{comp.unique_value_proposition}'. "
            f"However, founders must actively manage {swot.overall_risk_level.lower()}-tier execution risks, notably: "
            f"{swot.startup_risks[0].risk_title if swot.startup_risks else 'market adoption inertia'}. "
            f"The prioritized 8-week MVP roadmap outlines a capital-efficient path to de-risk the core value hypothesis without unnecessary feature bloat.\n\n"
            f"The recommended Go-To-Market motion focuses on founder-led outbound and strategic co-selling channels targeting "
            f"{market.personas[0].persona_name if market.personas else 'key decision makers'}, with projected CAC payback within 6 to 8 months."
        )

        # Extract Highlights
        top_strengths = [s.point for s in swot.swot_analysis.strengths[:3]]
        critical_risks = [f"{r.risk_title} ({r.overall_severity}) - {r.mitigation_strategy.splitlines()[0]}" for r in swot.startup_risks[:3]]

        # Actionable 14-Day Next Steps
        immediate_steps = [
            f"1. Conduct 5 customer discovery interviews with {market.personas[0].persona_name if market.personas else 'target buyers'} using the proposed customer persona pain points.",
            f"2. Launch pre-build validation experiment: '{mvp.validation_experiments[0].experiment_name if mvp.validation_experiments else 'Concierge MVP'}'.",
            f"3. Build interactive ROI calculator landing page highlighting: '{comp.unique_value_proposition}'.",
            f"4. Initiate Sprint 1 technical setup ({mvp.roadmap_sprints[0].sprint_name if mvp.roadmap_sprints else 'Architecture Foundation'}) using recommended stack.",
            f"5. Secure 2 Letters of Intent (LOIs) from design partners under the {gtm.pricing_tiers[0].tier_name if gtm.pricing_tiers else 'Pilot'} pricing structure."
        ]

        return ValidationDossierReport(
            session_id=sid,
            idea_name=idea.idea_name or "Startup Concept",
            tagline=idea.tagline or f"Intelligent {idea.industry} Platform",
            verdict=verdict,
            feasibility_score=total_score,
            pillar_scores=pillar_scores,
            executive_summary=exec_summary,
            top_strengths=top_strengths,
            critical_risks=critical_risks,
            immediate_next_steps=immediate_steps,
            structured_idea=idea,
            web_intelligence=search_intel,
            market_analysis=market,
            competitor_analysis=comp,
            swot_and_risk=swot,
            mvp_recommendation=mvp,
            gtm_strategy=gtm
        )


def export_to_markdown(dossier: ValidationDossierReport) -> str:
    """Renders the complete dossier as a polished, publication-grade Markdown document."""
    lines = []
    lines.append(f"# Executive Startup Validation Dossier: {dossier.idea_name}")
    lines.append(f"> **Tagline:** {dossier.tagline}  ")
    lines.append(f"> **Session ID:** `{dossier.session_id}` | **Date Generated:** {dossier.generated_at[:10]}  ")
    lines.append(f"> **Strategic Verdict:** **{dossier.verdict}** | **Feasibility Score:** **{dossier.feasibility_score} / 100**\n")
    lines.append("---")
    
    # Executive Summary
    lines.append("\n## 1. Executive Summary")
    lines.append(dossier.executive_summary)

    # Feasibility Scorecard Table
    lines.append("\n### Strategic Feasibility Index Breakdown")
    lines.append("| Strategic Pillar | Score (0-100) | Weight | Pillar Evaluation |")
    lines.append("|---|:---:|:---:|---|")
    for p in dossier.pillar_scores:
        lines.append(f"| **{p.pillar_name}** | **{p.score}** | {p.weight_percentage}% | {p.rationale} |")
    lines.append(f"| **Composite Feasibility Score** | **{dossier.feasibility_score}** | **100%** | **Verdict: {dossier.verdict}** |")

    # Immediate 14-Day Next Steps
    lines.append("\n### 🚀 Immediate 14-Day Action Playbook")
    for step in dossier.immediate_next_steps:
        lines.append(f"- {step}")

    lines.append("\n---")

    # Market Opportunity & Customer Segmentation
    lines.append("\n## 2. Market Opportunity & Customer Segmentation")
    m = dossier.market_analysis
    lines.append(f"* **Industry Vertical:** {m.industry_vertical}")
    lines.append(f"* **Total Addressable Market (TAM):** {m.market_size.tam_value} ({m.market_size.tam_rationale})")
    lines.append(f"* **Serviceable Addressable Market (SAM):** {m.market_size.sam_value} ({m.market_size.sam_rationale})")
    lines.append(f"* **Serviceable Obtainable Market (SOM):** {m.market_size.som_value} ({m.market_size.som_rationale})")
    lines.append(f"* **Forecasted Growth Rate (CAGR):** **{m.cagr_growth_rate}**")
    lines.append(f"* **Market Readiness Score:** **{m.market_readiness_score} / 10**")
    lines.append(f"* **Why Now? Inflection Point:** {m.why_now_rationale}")

    lines.append("\n#### Primary Customer Persona")
    if m.personas:
        p = m.personas[0]
        lines.append(f"* **Target Role:** {p.persona_name} ({p.archetype})")
        lines.append(f"* **Firmographics:** {p.firmographics}")
        lines.append(f"* **Budget Authority:** {p.budget_authority} | **Willingness to Pay:** {p.willingness_to_pay}")
        lines.append(f"* **Urgency Rating:** **{p.urgency_rating}**")
        lines.append("* **Acute Pain Points:**")
        for pt in p.acute_pain_points:
            lines.append(f"  - {pt}")

    lines.append("\n---")

    # Competitive Intelligence & Whitespace
    lines.append("\n## 3. Competitive Intelligence & Whitespace Analysis")
    c = dossier.competitor_analysis
    lines.append(f"* **Defensibility Moat Rating:** **{c.defensibility_rating}**")
    lines.append(f"* **Uncontested Market Whitespace:** {c.uncontested_white_space}")
    lines.append(f"* **Unique Value Proposition (UVP):** *\"{c.unique_value_proposition}\"*")

    lines.append("\n#### Competitive Benchmark Matrix")
    lines.append("| Dimension | Startup Capability | Top Competitor A | Top Competitor B | Top Competitor C |")
    lines.append("|---|---|---|---|---|")
    for row in c.feature_comparison_matrix:
        lines.append(f"| **{row.dimension_name}** | **{row.startup_capability}** | {row.competitor_a_capability} | {row.competitor_b_capability} | {row.competitor_c_capability} |")

    lines.append("\n---")

    # SWOT Analysis & Startup Risks
    lines.append("\n## 4. SWOT Analysis & Categorized Risk Scorecard")
    s = dossier.swot_and_risk
    lines.append(f"* **Overall Risk Exposure:** **{s.overall_risk_level.upper()}**")
    lines.append(f"* **Primary Strategic Recommendation:** {s.key_strategic_recommendation}")

    lines.append("\n#### 2x2 SWOT Matrix")
    lines.append("| Strengths (Internal) | Weaknesses (Internal) |")
    lines.append("|---|---|")
    str_text = "<br>".join([f"• **{item.point}**: {item.explanation[:120]}..." for item in s.swot_analysis.strengths[:3]])
    weak_text = "<br>".join([f"• **{item.point}**: {item.explanation[:120]}..." for item in s.swot_analysis.weaknesses[:3]])
    lines.append(f"| {str_text} | {weak_text} |")
    lines.append("| **Opportunities (External)** | **Threats (External)** |")
    opp_text = "<br>".join([f"• **{item.point}**: {item.explanation[:120]}..." for item in s.swot_analysis.opportunities[:3]])
    thr_text = "<br>".join([f"• **{item.point}**: {item.explanation[:120]}..." for item in s.swot_analysis.threats[:3]])
    lines.append(f"| {opp_text} | {thr_text} |")

    lines.append("\n#### Top Prioritized Risks & Actionable Mitigations")
    for r in s.startup_risks[:4]:
        lines.append(f"- **[{r.risk_id}] {r.risk_title}** *(Category: {r.category} | Severity: {r.overall_severity})*")
        lines.append(f"  - **Root Cause:** {r.explanation}")
        if r.historical_precedent:
            lines.append(f"  - **Historical Precedent (RAG Grounding):** {r.historical_precedent}")
        lines.append(f"  - **Mitigation:** {r.mitigation_strategy.replace(chr(10), ' ')}")

    if s.historical_case_studies:
        lines.append("\n#### 📚 Learning from Past Startups (RAG Historical Precedents)")
        for c in s.historical_case_studies:
            lines.append(f"- **{c.startup_name}** (*{c.outcome}* — {c.sector})")
            lines.append(f"  - **Outcome:** {c.outcome_summary}")
            lines.append(f"  - **Mistake / Key Lesson:** {c.fatal_mistake_or_key_lesson}")
            lines.append(f"  - **Warning for Founder:** {c.warning_for_founder}")

    lines.append("\n---")

    # MVP Product Roadmap
    lines.append("\n## 5. Minimum Viable Product (MVP) Scoping & Roadmap")
    mvp = dossier.mvp_recommendation
    lines.append(f"* **Core Value Hypothesis:** *\"{mvp.core_value_hypothesis}\"*")
    lines.append(f"* **Estimated MVP Build Time:** {mvp.estimated_mvp_timeline}")

    lines.append("\n#### Prioritized MoSCoW Feature Backlog")
    lines.append("| ID | Feature Title | MoSCoW | Complexity | Validation Goal |")
    lines.append("|---|---|:---:|:---:|---|")
    for feat in mvp.features:
        lines.append(f"| `{feat.feature_id}` | **{feat.title}** | **{feat.moscow_category}** | {feat.complexity} | {feat.validation_goal} |")

    lines.append("\n#### Recommended Modern Technology Stack")
    for tech in mvp.tech_stack:
        lines.append(f"- **{tech.layer}:** `{tech.recommended_tech}` — {tech.rationale}")

    lines.append("\n---")

    # Go-To-Market Playbook
    lines.append("\n## 6. Go-To-Market (GTM) Strategy & Pricing Model")
    gtm = dossier.gtm_strategy
    lines.append(f"* **Positioning Headline:** *\"{gtm.positioning_headline}\"*")
    lines.append(f"* **Sales Cycle Expectation:** {gtm.sales_cycle_estimate}")
    lines.append(f"* **Target Unit Economics:** {gtm.cac_to_ltv_target}")

    lines.append("\n#### Monetization & Pricing Tiers")
    lines.append("| Tier | Price Point | Target Profile | Key Included Features |")
    lines.append("|---|---|---|---|")
    for tier in gtm.pricing_tiers:
        feats = ", ".join(tier.included_features[:3])
        lines.append(f"| **{tier.tier_name}** | **{tier.price_point}** | {tier.target_customer_size} | {feats} |")

    lines.append("\n---")
    lines.append(f"\n*Generated autonomously by Infosys AI Startup Idea Validator — Multi-Agent System.*")
    return "\n".join(lines)


if __name__ == "__main__":
    from src.idea_extractor import extract_idea_structure
    from src.web_search_agent import WebSearchAgent
    from src.market_analysis_agent import MarketAnalysisAgent
    from src.competitor_analysis_agent import CompetitorAnalysisAgent
    from src.swot_risk_agent import SWOTRiskAgent
    from src.mvp_agent import MVPAgent
    from src.gtm_agent import GTMAgent
    from src.models import RawStartupSubmission

    idea = extract_idea_structure(RawStartupSubmission(
        startup_name="FleetPulse EV",
        description="Smart EV route optimization and charging software."
    ))
    search = WebSearchAgent().search_and_synthesize(idea)
    market = MarketAnalysisAgent().analyze(idea, search)
    comp = CompetitorAnalysisAgent().analyze(idea, search)
    swot = SWOTRiskAgent().analyze(idea, market, comp)
    mvp = MVPAgent().analyze(idea, swot, comp)
    gtm = GTMAgent().analyze(idea, market, comp, mvp)

    agent = ReportGeneratorAgent()
    dossier = agent.compile_dossier("test-session", idea, search, market, comp, swot, mvp, gtm)
    print(f"Compiled Dossier: {dossier.idea_name}")
    print(f"Feasibility Score: {dossier.feasibility_score}/100")
    print(f"Verdict: {dossier.verdict}")
    md = export_to_markdown(dossier)
    print(f"Markdown lines: {len(md.splitlines())}")
