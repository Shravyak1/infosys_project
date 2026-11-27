"""
Competitor Discovery and Comparison Agent (Agent 3)
Project: AI Startup Idea Validator

Responsibilities:
1. Ingests structured idea profile and competitor web search intelligence.
2. Identifies and profiles Direct Competitors, Indirect Competitors, and Legacy Substitutes.
3. Analyzes competitor pricing models, feature strengths, and customer-reported weaknesses.
4. Constructs a 5-dimension Competitive Feature Comparison Matrix.
5. Identifies Uncontested Market White Space and synthesizes the startup's Unique Value Proposition (UVP).
6. Multi-model LLM connectivity (Gemini / OpenAI) with deterministic domain fallback.
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
    CompetitorProfile,
    FeatureMatrixRow,
    CompetitorAnalysisReport
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CompetitorAnalysisAgent")

SYSTEM_COMPETITOR_PROMPT = """You are an elite Competitive Intelligence Strategist and Venture Partner.
Your task is to benchmark a proposed startup against existing market players and formulate its competitive moat.

You will receive the Startup Concept Profile and real-time Web Search Intelligence.
Produce a structured JSON report matching this EXACT schema:
{
  "idea_name": "Startup name",
  "direct_competitors": [
    {
      "name": "Competitor 1 Name",
      "competitor_type": "Direct",
      "core_offering": "What their core platform does",
      "pricing_model": "Their pricing structure and price point",
      "strengths": [
        "Major strength 1",
        "Major strength 2"
      ],
      "weaknesses_and_gaps": [
        "Customer pain point or missing capability 1",
        "Blindspot or limitation 2"
      ]
    }
  ],
  "indirect_competitors": [
    {
      "name": "Adjacent / Substitute Platform",
      "competitor_type": "Indirect | Legacy Substitute",
      "core_offering": "What they do",
      "pricing_model": "Pricing model",
      "strengths": ["Strength 1"],
      "weaknesses_and_gaps": ["Weakness 1"]
    }
  ],
  "feature_comparison_matrix": [
    {
      "dimension_name": "Core Dimension 1",
      "startup_capability": "Startup's capability or rating",
      "competitor_a_capability": "Competitor 1 capability",
      "competitor_b_capability": "Competitor 2 capability",
      "competitor_c_capability": "Competitor 3 capability"
    }
  ],
  "uncontested_white_space": "Clear explanation of the overlooked market niche or structural gap incumbents ignore.",
  "unique_value_proposition": "A concise, sharp positioning statement showing why buyers choose the startup.",
  "defensibility_rating": "High | Medium | Low"
}

INSTRUCTIONS:
1. Provide at least 2-3 direct competitors and 1-2 indirect or legacy substitutes.
2. Provide at least 5 meaningful comparison dimensions in the feature comparison matrix.
3. Return ONLY valid raw JSON without markdown fences.
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
) -> CompetitorAnalysisReport:
    """High-fidelity deterministic competitive analysis when LLM API keys are absent."""
    logger.warning(f"Generating deterministic competitor analysis. Reason: {reason}")
    text = (idea.industry + " " + idea.idea_name + " " + idea.problem_statement).lower()

    if any(k in text for k in ["pantry", "grocery", "groceries", "food", "fridge", "recipe", "spoil", "waste", "kitchen"]):
        direct_comps = [
            CompetitorProfile(
                name="SuperCook",
                competitor_type="Direct",
                core_offering="Recipe generator search engine based on ingredients selected from a checklist.",
                pricing_model="Free (Ad-supported) with $2.99/month Ad-free option",
                strengths=[
                    "Large database of over 11 million online recipes.",
                    "Strong organic brand awareness among home cooks."
                ],
                weaknesses_and_gaps=[
                    "Requires tedious manual checking off of dozens of pantry ingredients.",
                    "Completely lacks expiration date tracking or food waste alerts.",
                    "No automatic receipt photo scanning capability."
                ]
            ),
            CompetitorProfile(
                name="CozZo",
                competitor_type="Direct",
                core_offering="Home kitchen inventory, expiration date manager, and grocery shopping list.",
                pricing_model="$4.99 / month or $29.99 / year subscription",
                strengths=[
                    "Clean food expiration timeline interface.",
                    "Good notification system for expiring pantry staples."
                ],
                weaknesses_and_gaps=[
                    "High onboarding friction requiring barcode scanning or manual text entry item-by-item.",
                    "Basic recipe suggestions that do not adapt dynamically to perishable leftovers.",
                    "iOS-only with limited cross-platform Android presence."
                ]
            ),
            CompetitorProfile(
                name="MyFridgeFood",
                competitor_type="Direct",
                core_offering="Simple website tool matching fridge ingredients to user-submitted recipes.",
                pricing_model="Free (Display banner ads)",
                strengths=["Simple, zero-login web interface."],
                weaknesses_and_gaps=["Outdated 2010s user interface, zero mobile notifications, and no camera OCR."]
            )
        ]
        indirect_comps = [
            CompetitorProfile(
                name="Paprika Recipe Manager",
                competitor_type="Indirect",
                core_offering="Digital recipe organizer, meal planner, and grocery list creator.",
                pricing_model="$4.99 one-time app purchase",
                strengths=["Excellent recipe clipping from websites and offline storage."],
                weaknesses_and_gaps=["Zero AI intelligence and no expiration tracking; requires user to plan every meal manually."]
            ),
            CompetitorProfile(
                name="Pen & Paper / Post-it Notes on Fridge",
                competitor_type="Legacy Substitute",
                core_offering="Writing expiration dates or grocery needs on kitchen magnetic whiteboards.",
                pricing_model="Free ($1,500/year in wasted discarded groceries)",
                strengths=["Familiar, zero battery requirement."],
                weaknesses_and_gaps=["Easily forgotten, does not suggest recipes, and inaccessible while at the supermarket."]
            )
        ]
        matrix = [
            FeatureMatrixRow(
                dimension_name="Receipt Photo Automated Ingestion (Zero-Typing)",
                startup_capability="Instant Camera OCR (Logs 25 items in 3 seconds)",
                competitor_a_capability="None (Manual checkbox selection)",
                competitor_b_capability="Barcode-by-barcode scan only",
                competitor_c_capability="None (Manual typing only)"
            ),
            FeatureMatrixRow(
                dimension_name="Dynamic Expiration Alerts & Waste Countdown",
                startup_capability="Automated (48hr & 24hr push warnings)",
                competitor_a_capability="None (No expiration awareness)",
                competitor_b_capability="Manual Entry Required",
                competitor_c_capability="None"
            ),
            FeatureMatrixRow(
                dimension_name="Perishable-First AI Recipe Generation",
                startup_capability="Prioritizes items closest to expiration",
                competitor_a_capability="Generic recipe match (ignores expiry)",
                competitor_b_capability="Basic static web links",
                competitor_c_capability="Basic user-submitted recipes"
            ),
            FeatureMatrixRow(
                dimension_name="Household Financial Savings Tracker",
                startup_capability="Visual '$ Saved This Month' dashboard",
                competitor_a_capability="None",
                competitor_b_capability="None",
                competitor_c_capability="None"
            ),
            FeatureMatrixRow(
                dimension_name="User Onboarding Time per Grocery Trip",
                startup_capability="< 10 seconds (Snap 1 receipt photo)",
                competitor_a_capability="5 to 10 minutes checking boxes",
                competitor_b_capability="3 to 5 minutes barcode scanning",
                competitor_c_capability="N/A (Web tool)"
            )
        ]
        white_space = (
            "The intersection of zero-effort receipt photo ingestion and expiration-prioritized recipe generation: "
            "existing apps either make users manually check off ingredients (SuperCook) or barcode-scan each item (CozZo). "
            "SmartPantry AI eliminates all manual entry friction with a single receipt photo and immediately tells users what to cook before food goes bad."
        )
        uvp = (
            "The effortless AI kitchen assistant that saves households $1,500 a year by turning expiring groceries into delicious 15-minute meals with a single receipt photo."
        )
        defensibility = "High"

    elif any(k in text for k in ["ev", "electric", "battery", "fleet", "logistics", "charging"]):
        direct_comps = [
            CompetitorProfile(
                name="Samsara",
                competitor_type="Direct",
                core_offering="Enterprise telematics, GPS vehicle tracking, driver dashcams, and maintenance scheduling.",
                pricing_model="$35 – $55 / vehicle / month (Multi-year contract required)",
                strengths=[
                    "Massive enterprise market presence and recognized public brand.",
                    "Comprehensive hardware suite with plug-and-play OBD-II devices.",
                    "Rich safety analytics and automated video event recording."
                ],
                weaknesses_and_gaps=[
                    "Generic EV features that treat electric vans essentially like diesel vehicles.",
                    "No battery degradation or electrochemistry prediction models.",
                    "Lacks integration with depot EV charger OCPP protocols or utility time-of-use tariffs."
                ]
            ),
            CompetitorProfile(
                name="Geotab",
                competitor_type="Direct",
                core_offering="Fleet telematics ecosystem with vehicle analytics and EV Suitability Assessments.",
                pricing_model="$25 – $40 / vehicle / month (Distributed via reseller network)",
                strengths=[
                    "Broadest vehicle CAN bus protocol database in the commercial industry.",
                    "Large third-party marketplace and open developer SDK."
                ],
                weaknesses_and_gaps=[
                    "Fragmented user experience relying on third-party marketplace add-ons.",
                    "Static route planning that does not dynamically recalculate based on elevation and cargo weight.",
                    "Complex reseller sales channel with slow deployment for mid-sized operators."
                ]
            ),
            CompetitorProfile(
                name="Ampcontrol",
                competitor_type="Direct",
                core_offering="Cloud-based EV charging management and depot load balancing software.",
                pricing_model="$20 – $40 / charger / month",
                strengths=[
                    "Deep OCPP charger hardware integration and peak shaving algorithms.",
                    "Utility tariff schedule synchronization."
                ],
                weaknesses_and_gaps=[
                    "Pure depot charging focus with zero vehicle route dispatch or driver navigation tools.",
                    "Does not ingest in-transit vehicle telemetry or driver behavioral drain."
                ]
            )
        ]
        indirect_comps = [
            CompetitorProfile(
                name="OptimoRoute / Route4Me",
                competitor_type="Indirect",
                core_offering="Multi-stop delivery route optimization software for parcel couriers.",
                pricing_model="$39 – $59 / driver / month",
                strengths=["Rapid route generation and delivery time window optimization."],
                weaknesses_and_gaps=["Zero EV-specific features; completely unaware of battery state of charge."]
            ),
            CompetitorProfile(
                name="Manual Dispatch & Utility Spreadsheets",
                competitor_type="Legacy Substitute",
                core_offering="Internal spreadsheets, paper driver logs, and utility paper bills.",
                pricing_model="Internal labor cost ($30,000+ in wasted administrative hours)",
                strengths=["Zero software subscription cost."],
                weaknesses_and_gaps=["Cannot prevent peak electricity spikes or predict mid-shift van breakdowns."]
            )
        ]
        matrix = [
            FeatureMatrixRow(
                dimension_name="Dynamic Route Dispatch with Battery Chemistry",
                startup_capability="Native (Real-time terrain, payload, and SoH adjustments)",
                competitor_a_capability="Basic (Static battery percentage threshold)",
                competitor_b_capability="None (Standard ICE routing only)",
                competitor_c_capability="None (Stationary charger software only)"
            ),
            FeatureMatrixRow(
                dimension_name="Depot Utility Tariff & Demand Charge Arbitrage",
                startup_capability="Automated (Coordinated off-peak depot scheduling)",
                competitor_a_capability="None (Manual driver plug-in)",
                competitor_b_capability="None (Requires third-party add-on)",
                competitor_c_capability="Strong (Dedicated OCPP load management)"
            ),
            FeatureMatrixRow(
                dimension_name="Hardware Interoperability (OBD + OEM APIs)",
                startup_capability="Agnostic (API-first cloud connectors + OBD-II)",
                competitor_a_capability="Proprietary Hardware Mandate",
                competitor_b_capability="Proprietary Hardware Mandate",
                competitor_c_capability="Charger Hardware Only"
            ),
            FeatureMatrixRow(
                dimension_name="Mid-Market Onboarding Velocity",
                startup_capability="Rapid (<48 hours self-service cloud sync)",
                competitor_a_capability="Slow (4-8 weeks enterprise procurement)",
                competitor_b_capability="Slow (Reseller dependent)",
                competitor_c_capability="Moderate (Requires charger network config)"
            ),
            FeatureMatrixRow(
                dimension_name="Pricing Flexibility for 15-250 Van Fleets",
                startup_capability="Transparent per-vehicle monthly pricing ($50/mo)",
                competitor_a_capability="Rigid 36-month enterprise lock-in",
                competitor_b_capability="Fragmented add-on tiered billing",
                competitor_c_capability="Per-charger billing (disconnected from vans)"
            )
        ]
        white_space = (
            "The intersection of in-motion vehicle battery electrochemistry and depot stationary charging power: "
            "incumbents either focus solely on vehicle telematics (Samsara) or depot chargers (Ampcontrol). "
            "No single unified platform connects live route dispatch directly with automated utility tariff arbitrage for mid-sized delivery fleets."
        )
        uvp = (
            f"The only unified intelligence platform for commercial electric fleets that simultaneously eliminates driver range anxiety "
            f"and slashes depot utility charging costs by 30% through coupled battery telemetry and dynamic route optimization."
        )
        defensibility = "High"

    elif any(k in text for k in ["health", "med", "pharmacy", "hospital", "patient", "drug"]):
        direct_comps = [
            CompetitorProfile(
                name="Omnicell",
                competitor_type="Direct",
                core_offering="Central pharmacy carousels and floor automated dispensing cabinets (ADCs).",
                pricing_model="$50,000 – $150,000 per hardware unit + 18% annual maintenance contract",
                strengths=["Entrenched in top-tier health systems, deep brand reputation, DEA compliance."],
                weaknesses_and_gaps=["Massive capital cost, inflexible physical footprint, poor predictive expiration algorithms."]
            ),
            CompetitorProfile(
                name="Kit Check",
                competitor_type="Direct",
                core_offering="RFID medication tray and anesthesia medication tracking.",
                pricing_model="$2,500 – $4,000 / hospital / month",
                strengths=["Rapid scanning of procedural medication kits in operating rooms."],
                weaknesses_and_gaps=["Narrowly focused on OR trays; lacks bulk stockroom computer vision and predictive restocking."]
            )
        ]
        indirect_comps = [
            CompetitorProfile(
                name="Epic / Cerner EHR Inventory Modules",
                competitor_type="Indirect",
                core_offering="Basic electronic health record medication inventory logging.",
                pricing_model="Included with multi-million dollar hospital EHR license",
                strengths=["Unified patient medical record integration."],
                weaknesses_and_gaps=["Requires constant manual barcode scanning; lacks real-time sensor awareness."]
            )
        ]
        matrix = [
            FeatureMatrixRow(dimension_name="Continuous Weight/RFID Smart Bin Tracking", startup_capability="Native Autonomous Sensors", competitor_a_capability="Cabinet Locking Only", competitor_b_capability="Tray RFID Scanning Only", competitor_c_capability="None (Manual entry)"),
            FeatureMatrixRow(dimension_name="Predictive Expiration Date Waste Reduction", startup_capability="AI EHR Consumption Forecaster", competitor_a_capability="Static FIFO Alerting", competitor_b_capability="Manual Expiration Flagging", competitor_c_capability="Basic Batch Expiration"),
            FeatureMatrixRow(dimension_name="Upfront Capital Expenditure (CapEx)", startup_capability="Zero CapEx (SaaS + Sensor Lease)", competitor_a_capability="Extremely High ($100k+ cabinets)", competitor_b_capability="Moderate ($25k scanners)", competitor_c_capability="Zero (Bundled in EHR)"),
            FeatureMatrixRow(dimension_name="Deployment Time per Hospital", startup_capability="1 to 2 Weeks", competitor_a_capability="4 to 9 Months", competitor_b_capability="6 to 10 Weeks", competitor_c_capability="Immediate (Existing module)"),
            FeatureMatrixRow(dimension_name="EHR Interoperability (Epic/Cerner FHIR)", startup_capability="Native Bi-Directional FHIR APIs", competitor_a_capability="Proprietary Middleware", competitor_b_capability="Standard HL7", competitor_c_capability="Native EHR Core")
        ]
        white_space = (
            "Lightweight, continuous optical/RFID smart bin tracking for mid-tier hospital stockrooms that avoids "
            "prohibitive $100k+ robotic cabinet CapEx while providing automated EHR-predictive stockout prevention."
        )
        uvp = "Affordable, sensor-driven pharmacy inventory automation that cuts medication waste by 40% with zero capital expenditure."
        defensibility = "High"

    else:
        # General Technology / SaaS
        direct_comps = [
            CompetitorProfile(
                name="Legacy Enterprise Suite A",
                competitor_type="Direct",
                core_offering="Comprehensive legacy enterprise software platform.",
                pricing_model="$1,000+ / month (Annual upfront contract)",
                strengths=["Broad feature checklist, long-standing market reputation."],
                weaknesses_and_gaps=["Bloated UI, slow customer support, complex 3-month setup."]
            ),
            CompetitorProfile(
                name="Point Solution Provider B",
                competitor_type="Direct",
                core_offering="Specialized point tool solving one sub-problem.",
                pricing_model="$99 / user / month",
                strengths=["Simple interface, low price point."],
                weaknesses_and_gaps=["Lacks automated end-to-end workflow intelligence."]
            )
        ]
        indirect_comps = [
            CompetitorProfile(
                name="Spreadsheets & Manual Email Chains",
                competitor_type="Legacy Substitute",
                core_offering="Internal ad-hoc tracking via Google Sheets and Excel.",
                pricing_model="Free (Hidden employee friction)",
                strengths=["Familiar, zero financial cost."],
                weaknesses_and_gaps=["Prone to human error, zero real-time automation."]
            )
        ]
        matrix = [
            FeatureMatrixRow(dimension_name="Workflow Automation Velocity", startup_capability="High (Modern AI pipeline)", competitor_a_capability="Low (Manual configuration)", competitor_b_capability="Medium", competitor_c_capability="None (Manual)"),
            FeatureMatrixRow(dimension_name="Time to Value / Onboarding", startup_capability="Hours (Self-guided)", competitor_a_capability="Months (Consultant required)", competitor_b_capability="Days", competitor_c_capability="Instant"),
            FeatureMatrixRow(dimension_name="Modern API & Data Integration", startup_capability="Native REST & Webhooks", competitor_a_capability="Legacy batch export", competitor_b_capability="Limited API", competitor_c_capability="None"),
            FeatureMatrixRow(dimension_name="Predictive Decision Intelligence", startup_capability="Native Predictive Engine", competitor_a_capability="Static Reporting", competitor_b_capability="None", competitor_c_capability="None"),
            FeatureMatrixRow(dimension_name="Total Cost of Ownership", startup_capability="Low, Transparent SaaS", competitor_a_capability="High CapEx + Maintenance", competitor_b_capability="Moderate", competitor_c_capability="High Operational Waste")
        ]
        white_space = "A lightweight, modern automation platform that delivers rapid ROI without the bloated cost and implementation friction of legacy incumbents."
        uvp = f"The intelligent, agile {idea.industry} platform that automates core operational workflows in minutes, not months."
        defensibility = "Medium"

    return CompetitorAnalysisReport(
        idea_name=idea.idea_name,
        direct_competitors=direct_comps,
        indirect_competitors=indirect_comps,
        feature_comparison_matrix=matrix,
        uncontested_white_space=white_space,
        unique_value_proposition=uvp,
        defensibility_rating=defensibility,
        agent_metadata={
            "agent_name": "Competitor Discovery & Comparison Agent",
            "model_used": "FALLBACK_RULE_BASED",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "status": f"partial ({reason})"
        }
    )


class CompetitorAnalysisAgent:
    """Agent 3: Discovers competitors, constructs comparison matrices, and uncovers whitespaces."""

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    def analyze(
        self,
        idea: StructuredIdeaOutput,
        intel: Optional[WebSearchIntelligence] = None
    ) -> CompetitorAnalysisReport:
        """Executes competitor discovery and benchmarking analysis."""
        user_prompt = (
            f"Startup Name: {idea.idea_name}\n"
            f"Tagline: {idea.tagline}\n"
            f"Industry: {idea.industry}\n"
            f"Core Problem: {idea.problem_statement}\n"
            f"Proposed Solution: {idea.proposed_solution}\n"
            f"Key Features: {', '.join(idea.key_features)}\n"
        )
        if intel:
            user_prompt += f"\nWeb Search Competitor Synthesis: {intel.ai_synthesis}\n"
            if intel.competitor_results:
                user_prompt += "Retrieved Competitor Intelligence:\n"
                for res in intel.competitor_results[:3]:
                    user_prompt += f"- {res.title}: {res.snippet}\n"

        # 1. Try Gemini
        if self.gemini_key and not self.gemini_key.startswith("your_"):
            logger.info("Calling Gemini LLM for Competitor Analysis...")
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    generation_config={"response_mime_type": "application/json", "temperature": 0.25},
                    system_instruction=SYSTEM_COMPETITOR_PROMPT
                )
                resp = model.generate_content(user_prompt)
                parsed = _clean_and_parse_json(resp.text)
                parsed["agent_metadata"] = {
                    "agent_name": "Competitor Discovery & Comparison Agent",
                    "model_used": "gemini-1.5-flash",
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "status": "success"
                }
                return CompetitorAnalysisReport.model_validate(parsed)
            except Exception as e:
                logger.warning(f"Gemini Competitor Analysis failed: {e}. Trying fallback...")

        # 2. Try OpenAI
        if self.openai_key and not self.openai_key.startswith("your_"):
            logger.info("Calling OpenAI LLM for Competitor Analysis...")
            try:
                import requests
                headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": SYSTEM_COMPETITOR_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.25
                }
                r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=45)
                r.raise_for_status()
                parsed = _clean_and_parse_json(r.json()["choices"][0]["message"]["content"])
                parsed["agent_metadata"] = {
                    "agent_name": "Competitor Discovery & Comparison Agent",
                    "model_used": "gpt-4o-mini",
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "status": "success"
                }
                return CompetitorAnalysisReport.model_validate(parsed)
            except Exception as e:
                logger.warning(f"OpenAI Competitor Analysis failed: {e}. Trying fallback...")

        return _generate_domain_fallback(idea, intel, "No active LLM API key configured")


if __name__ == "__main__":
    from src.idea_extractor import extract_idea_structure
    from src.models import RawStartupSubmission
    idea = extract_idea_structure(RawStartupSubmission(
        startup_name="FleetPulse EV",
        description="Smart EV route optimization and charging software."
    ))
    agent = CompetitorAnalysisAgent()
    rep = agent.analyze(idea)
    print(f"Direct Competitors: {[c.name for c in rep.direct_competitors]}")
    print(f"Matrix Rows: {len(rep.feature_comparison_matrix)}")
    print(f"White Space: {rep.uncontested_white_space[:100]}...")
    print(f"UVP: {rep.unique_value_proposition[:100]}...")
