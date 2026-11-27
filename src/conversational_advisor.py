"""
Conversational Startup Advisor (Module 9)
Project: AI Startup Idea Validator

Responsibilities:
1. Provides an interactive, persistent conversational AI partner for founders.
2. Context-grounded directly in the complete Validation Dossier Report (Market, Competitors, SWOT, MVP, GTM).
3. Advises on tactical execution: pricing negotiation, objection handling, pilot outreach, competitor defense, tech architecture.
4. Generates contextual follow-up prompt chips for ongoing exploration.
5. Multi-model LLM connectivity (Gemini / OpenAI) with context-grounded fallback reasoning.
"""

import os
import sys
import json
import re
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
    ChatMessage,
    AdvisorChatRequest,
    AdvisorChatResponse,
    ValidationDossierReport
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ConversationalAdvisor")

SYSTEM_ADVISOR_PROMPT = """You are an elite Startup Co-Founder, Y-Combinator Mentor, and Venture Strategist.
You are having an ongoing advisory dialogue with the founder of the startup analyzed below.

You MUST ground your answers in the provided Startup Validation Dossier:
- Market Opportunity (TAM/SAM/SOM, personas, CAGR)
- Competitors & Whitespace (Direct rivals, feature matrix, UVP)
- SWOT & Categorized Risks (Mitigation plans, severity)
- MVP Roadmap (MoSCoW backlog, tech stack, 8-week sprints)
- Go-To-Market Playbook (Channels, pricing tiers, pilot structure)

Provide high-impact, actionable, realistic business and technical advice.
Format your response as valid JSON matching this schema:
{
  "response": "Detailed, formatted markdown response directly answering the founder's inquiry with structured advice, examples, or scripts.",
  "suggested_followups": [
    "Suggested follow-up question chip 1",
    "Suggested follow-up question chip 2",
    "Suggested follow-up question chip 3"
  ],
  "grounded_in_modules": [
    "Market Analysis | Competitor Intelligence | SWOT & Risk | MVP Scoping | Go-To-Market"
  ]
}

STRICT INSTRUCTIONS:
1. Return ONLY the raw JSON object.
2. Be specific, concrete, and quote metrics or features from the report where relevant.
3. Suggest 3 high-leverage follow-up questions tailored to what was just discussed.
"""


def _clean_and_parse_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise ValueError(f"Could not parse valid JSON from LLM: {text[:150]}")


def _generate_grounded_fallback(
    query: str,
    dossier: Optional[ValidationDossierReport]
) -> AdvisorChatResponse:
    """Intelligent fallback advisor grounded directly in the dossier data."""
    q_lower = query.lower()
    idea_name = dossier.idea_name if dossier else "Your Startup"
    uvp = dossier.competitor_analysis.unique_value_proposition if dossier else "your unique value proposition"
    sid = dossier.session_id if dossier else "default"

    # Route based on inquiry topic
    if any(w in q_lower for w in ["price", "pricing", "monetiz", "charge", "cost", "tier"]):
        tiers = dossier.gtm_strategy.pricing_tiers if dossier else []
        t_desc = "\n".join([f"- **{t.tier_name}**: `{t.price_point}` for {t.target_customer_size}." for t in tiers])
        response_text = (
            f"### Pricing & Monetization Strategy for {idea_name}\n\n"
            f"Based on our Go-To-Market validation analysis, here is how we recommend structuring your pricing:\n\n"
            f"{t_desc}\n\n"
            f"#### Key Execution Tactics for Early Pilots:\n"
            f"1. **Never offer free trials to enterprises:** Instead, offer a 30-day paid Proof-of-Value (PoV) or a 100% money-back satisfaction guarantee.\n"
            f"2. **Anchor to Customer Savings:** Your software saves customers money (e.g. 20-30% reduction in operating waste). Position the price point as capturing no more than 20% of the verified savings.\n"
            f"3. **Annual Prepaid Incentive:** Offer a 15-20% discount for annual upfront billing to maximize early cash runway."
        )
        followups = [
            "How do I structure a paid Proof-of-Value agreement?",
            "What objection handling scripts should I use for price resistance?",
            "How does our pricing compare against top incumbents?"
        ]
        modules = ["Go-To-Market", "Market Analysis"]

    elif any(w in q_lower for w in ["competitor", "samsara", "geotab", "omnicell", "rival", "moat", "defend"]):
        comps = [c.name for c in dossier.competitor_analysis.direct_competitors] if dossier else ["Incumbents"]
        whitespace = dossier.competitor_analysis.uncontested_white_space if dossier else "your core focus"
        response_text = (
            f"### Competitive Positioning & Defensibility against {', '.join(comps)}\n\n"
            f"Incumbents have massive brand distribution, but they are generalists burdened by legacy infrastructure. "
            f"Here is how {idea_name} defends its position:\n\n"
            f"1. **Double Down on the Whitespace:** {whitespace}\n"
            f"2. **Your Core UVP:** *\"{uvp}\"*\n"
            f"3. **Integration Over Replacement:** Rather than telling enterprise buyers to rip out existing software, build connectors into their current systems.\n"
            f"4. **Algorithmic Data Moat:** As early customers feed real-world operational data into your models, accuracy compounds, creating a switching barrier incumbents cannot easily replicate."
        )
        followups = [
            "What if an incumbent copies our core feature tomorrow?",
            "How should I position against incumbents in outbound sales emails?",
            "Which integration APIs should we prioritize in Sprint 1?"
        ]
        modules = ["Competitor Intelligence", "SWOT & Risk"]

    elif any(w in q_lower for w in ["mvp", "feature", "build", "stack", "tech", "roadmap", "timeline"]):
        mvp = dossier.mvp_recommendation if dossier else None
        must_haves = [f.title for f in mvp.features if f.moscow_category == "Must-Have"] if mvp else ["Core Engine"]
        response_text = (
            f"### MVP Scoping & Engineering Roadmap for {idea_name}\n\n"
            f"The goal of your MVP is **not** to build a complete product — it is to validate the Core Value Hypothesis:\n"
            f"> *\"{dossier.mvp_recommendation.core_value_hypothesis if dossier else 'Core hypothesis'}\"*\n\n"
            f"#### Non-Negotiable Must-Haves (Weeks 1 to 4):\n"
            f"{chr(10).join([f'- **{m}**' for m in must_haves])}\n\n"
            f"#### Technology Stack Recommendation:\n"
            f"{chr(10).join([f'- **{t.layer}**: `{t.recommended_tech}`' for t in (mvp.tech_stack[:3] if mvp else [])])}\n\n"
            f"**Golden Rule:** Resists requests for custom features from single prospects. Stick strictly to the MoSCoW backlog until 3 pilot customers complete validation."
        )
        followups = [
            "What pre-build validation experiments can I run before writing code?",
            "How should I organize the 8-week sprint roadmap?",
            "What is our biggest technical risk and how do we mitigate it?"
        ]
        modules = ["MVP Scoping", "SWOT & Risk"]

    elif any(w in q_lower for w in ["rag", "past", "history", "historical", "juicero", "cozzo", "webvan", "fast", "mistake", "fatal"]):
        cases = dossier.swot_and_risk.historical_case_studies if (dossier and dossier.swot_and_risk) else []
        if cases:
            c_desc = "\n\n".join([
                f"- **{c.startup_name}** (*{c.outcome}* — {c.sector}):\n  *Mistake/Lesson:* {c.fatal_mistake_or_key_lesson}\n  *Warning for {idea_name}:* {c.warning_for_founder}"
                for c in cases
            ])
        else:
            c_desc = "- Past ventures like Juicero and Webvan collapsed due to premature CapEx and over-engineering without proving consumer retention. Stay asset-light and software-focused."

        response_text = (
            f"### Historical Post-Mortem Precedents (RAG Intelligence) for {idea_name}\n\n"
            f"Our RAG knowledge base analyzed past startup successes and bankruptcies in related domains to warn you about real mistakes others already made:\n\n"
            f"{c_desc}\n\n"
            f"#### How to Avoid Repeating These Mistakes:\n"
            f"1. **Never build custom hardware before software:** Keep the solution 100% on users' existing devices.\n"
            f"2. **Eliminate manual data entry:** As CozZo proved, asking users to type or barcode-scan causes 80%+ drop-off. 1-second OCR or automated ingestion is mandatory.\n"
            f"3. **Organic Virality over Paid Burn:** As Fast proved, spending heavily on paid ads without sustainable retention leads to sudden collapse. Keep LTV:CAC > 4:1 organically."
        )
        followups = [
            "What is our biggest execution risk based on past startups?",
            "How do we prevent customer habit drop-off after week 2?",
            "What should we build in Sprint 1 to de-risk the product?"
        ]
        modules = ["SWOT & Risk", "RAG Grounded Intelligence"]

    elif any(w in q_lower for w in ["risk", "threat", "fail", "mitigat", "danger", "worst"]):
        risks = dossier.swot_and_risk.startup_risks if dossier else []
        r_list = "\n".join([f"- **[{r.category}] {r.risk_title}** *(Severity: {r.overall_severity})*:\n  *Mitigation:* {r.mitigation_strategy.splitlines()[0]}" for r in risks[:3]])
        response_text = (
            f"### Critical Risk Assessment & Proactive Mitigations for {idea_name}\n\n"
            f"Overall Venture Risk Exposure: **{dossier.swot_and_risk.overall_risk_level.upper() if dossier else 'MODERATE'}**\n\n"
            f"Here are the top existential risks identified by our audit:\n\n"
            f"{r_list}\n\n"
            f"#### Immediate Action Recommendation:\n"
            f"{dossier.swot_and_risk.key_strategic_recommendation if dossier else 'Execute pilot testing.'}"
        )
        followups = [
            "How do we handle enterprise customer inertia and long sales cycles?",
            "What compliance and regulatory certifications do we need?",
            "How do we prevent unit economics decay during early pilots?"
        ]
        modules = ["SWOT & Risk"]

    else:
        # General Strategy Consultation
        response_text = (
            f"### Strategic Advisor Consultation for {idea_name}\n\n"
            f"Regarding: *\"{query}\"*\n\n"
            f"Looking across your complete validation dossier (Feasibility Score: **{dossier.feasibility_score if dossier else 80}/100**, Verdict: **{dossier.verdict if dossier else 'PROCEED'}**):\n\n"
            f"1. **Core Strength to Leverage:** {dossier.top_strengths[0] if (dossier and dossier.top_strengths) else 'High-impact value proposition'}.\n"
            f"2. **Primary Next Step:** {dossier.immediate_next_steps[0] if (dossier and dossier.immediate_next_steps) else 'Run customer discovery interviews'}.\n"
            f"3. **Strategic Focus:** Keep burn rate low and focus 80% of your time on customer discovery and pilot commitments before writing production code."
        )
        followups = [
            "What are the top 3 questions I should ask target customers in discovery?",
            "How can I turn this validation report into a seed investor pitch deck?",
            "What is our estimated Customer Acquisition Cost (CAC) and sales cycle?"
        ]
        modules = ["Executive Dossier", "Go-To-Market"]

    return AdvisorChatResponse(
        session_id=sid,
        response=response_text,
        suggested_followups=followups,
        grounded_in_modules=modules
    )


class ConversationalAdvisorAgent:
    """Module 9: Interactive contextual startup advisor."""

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    def chat(
        self,
        request: AdvisorChatRequest,
        dossier: Optional[ValidationDossierReport] = None
    ) -> AdvisorChatResponse:
        """Processes a chat query grounded in validation dossier."""
        dossier_context = ""
        if dossier:
            dossier_context = (
                f"--- STARTUP DOSSIER CONTEXT ---\n"
                f"Idea Name: {dossier.idea_name}\n"
                f"Verdict: {dossier.verdict} (Feasibility Score: {dossier.feasibility_score}/100)\n"
                f"Industry: {dossier.structured_idea.industry}\n"
                f"Problem Statement: {dossier.structured_idea.problem_statement}\n"
                f"TAM: {dossier.market_analysis.market_size.tam_value} | SAM: {dossier.market_analysis.market_size.sam_value}\n"
                f"CAGR: {dossier.market_analysis.cagr_growth_rate}\n"
                f"Unique Value Proposition: {dossier.competitor_analysis.unique_value_proposition}\n"
                f"Whitespace: {dossier.competitor_analysis.uncontested_white_space}\n"
                f"Overall Risk Level: {dossier.swot_and_risk.overall_risk_level}\n"
                f"Core Hypothesis: {dossier.mvp_recommendation.core_value_hypothesis}\n"
                f"Recommended Tech Stack: {', '.join([t.recommended_tech for t in dossier.mvp_recommendation.tech_stack[:3]])}\n"
                f"Pricing Tiers: {', '.join([t.tier_name + ': ' + t.price_point for t in dossier.gtm_strategy.pricing_tiers])}\n"
            )

        history_text = ""
        if request.history:
            history_text = "\n--- RECENT CONVERSATION HISTORY ---\n"
            for msg in request.history[-4:]:
                history_text += f"{msg.role.upper()}: {msg.content}\n"

        user_content = f"{dossier_context}\n{history_text}\nFOUNDER QUESTION: {request.message}\n"

        # 1. Try Gemini
        if self.gemini_key and not self.gemini_key.startswith("your_"):
            logger.info("Engaging Gemini LLM for Conversational Advisor...")
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    generation_config={"response_mime_type": "application/json", "temperature": 0.3},
                    system_instruction=SYSTEM_ADVISOR_PROMPT
                )
                resp = model.generate_content(user_content)
                parsed = _clean_and_parse_json(resp.text)
                return AdvisorChatResponse(
                    session_id=request.session_id,
                    response=parsed.get("response", ""),
                    suggested_followups=parsed.get("suggested_followups", []),
                    grounded_in_modules=parsed.get("grounded_in_modules", ["Executive Dossier"])
                )
            except Exception as e:
                logger.warning(f"Gemini Advisor failed: {e}. Falling back to deterministic advisor...")

        # 2. Try OpenAI
        if self.openai_key and not self.openai_key.startswith("your_"):
            logger.info("Engaging OpenAI LLM for Conversational Advisor...")
            try:
                import requests
                headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": SYSTEM_ADVISOR_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3
                }
                r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
                r.raise_for_status()
                parsed = _clean_and_parse_json(r.json()["choices"][0]["message"]["content"])
                return AdvisorChatResponse(
                    session_id=request.session_id,
                    response=parsed.get("response", ""),
                    suggested_followups=parsed.get("suggested_followups", []),
                    grounded_in_modules=parsed.get("grounded_in_modules", ["Executive Dossier"])
                )
            except Exception as e:
                logger.warning(f"OpenAI Advisor failed: {e}. Falling back to deterministic advisor...")

        return _generate_grounded_fallback(request.message, dossier)


if __name__ == "__main__":
    from src.idea_extractor import extract_idea_structure
    from src.models import RawStartupSubmission
    from src.report_generator_agent import ReportGeneratorAgent
    from src.web_search_agent import WebSearchAgent
    from src.market_analysis_agent import MarketAnalysisAgent
    from src.competitor_analysis_agent import CompetitorAnalysisAgent
    from src.swot_risk_agent import SWOTRiskAgent
    from src.mvp_agent import MVPAgent
    from src.gtm_agent import GTMAgent

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
    dossier = ReportGeneratorAgent().compile_dossier("test-session", idea, search, market, comp, swot, mvp, gtm)

    advisor = ConversationalAdvisorAgent()
    req = AdvisorChatRequest(session_id="test-session", message="How should I price the initial commercial pilot?")
    res = advisor.chat(req, dossier)
    print(f"Response: {res.response[:150]}...")
    print(f"Followups: {res.suggested_followups}")
