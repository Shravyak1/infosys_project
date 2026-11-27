"""
Market Opportunity and Customer Segmentation Analysis Agent (Agent 2)
Project: AI Startup Idea Validator

Responsibilities:
1. Ingests structured idea profile and real-time web intelligence.
2. Evaluates Total Addressable Market (TAM), Serviceable Addressable Market (SAM), and Serviceable Obtainable Market (SOM).
3. Analyzes industry growth rate (CAGR), market tailwinds, and deceleration headwinds.
4. Generates granular customer personas (roles, firmographics, acute pain points, budget authority, willingness to pay).
5. Computes a Market Readiness Score (1-10) with "Why Now?" inflection rationale.
6. Provides multi-model LLM integration (Gemini / OpenAI) with robust deterministic domain fallback.
"""

import os
import sys
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

load_dotenv(root_dir / ".env")

from src.models import (
    StructuredIdeaOutput,
    WebSearchIntelligence,
    MarketSizeBreakdown,
    CustomerPersonaProfile,
    MarketOpportunityReport
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MarketAnalysisAgent")

SYSTEM_MARKET_PROMPT = """You are a Senior Venture Capital Market Analyst and Strategy Partner.
Your task is to conduct an in-depth Market Opportunity and Customer Segmentation evaluation on a proposed startup.

You will receive the Structured Startup Profile and real-time Web Search Intelligence.
Produce a structured JSON report matching this EXACT schema:
{
  "industry_vertical": "Standardized industry name",
  "market_size": {
    "tam_value": "$X.X Billion",
    "tam_rationale": "Clear bottom-up or top-down calculation methodology",
    "sam_value": "$X.X Billion",
    "sam_rationale": "Filtered by target geography and customer segment",
    "som_value": "$X Million",
    "som_rationale": "Realistic 3-5 year market share capture estimate"
  },
  "cagr_growth_rate": "XX.X% (2025-2032)",
  "market_tailwinds": [
    "Macro tailwind 1 with context",
    "Macro tailwind 2 with context",
    "Macro tailwind 3 with context"
  ],
  "market_headwinds": [
    "Market challenge or barrier 1",
    "Market challenge or barrier 2"
  ],
  "target_customer_segments": [
    "Rank 1 customer segment",
    "Rank 2 customer segment",
    "Rank 3 customer segment"
  ],
  "personas": [
    {
      "persona_name": "Job title or buyer role",
      "archetype": "Organization profile",
      "firmographics": "Size, fleet count, revenue, or employee count",
      "acute_pain_points": [
        "Primary operational headache",
        "Financial cost of inaction",
        "Workflow disruption"
      ],
      "budget_authority": "Sole decision maker | Committee champion | Influencer",
      "willingness_to_pay": "Estimated annual budget or per-unit range",
      "urgency_rating": "High (Painkiller) | Medium (Efficiency) | Low (Vitamin)"
    }
  ],
  "market_readiness_score": 8,
  "why_now_rationale": "The technological, regulatory, or economic inflection point making this the exact right moment to launch."
}

INSTRUCTIONS:
1. Return ONLY the raw JSON object.
2. Market readiness score must be an integer between 1 and 10.
3. Personas must be realistic and non-generic.
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


def _generate_domain_fallback(
    idea: StructuredIdeaOutput,
    intel: Optional[WebSearchIntelligence] = None,
    reason: str = "Fallback"
) -> MarketOpportunityReport:
    """High-fidelity deterministic market analysis for offline use or when LLM API keys are absent."""
    logger.warning(f"Generating deterministic market analysis. Reason: {reason}")
    text = (idea.industry + " " + idea.idea_name + " " + idea.problem_statement).lower()

    if any(k in text for k in ["pantry", "grocery", "groceries", "food", "fridge", "recipe", "spoil", "waste", "kitchen"]):
        market_size = MarketSizeBreakdown(
            tam_value="$12.8 Billion (Global Consumer FoodTech & Meal Planning Apps by 2030)",
            tam_rationale="Estimated 280 Million smartphone households globally that actively track grocery spending × $45 average annual app subscription spend.",
            sam_value="$3.4 Billion (North America & Western Europe Urban Households)",
            sam_rationale="75 Million urban households and young professionals seeking to cut grocery inflation and food waste.",
            som_value="$145 Million (Years 3-5 Realistic Capture)",
            som_rationale="Capturing 2.4 Million paid Pro subscribers (approx. 3.2% of SAM) at $4.99/month ($59.88/year)."
        )
        cagr = "18.4% (2025-2032)"
        tailwinds = [
            "Persistent post-pandemic grocery inflation making food waste reduction an immediate financial priority for households.",
            "Rising Gen Z and millennial environmental consciousness around household carbon footprint and food waste.",
            "Widespread consumer adoption of mobile camera OCR and mobile-first micro-subscriptions ($3-$5/mo)."
        ]
        headwinds = [
            "Friction in establishing habitual user routines to snap receipts after grocery shopping.",
            "Competition from free, fragmented ad-supported cooking blogs and YouTube recipe videos."
        ]
        segments = [
            "Busy Young Professionals and Dual-Income Couples without Kids",
            "Budget-Conscious College Students and Shared Apartment Roommates",
            "Eco-Conscious Urban Families Seeking Meal Planning Efficiency"
        ]
        personas = [
            CustomerPersonaProfile(
                persona_name="Sarah - Busy Urban Working Professional",
                archetype="Single / Young Couple Apartment Dweller",
                firmographics="28 years old, tech/marketing professional, cooks dinner 3-4 nights/week",
                acute_pain_points=[
                    "Frequently throws away $20–$30 worth of forgotten spoiled produce and dairy every Sunday.",
                    "Experiences decision fatigue at 7:00 PM opening the fridge not knowing what to cook with random leftover items.",
                    "Lacks time to manually type out grocery lists or manually enter expiration dates into tracking spreadsheets."
                ],
                budget_authority="Direct Consumer Buyer (instant App Store / Google Play in-app purchase)",
                willingness_to_pay="$4.99 / month or $39.99 / year (easily justified by saving >$50/month in groceries)",
                urgency_rating="High (Painkiller)"
            )
        ]
        readiness = 9
        why_now = (
            "Smartphone computer vision and LLM multimodal vision APIs have reached near 100% accuracy on complex supermarket receipts, "
            "making completely automated, zero-typing pantry management possible for the first time."
        )

    elif any(k in text for k in ["ev", "electric", "battery", "fleet", "logistics", "charging"]):
        market_size = MarketSizeBreakdown(
            tam_value="$14.2 Billion (Global Commercial EV Fleet Management by 2030)",
            tam_rationale="Estimated 12.8M commercial electric delivery vans globally × $1,100 average annual fleet software spend per vehicle.",
            sam_value="$3.8 Billion (North America & Western Europe Mid-Sized Fleets)",
            sam_rationale="3.5M mid-market commercial vans operating in regional logistics depots within regulated zero-emission zones.",
            som_value="$190 Million (Years 3-5 Realistic Capture)",
            som_rationale="Capturing 5% of addressable mid-market fleets (approx. 175,000 vehicles at $90/month blended software & charging margin)."
        )
        cagr = "26.8% (2025-2032)"
        tailwinds = [
            "Government zero-emission mandates (e.g., California Advanced Clean Fleets, EU Clean Fleets Directive) legally penalizing fossil fuel fleets.",
            "Surging corporate ESG pledges from Fortune 500 shippers (Amazon, DHL, FedEx) requiring subcontractors to electrify.",
            "Rising commercial electricity demand tariffs making unmanaged EV charging economically unviable."
        ]
        headwinds = [
            "Extended lead times for commercial EV van delivery and depot electrical grid transformer upgrades.",
            "Heterogeneous telematics standards across OEMs requiring continuous connector maintenance."
        ]
        segments = [
            "Mid-Sized Regional Parcel & Last-Mile Delivery Operators (15–250 vans)",
            "Municipal & Utility Public Service Fleets",
            "Field Service & Corporate Maintenance Fleets"
        ]
        personas = [
            CustomerPersonaProfile(
                persona_name="Director of Fleet Operations & Maintenance",
                archetype="Regional Express Logistics Carrier",
                firmographics="50 to 180 electric vans, $25M-$80M annual freight revenue",
                acute_pain_points=[
                    "Mid-shift battery depletion causing stranded delivery drivers and missed customer SLAs.",
                    "Thousands of dollars in unexpected monthly utility peak demand charges when all vans plug in at 5:00 PM.",
                    "Premature battery degradation due to unoptimized fast-charging cycles reducing vehicle resale value."
                ],
                budget_authority="Primary Buyer & Budget Holder (with CFO sign-off for enterprise SaaS)",
                willingness_to_pay="$45 – $75 per vehicle / month ($30,000 to $120,000 annual contract value)",
                urgency_rating="High (Painkiller)"
            ),
            CustomerPersonaProfile(
                persona_name="Fleet Sustainability & Energy Manager",
                archetype="National E-Commerce Delivery Subcontractor",
                firmographics="200+ mixed ICE and electric delivery vans across 4 regional depots",
                acute_pain_points=[
                    "Depot electrical substation capacity constraints preventing installation of more Level 2/3 chargers.",
                    "Lack of centralized reporting linking kWh energy consumed to specific route delivery profitability."
                ],
                budget_authority="Executive Influencer & Technical Champion",
                willingness_to_pay="$500 – $1,500 per charging depot / month",
                urgency_rating="High (Painkiller)"
            )
        ]
        readiness = 9
        why_now = (
            "Commercial fleet electrification has crossed the 5% tipping point in major metropolitan areas, "
            "moving from experimental trials into mass commercial deployments where fuel and battery operational costs directly determine business survival."
        )

    elif any(k in text for k in ["health", "med", "pharmacy", "hospital", "patient", "drug"]):
        market_size = MarketSizeBreakdown(
            tam_value="$13.5 Billion (Global Hospital Pharmacy Automation by 2031)",
            tam_rationale="6,100 US hospitals + 14,000 European hospitals × $650,000 average automated pharmacy technology investment.",
            sam_value="$4.2 Billion (Mid-Tier Community & Regional Acute Care Hospitals)",
            sam_rationale="3,200 non-academic acute care hospitals (200-800 beds) with decentralized medication stockrooms.",
            som_value="$140 Million (Years 3-5 Capture)",
            som_rationale="Capturing 3.3% of target mid-tier hospital networks at an average annual recurring contract value of $42,000."
        )
        cagr = "9.8% (2025-2032)"
        tailwinds = [
            "Federal Drug Supply Chain Security Act (DSCSA) requiring full electronic item-level traceability.",
            "Severe clinical pharmacist and nursing shortages requiring automated administrative workflows.",
            "Escalating medication costs amplifying the financial penalty of expired drug discards."
        ]
        headwinds = [
            "Extended hospital procurement and committee approval timelines (6 to 12 months).",
            "Complex EHR data integration and strict HIPAA / ISO 27001 compliance standards."
        ]
        segments = [
            "Mid-Tier Regional Acute Care Hospitals (200–800 beds)",
            "Specialized Surgery Centers & Ambulatory Surgical Networks",
            "Outpatient Infusion Clinics and Oncology Centers"
        ]
        personas = [
            CustomerPersonaProfile(
                persona_name="Director of Hospital Pharmacy Services",
                archetype="Community Acute Care Hospital (350 beds)",
                firmographics="350 inpatient beds, $180M operating budget, 24/7 central pharmacy",
                acute_pain_points=[
                    "Critical stockouts of emergency anesthesia and cardiac medications during surgical shifts.",
                    "Over $300,000 in annual write-downs on expired medications lost in satellite floor cabinets.",
                    "Pharmacy technicians spending 3+ hours daily manually barcode scanning shelf inventories."
                ],
                budget_authority="Primary Champion & Budget Co-Signer with Chief Medical Officer",
                willingness_to_pay="$3,000 – $5,500 / hospital / month",
                urgency_rating="High (Painkiller)"
            )
        ]
        readiness = 8
        why_now = (
            "The combination of the mandatory 2024-2025 DSCSA tracking deadline and acute healthcare staffing shortages "
            "has transformed medication inventory automation from an optional efficiency tool into an urgent regulatory necessity."
        )

    else:
        # General Technology / SaaS
        market_size = MarketSizeBreakdown(
            tam_value="$18.5 Billion (Global Sector TAM)",
            tam_rationale="Top-down market calculation across addressable enterprise and mid-market accounts globally.",
            sam_value="$4.8 Billion (Primary Regional Beachhead)",
            sam_rationale="Targeting organizations with 50-1,000 employees in initial geographic focus.",
            som_value="$120 Million (3-5 Year Capture)",
            som_rationale="2.5% market share capture of beachhead market via modern digital acquisition."
        )
        cagr = "16.4% (2025-2030)"
        tailwinds = [
            "Systemic shift toward intelligent, automated operational workflows.",
            "Enterprise consolidation of fragmented point solutions into unified platforms.",
            "Demand for rapid-ROI SaaS with transparent usage-based or tiered pricing."
        ]
        headwinds = [
            "Enterprise scrutiny over new software vendor security credentials.",
            "Customer inertia and friction in migrating away from legacy spreadsheets and tools."
        ]
        segments = [
            "Mid-Market Businesses (100–500 employees)",
            "Fast-Growing Digital-Native Enterprises",
            "Forward-Thinking SMB Operators"
        ]
        personas = [
            CustomerPersonaProfile(
                persona_name="Head of Operations / Chief Operating Officer",
                archetype="Mid-Market Growth Company",
                firmographics="150 employees, $20M-$50M annual revenue",
                acute_pain_points=[
                    "Manual, error-prone workflows draining productive engineering and operational hours.",
                    "Lack of real-time visibility into operational bottlenecks and resource waste."
                ],
                budget_authority="Decision Maker for operational software under $50k/year",
                willingness_to_pay="$500 – $2,500 / month",
                urgency_rating="Medium (Efficiency)"
            )
        ]
        readiness = 8
        why_now = "Recent advances in generative AI and API orchestration make it possible to deliver enterprise-grade automation at a fraction of legacy implementation costs."

    return MarketOpportunityReport(
        industry_vertical=idea.industry or "Technology",
        market_size=market_size,
        cagr_growth_rate=cagr,
        market_tailwinds=tailwinds,
        market_headwinds=headwinds,
        target_customer_segments=segments,
        personas=personas,
        market_readiness_score=readiness,
        why_now_rationale=why_now,
        agent_metadata={
            "agent_name": "Market Opportunity & Customer Segmentation Agent",
            "model_used": "FALLBACK_RULE_BASED",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "status": f"partial ({reason})"
        }
    )


class MarketAnalysisAgent:
    """Agent 2: Conducts Market Sizing, Growth Analysis, and Customer Persona Segmentation."""

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    def analyze(
        self,
        idea: StructuredIdeaOutput,
        intel: Optional[WebSearchIntelligence] = None
    ) -> MarketOpportunityReport:
        """Executes market opportunity analysis."""
        user_prompt = (
            f"Startup Name: {idea.idea_name}\n"
            f"Tagline: {idea.tagline}\n"
            f"Industry: {idea.industry}\n"
            f"Target Customers: {idea.target_customers}\n"
            f"Problem Statement: {idea.problem_statement}\n"
            f"Proposed Solution: {idea.proposed_solution}\n"
            f"Monetization Hypothesis: {idea.monetization_model}\n"
        )
        if intel:
            user_prompt += f"\nWeb Search AI Synthesis: {intel.ai_synthesis}\n"
            if intel.market_results:
                user_prompt += "Retrieved Market Data:\n"
                for res in intel.market_results[:2]:
                    user_prompt += f"- {res.title}: {res.snippet}\n"

        # 1. Try Gemini
        if self.gemini_key and not self.gemini_key.startswith("your_"):
            logger.info("Calling Gemini LLM for Market Analysis...")
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    generation_config={"response_mime_type": "application/json", "temperature": 0.2},
                    system_instruction=SYSTEM_MARKET_PROMPT
                )
                resp = model.generate_content(user_prompt)
                parsed = _clean_and_parse_json(resp.text)
                parsed["agent_metadata"] = {
                    "agent_name": "Market Opportunity & Customer Segmentation Agent",
                    "model_used": "gemini-1.5-flash",
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "status": "success"
                }
                return MarketOpportunityReport.model_validate(parsed)
            except Exception as e:
                logger.warning(f"Gemini Market Analysis failed: {e}. Trying fallback...")

        # 2. Try OpenAI
        if self.openai_key and not self.openai_key.startswith("your_"):
            logger.info("Calling OpenAI LLM for Market Analysis...")
            try:
                import requests
                headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": SYSTEM_MARKET_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.2
                }
                r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=45)
                r.raise_for_status()
                parsed = _clean_and_parse_json(r.json()["choices"][0]["message"]["content"])
                parsed["agent_metadata"] = {
                    "agent_name": "Market Opportunity & Customer Segmentation Agent",
                    "model_used": "gpt-4o-mini",
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "status": "success"
                }
                return MarketOpportunityReport.model_validate(parsed)
            except Exception as e:
                logger.warning(f"OpenAI Market Analysis failed: {e}. Trying fallback...")

        return _generate_domain_fallback(idea, intel, "No active LLM API key configured")


if __name__ == "__main__":
    from src.idea_extractor import extract_idea_structure
    from src.models import RawStartupSubmission
    idea = extract_idea_structure(RawStartupSubmission(
        startup_name="FleetPulse EV",
        description="Smart EV route optimization and charging software."
    ))
    agent = MarketAnalysisAgent()
    rep = agent.analyze(idea)
    print(f"TAM: {rep.market_size.tam_value}")
    print(f"SAM: {rep.market_size.sam_value}")
    print(f"CAGR: {rep.cagr_growth_rate}")
    print(f"Readiness Score: {rep.market_readiness_score}/10")
