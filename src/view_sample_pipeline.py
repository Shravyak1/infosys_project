"""
End-to-End Multi-Agent Pipeline Demonstration Viewer
Project: AI Startup Idea Validator

Demonstrates the execution of all 9 modules and agents:
1. Startup Idea Submission & Intake
2. Web Search & Real-Time Intelligence (Tavily)
3. Market Opportunity & Customer Segmentation Analysis
4. Competitor Discovery & Whitespace Benchmarking
5. SWOT & Categorized Risk Evaluation
6. MVP Feature Recommendation (MoSCoW Framework)
7. Go-To-Market Strategy & Monetization Tiers
8. Executive Startup Validation Dossier (Feasibility Score 0-100)
9. Conversational Startup Advisor Consultation

Usage:
    python src/view_sample_pipeline.py
"""

import sys
import json
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.models import RawStartupSubmission, AdvisorChatRequest
from src.orchestrator import StartupValidationOrchestrator
from src.conversational_advisor import ConversationalAdvisorAgent


def run_full_pipeline_demo():
    border = "=" * 80
    sub_border = "-" * 80

    print("\n" + border)
    print("      AI STARTUP IDEA VALIDATOR — COMPLETE MULTI-AGENT PLATFORM DEMO")
    print("           (9 Modules & Agents Autonomous Pipeline Execution)")
    print(border)

    # 1. Input Idea Submission (Layman-friendly default example)
    sample = RawStartupSubmission(
        startup_name="SmartPantry AI",
        description=(
            "A smart mobile app that tracks grocery expiration dates by snapping a photo of grocery store receipts, "
            "alerts users before food spoils, and automatically suggests quick recipes using ingredients already in the fridge "
            "to stop household food waste and save money."
        ),
        industry="Consumer Tech & FoodTech",
        target_customers="Busy working professionals, college students, and budget-conscious families",
        monetization_hypothesis="Freemium ($4.99/month for Pro unlimited receipt scanning and custom meal plans)",
        known_competitors="SuperCook, CozZo, MyFridgeFood, Paprika"
    )

    print("\n[MODULE 1: STARTUP IDEA SUBMISSION & INTAKE]")
    print(f"  Startup Name     : {sample.startup_name}")
    print(f"  Industry Sector  : {sample.industry}")
    print(f"  Target Customers : {sample.target_customers}")
    print(f"  Monetization Hypo: {sample.monetization_hypothesis}")
    print(f"  Problem Input    : \"{sample.description}\"")

    # Run Orchestrator Pipeline
    print("\n[ORCHESTRATING MULTI-AGENT AGENTIC WORKFLOW...]")
    orchestrator = StartupValidationOrchestrator()

    def tracker(step, total, name, status, details):
        if status == "completed":
            print(f"  [+] [{step}/{total}] {name.ljust(44)} : COMPLETE")

    dossier = orchestrator.run_pipeline(sample, session_id="demo-smartpantry-pipeline", progress_callback=tracker)

    # Step 2: Web Search Intelligence
    print("\n" + sub_border)
    print("[MODULE 2: WEB SEARCH & DATA RETRIEVAL AGENT (TAVILY)]")
    search = dossier.web_intelligence
    print(f"  Target Query    : \"{search.query}\"")
    print(f"  Retrieval Mode  : [{search.mode}]")
    print(f"  Direct Synthesis: {search.ai_synthesis[:180]}...")
    print(f"  Top Retrieved Sources: {len(search.market_results) + len(search.competitor_results)} industry sources retrieved.")

    # Step 3: Market Opportunity & Personas
    print("\n" + sub_border)
    print("[MODULE 3: MARKET OPPORTUNITY & CUSTOMER SEGMENTATION AGENT]")
    m = dossier.market_analysis
    print(f"  TAM (Total Addressable Market)       : {m.market_size.tam_value}")
    print(f"  SAM (Serviceable Addressable Market) : {m.market_size.sam_value}")
    print(f"  SOM (Serviceable Obtainable Market)  : {m.market_size.som_value}")
    print(f"  Forecasted Industry CAGR             : {m.cagr_growth_rate}")
    print(f"  Market Readiness Score               : {m.market_readiness_score} / 10")
    if m.personas:
        p = m.personas[0]
        print(f"  Primary Buyer Persona: {p.persona_name} ({p.firmographics})")
        print(f"    - Urgency: {p.urgency_rating} | Willingness to Pay: {p.willingness_to_pay}")

    # Step 4: Competitor Benchmarking & Whitespace
    print("\n" + sub_border)
    print("[MODULE 4: COMPETITOR DISCOVERY & COMPARISON AGENT]")
    c = dossier.competitor_analysis
    print(f"  Direct Competitors Identified : {', '.join([comp.name for comp in c.direct_competitors])}")
    print(f"  Defensibility Moat Rating     : {c.defensibility_rating.upper()}")
    print(f"  Uncontested Market Whitespace : {c.uncontested_white_space[:140]}...")
    print(f"  Unique Value Proposition (UVP): \"{c.unique_value_proposition}\"")

    # Step 5: SWOT & Risk Analysis (RAG-Augmented)
    print("\n" + sub_border)
    print("[MODULE 5: SWOT & RISK ANALYSIS AGENT (RAG-AUGMENTED)]")
    s = dossier.swot_and_risk
    print(f"  Overall Risk Exposure Level   : {s.overall_risk_level.upper()}")
    print(f"  Top Internal Strength         : {s.swot_analysis.strengths[0].point}")
    print(f"  Top Critical Risk Identified  : [{s.startup_risks[0].risk_id}] {s.startup_risks[0].risk_title} ({s.startup_risks[0].overall_severity} Severity)")
    if s.startup_risks[0].historical_precedent:
        print(f"    - Historical Precedent (RAG): {s.startup_risks[0].historical_precedent}")
    print(f"    - Actionable Mitigation     : {s.startup_risks[0].mitigation_strategy.splitlines()[0]}")
    if s.historical_case_studies:
        print("  RAG Historical Startup Precedents & Lessons:")
        for case in s.historical_case_studies[:2]:
            print(f"    • [{case.outcome}] {case.startup_name}: {case.fatal_mistake_or_key_lesson}")
            print(f"      Warning: {case.warning_for_founder}")
    print(f"  Primary Strategic Directive   : \"{s.key_strategic_recommendation}\"")

    # Step 6: MVP Feature Scope & Roadmap
    print("\n" + sub_border)
    print("[MODULE 6: MVP FEATURE RECOMMENDATION AGENT (MoSCoW)]")
    mvp = dossier.mvp_recommendation
    print(f"  Core Value Hypothesis : \"{mvp.core_value_hypothesis}\"")
    print(f"  Estimated Build Time  : {mvp.estimated_mvp_timeline}")
    must_haves = [f.title for f in mvp.features if f.moscow_category == "Must-Have"]
    print(f"  Must-Have MVP Backlog : {', '.join(must_haves)}")
    print(f"  Recommended Stack     : {mvp.tech_stack[0].recommended_tech} | {mvp.tech_stack[1].recommended_tech}")

    # Step 7: Go-To-Market Playbook
    print("\n" + sub_border)
    print("[MODULE 7: GO-TO-MARKET STRATEGY GENERATION MODULE]")
    gtm = dossier.gtm_strategy
    print(f"  Positioning Headline  : \"{gtm.positioning_headline}\"")
    print(f"  Target Unit Economics : {gtm.cac_to_ltv_target}")
    print(f"  Primary GTM Channel   : {gtm.acquisition_channels[0].channel_name} (Expected CAC: {gtm.acquisition_channels[0].expected_cac})")
    tiers_summary = " | ".join([f"{t.tier_name}: {t.price_point}" for t in gtm.pricing_tiers])
    print(f"  Monetization Tiers    : {tiers_summary}")

    # Step 8: Executive Dossier Compilation & Scoring
    print("\n" + sub_border)
    print("[MODULE 8: STARTUP VALIDATION DOSSIER & SCORING]")
    print(f"  OVERALL STARTUP FEASIBILITY SCORE : {dossier.feasibility_score} / 100")
    print(f"  STRATEGIC VENTURE VERDICT         : {dossier.verdict}")
    print("  Weighted Pillar Scorecard Breakdown:")
    for p in dossier.pillar_scores:
        print(f"    • {p.pillar_name.ljust(35)} : {str(p.score).rjust(3)} / 100  (Weight: {p.weight_percentage}%)")

    # Step 9: Conversational Advisor Turn
    print("\n" + sub_border)
    print("[MODULE 9: CONVERSATIONAL STARTUP ADVISOR (SAMPLE TURN)]")
    advisor = ConversationalAdvisorAgent()
    advisor_query = "How should I structure the initial commercial pilot pricing?"
    print(f"  Founder Inquiry : \"{advisor_query}\"")
    adv_resp = advisor.chat(AdvisorChatRequest(session_id="demo-smartpantry-pipeline", message=advisor_query), dossier)
    print(f"  Advisor Response:")
    for line in adv_resp.response.splitlines()[:6]:
        print(f"    {line}")
    print("    ...")
    print(f"  Suggested Follow-Up Chips: {adv_resp.suggested_followups}")

    print("\n" + border)
    print("  STATUS: ALL 9 MODULES & AGENTS EXECUTED SUCCESSFULLY — SYSTEM READY FOR PRODUCTION")
    print(border + "\n")


if __name__ == "__main__":
    run_full_pipeline_demo()
