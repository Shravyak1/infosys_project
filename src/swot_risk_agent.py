"""
SWOT and Risk Analysis Agent (Agent 4 in Multi-Agent Pipeline)
Project: AI Startup Idea Validator

Responsibilities:
1. Ingest structured startup idea profiles (and optional market/competitor intelligence).
2. Identify internal Strengths and Weaknesses, plus external Opportunities and Threats.
3. Generate categorized startup risks with root-cause explanations and actionable mitigation strategies.
4. Output structured, schema-validated JSON conforming to SWOTAndRiskReport.
5. Provide multi-model LLM connectivity (Google Gemini, OpenAI) with a robust deterministic fallback.
"""

import os
import sys
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from pydantic import BaseModel

from dotenv import load_dotenv

# Ensure project root is on sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

load_dotenv(root_dir / ".env")

from src.models import (
    StructuredIdeaOutput,
    RawStartupSubmission,
    SWOTItem,
    SWOTAnalysis,
    StartupRisk,
    SWOTAndRiskReport,
    HistoricalPrecedentCase,
)
from src.rag_startup_knowledge import rag_engine

# Configure module logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SWOTRiskAgent")


# ---------------------------------------------------------------------------
# Prompt Engineering for SWOT and Risk Analysis
# ---------------------------------------------------------------------------
SYSTEM_SWOT_RISK_PROMPT = """You are an elite Venture Capital Partner, Chief Risk Officer, and Startup Strategist.
Your mission is to perform a rigorous, enterprise-grade SWOT Analysis and Startup Risk Evaluation on a proposed startup concept.

You will receive:
1. Startup Name, Industry, Target Customers
2. Problem Statement and Proposed Solution
3. Key Features / Capabilities
4. Optional Market and Competitor Intelligence

You MUST produce a comprehensive, structured evaluation following this exact JSON schema:

{
  "idea_name": "Name of the startup",
  "industry": "Primary industry vertical",
  "executive_summary": "A concise, high-impact 2-3 paragraph synthesis of the startup's viability, strategic position, and risk posture.",
  "swot_analysis": {
    "strengths": [
      {
        "point": "Concise strength title",
        "explanation": "Detailed explanation of why this internal capability is a competitive advantage",
        "strategic_implication": "How this strength translates into defensibility, margin expansion, or velocity"
      }
    ],
    "weaknesses": [
      {
        "point": "Concise weakness title",
        "explanation": "Detailed explanation of this internal deficit, resource limitation, or operational vulnerability",
        "strategic_implication": "Risk of execution stall, increased burn rate, or client acquisition friction"
      }
    ],
    "opportunities": [
      {
        "point": "Concise opportunity title",
        "explanation": "Detailed explanation of external industry tailwinds, regulatory shifts, or unmet customer segments",
        "strategic_implication": "Growth vectors, expansion paths, or partner distribution leverage"
      }
    ],
    "threats": [
      {
        "point": "Concise threat title",
        "explanation": "Detailed explanation of external competitive moves, incumbent retaliation, or macro risks",
        "strategic_implication": "Potential margin compression, customer churn, or existential market disruption"
      }
    ]
  },
  "startup_risks": [
    {
      "risk_id": "RISK-01",
      "category": "Category name (e.g., Technical Feasibility, Market & Adoption, Regulatory & Compliance, Financial & Runway, Competitive Defensibility, Operational & Execution)",
      "risk_title": "Descriptive, concrete title of the risk",
      "likelihood": "High | Medium | Low",
      "impact": "High | Medium | Low",
      "overall_severity": "Critical | High | Medium | Low",
      "explanation": "Thorough root-cause analysis explaining how this risk manifests, trigger events, and consequences if unmanaged",
      "mitigation_strategy": "Actionable, concrete step-by-step mitigation plan, architectural safeguards, pilot milestones, or contingency protocols"
    }
  ],
  "overall_risk_level": "Low | Moderate | High | Critical",
  "key_strategic_recommendation": "The single most critical proactive action or pilot experiment the founders must execute immediately to de-risk the venture."
}

CRITICAL INSTRUCTIONS:
1. Provide at least 3-4 distinct points for EACH SWOT quadrant (Strengths, Weaknesses, Opportunities, Threats).
2. Provide at least 4-6 granular, non-generic startup risks covering at least:
   - Technical Feasibility (e.g. data silos, hardware integration, AI accuracy/drift, API rate limits)
   - Market & Adoption (e.g. enterprise inertia, switching costs, budget cycles)
   - Regulatory & Compliance (e.g. data privacy, grid tariffs, government safety standards)
   - Financial & Unit Economics (e.g. CAC vs LTV mismatch, high upfront hardware/compute costs)
   - Competitive Defensibility (e.g. legacy incumbents bundling copycat tools)
3. For EVERY risk, provide a practical, realistic, step-by-step mitigation strategy.
4. Output MUST BE strictly raw valid JSON. Do not include markdown code fences (```json ... ```) or conversational commentary.
"""


# ---------------------------------------------------------------------------
# Utility: Clean & Parse JSON
# ---------------------------------------------------------------------------
def clean_and_parse_json(raw_text: str) -> Dict[str, Any]:
    """
    Sanitizes LLM output to guarantee valid JSON:
    - Strips markdown fences (```json ... ```)
    - Locates outermost JSON boundaries if conversational noise exists.
    """
    text = raw_text.strip()
    
    # Remove markdown code fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE).strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise ValueError(f"Could not parse valid JSON from LLM output: {raw_text[:160]}...")


# ---------------------------------------------------------------------------
# LLM Providers (Google Gemini & OpenAI)
# ---------------------------------------------------------------------------
def _call_gemini_api(system_prompt: str, user_prompt: str, api_key: str) -> str:
    """Invokes Google Gemini API with JSON enforcement."""
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.25,
        },
        system_instruction=system_prompt,
    )
    response = model.generate_content(user_prompt)
    return response.text


def _call_openai_api(system_prompt: str, user_prompt: str, api_key: str) -> str:
    """Invokes OpenAI Chat Completion API."""
    import requests
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.25
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Deterministic Fallback Generator
# ---------------------------------------------------------------------------
def _generate_deterministic_fallback(
    idea_dict: Dict[str, Any], 
    reason: str,
    market_context: Optional[Dict[str, Any]] = None,
    competitor_context: Optional[Dict[str, Any]] = None
) -> SWOTAndRiskReport:
    """
    Generates a high-fidelity, domain-tailored SWOT analysis and risk assessment
    when no API key is supplied or when LLM services encounter network/quota errors.
    Ensures zero runtime crashes in automated tests and offline deployments.
    """
    logger.warning(f"Executing deterministic SWOT & Risk fallback generator. Reason: {reason}")
    
    name = idea_dict.get("idea_name") or "Startup Venture"
    industry = idea_dict.get("industry") or "Technology"
    problem = idea_dict.get("problem_statement") or "Market inefficiencies and manual processes."
    solution = idea_dict.get("proposed_solution") or "An intelligent automated platform."
    customers = idea_dict.get("target_customers") or "Commercial customers and enterprises."
    features = idea_dict.get("key_features") or [
        "Predictive analytics and optimization engine",
        "Automated operational workflow scheduling",
        "Centralized real-time telemetry dashboard",
        "Integration APIs for legacy enterprise platforms"
    ]

    # Domain-specific customization for SmartPantry AI / FoodTech or other domains
    is_smartpantry = any(w in (industry + problem + solution).lower() for w in ["pantry", "grocery", "groceries", "food", "fridge", "recipe", "spoil", "waste", "kitchen"])
    is_ev_logistics = any(w in (industry + problem + solution).lower() for w in ["ev", "electric", "fleet", "battery", "logistics", "charging"])

    if is_smartpantry:
        strengths = [
            SWOTItem(
                point="Zero-Friction Receipt Photo Ingestion (Instant OCR)",
                explanation=f"{name} removes the #1 barrier of kitchen management apps by turning a 1-second grocery receipt photo into a categorized digital pantry inventory with auto-estimated expiration dates.",
                strategic_implication="Dramatically increases daily active retention compared to competitors that require manual typing."
            ),
            SWOTItem(
                point="Perishable-First Dynamic Recipe Generation",
                explanation="Algorithmic engine prioritizes ingredients expiring within 48 hours, suggesting quick 15-minute meals that directly prevent food waste.",
                strategic_implication="Creates immediate, tangible value every time a user saves an ingredient from the trash."
            ),
            SWOTItem(
                point="Quantifiable Household Financial ROI ($1,500/Year)",
                explanation="The consumer value proposition is undeniable: saving just one carton of berries and a steak each month completely pays for the $4.99/month subscription 5x over.",
                strategic_implication="Significantly lowers consumer purchase friction on iOS App Store and Google Play."
            ),
            SWOTItem(
                point="Zero Custom Hardware Requirement",
                explanation="Runs entirely on existing consumer smartphone cameras without requiring expensive smart refrigerators or proprietary barcode scanners.",
                strategic_implication="Enables frictionless viral consumer distribution with zero supply chain or manufacturing risk."
            )
        ]

        weaknesses = [
            SWOTItem(
                point="Reliance on User Scanning Habit Formation",
                explanation="Users must remember to take a photo of their receipt after unpacking groceries; breaking this routine causes inventory data to become outdated.",
                strategic_implication="Demands strong onboarding gamification and timely weekend grocery shopping reminder notifications."
            ),
            SWOTItem(
                point="Supermarket Receipt Layout & Abbreviation Variance",
                explanation="Grocery store receipts often use obscure abbreviations (e.g. 'ORG BBY CHK 1LB') that can cause OCR parsing ambiguity.",
                strategic_implication="Requires continuous tuning of fuzzy matching dictionaries and user-assisted one-tap corrections."
            ),
            SWOTItem(
                point="Early-Stage Cold Start Organic Social Traction",
                explanation="Consumer mobile apps require substantial initial viral momentum and app store review volume to maintain low Customer Acquisition Cost (CAC).",
                strategic_implication="Requires disciplined founder-led social video marketing (TikTok/Reels) to seed initial user base."
            )
        ]

        opportunities = [
            SWOTItem(
                point="Grocery Delivery API Integrations (Instacart, Walmart, Amazon Fresh)",
                explanation="Partnering with digital grocery delivery services allows automated digital receipt import without users having to snap physical paper photos.",
                strategic_implication="Transforms product into a completely passive, background pantry intelligence service."
            ),
            SWOTItem(
                point="Brand-Sponsored Smart Recipe Ingredient Placements",
                explanation="Food brands (e.g. pasta sauce, olive oil makers) seek contextual placement in recipe suggestions, unlocking auxiliary B2B advertising revenue.",
                strategic_implication="Enables dual consumer subscription plus high-margin CPG brand advertising revenue."
            ),
            SWOTItem(
                point="Household Sustainability & Carbon Reduction Incentives",
                explanation="Municipalities and corporate wellness programs are actively funding employee consumer initiatives that cut household landfill methane waste.",
                strategic_implication="Opens corporate wellness benefit B2B2C distribution channels."
            )
        ]

        threats = [
            SWOTItem(
                point="Big Tech Native Mobile Feature Bundling",
                explanation="Apple or Google could add basic receipt scanning or kitchen expiration reminders into native Notes or Apple Reminders apps.",
                strategic_implication="Demands maintaining superior culinary recipe intelligence and personalized taste profile moats."
            ),
            SWOTItem(
                point="Smart Refrigerator Manufacturer Native Software",
                explanation="Samsung and LG are embedding interior cameras into luxury refrigerators that detect inventory automatically.",
                strategic_implication="Positions SmartPantry AI as the accessible universal solution for the 95% of households with standard non-smart fridges."
            ),
            SWOTItem(
                point="Consumer Subscription Fatigue",
                explanation="Consumers are increasingly vigilant about canceling non-essential $5 monthly app subscriptions.",
                strategic_implication="Must continuously display visual '$ Saved This Month' metrics on the app homescreen to reinforce ROI."
            )
        ]

        risks = [
            StartupRisk(
                risk_id="RISK-01",
                category="Market & Adoption",
                risk_title="User Habit Churn After Initial Week 1 Novelty Wears Off",
                likelihood="High",
                impact="High",
                overall_severity="High",
                explanation="Consumers frequently download habit-tracking apps enthusiastically but abandon them when manual logging feels like a chore after 2-3 weeks.",
                mitigation_strategy="1. Implement 1-tap lockscreen reminder notifications on Sunday evenings ('Snap your grocery receipt in 5 seconds').\n2. Introduce gamified badges and visual '$ Saved This Month' milestones.\n3. Allow users to simply share digital email e-receipts directly into the app."
            ),
            StartupRisk(
                risk_id="RISK-02",
                category="Technical Feasibility",
                risk_title="Receipt OCR Item Name Ambiguity & Perishable Expiration Variance",
                likelihood="Medium",
                impact="Medium",
                overall_severity="Medium",
                explanation="Supermarket receipts use cryptic abbreviations and produce items often lack clear standardized shelf-life dates, risking inaccurate expiry warnings.",
                mitigation_strategy="1. Implement a crowd-sourced grocery abbreviation normalization database.\n2. Apply conservative expiration estimates for perishables (berries: 4 days, milk: 7 days) with editable user overrides.\n3. Use multimodal LLM vision to extract both text and brand logos."
            ),
            StartupRisk(
                risk_id="RISK-03",
                category="Financial & Runway",
                risk_title="Paid Customer Acquisition Cost (CAC) Exceeding Consumer Lifetime Value (LTV)",
                likelihood="High",
                impact="High",
                overall_severity="Critical",
                explanation="Spending $20+ on Meta or Google paid ads to acquire a $4.99/month subscriber will quickly deplete startup capital.",
                mitigation_strategy="1. Rely primarily on organic viral short-form cooking videos (e.g. 'I made a gourmet dinner out of food about to expire').\n2. Implement a 'Give 1 Month, Get 1 Month Free' friend referral loop.\n3. Partner with food waste TikTok and Instagram creators on performance revenue-share."
            ),
            StartupRisk(
                risk_id="RISK-04",
                category="Competitive Defensibility",
                risk_title="Copycat AI Recipe Apps Launching with Lower Prices",
                likelihood="Medium",
                impact="Medium",
                overall_severity="Medium",
                explanation="Low technical barriers to connecting OpenAI APIs mean developers can easily deploy basic recipe generator apps.",
                mitigation_strategy="1. Build the defensibility moat around household pantry inventory retention and personalized dietary preference graphs.\n2. Deliver seamless receipt OCR which generic recipe wrappers lack.\n3. Secure brand partnerships that provide exclusive discount coupons on grocery restocking."
            )
        ]

        exec_summary = (
            f"{name} targets a massive, universally relatable consumer pain point: the $1,500 in spoiled, forgotten groceries discarded by the average household every year. "
            f"By combining effortless receipt photo scanning with smart expiration alerts and recipe generation, {name} provides an instant, quantifiable return on investment for everyday consumers.\n\n"
            f"The venture's primary execution hurdles lie in consumer habit retention and maintaining organic user acquisition without relying on expensive paid advertising. "
            f"With a lean mobile MVP and viral food waste reduction content, {name} is exceptionally well-positioned to achieve rapid consumer adoption and profitable freemium unit economics."
        )

        rec = (
            "Launch a 2-week viral 'Zero Food Waste Challenge' with 50 beta test households. Track the exact dollar savings achieved per household "
            "and feature the top user transformations in short-form TikTok/Instagram videos to drive organic pre-launch app store waitlists."
        )
        overall_risk = "Moderate"

    elif is_ev_logistics:
        strengths = [
            SWOTItem(
                point="Coupled Battery Telemetry & Dynamic Route Optimization",
                explanation=f"{name} bridges physical battery electrochemistry with dynamic logistics routing, eliminating costly range anxiety and unexpected mid-shift vehicle discharge.",
                strategic_implication="Creates a high-defensibility IP barrier against pure software dispatch platforms lacking deep powertrain understanding."
            ),
            SWOTItem(
                point="Automated Utility Tariff Arbitrage",
                explanation="Integrated off-peak charging schedules exploit localized time-of-use tariffs, yielding direct, measurable 20-35% fuel cost reductions from day one.",
                strategic_implication="Provides rapid, quantifiable ROI for fleet CFOs, significantly shortening initial enterprise sales cycles."
            ),
            SWOTItem(
                point="Hardware-Agnostic Telematics Ingestion",
                explanation="Architected to ingest standard OBD-II/CAN bus protocols and OEM telematics APIs across multi-vendor mixed vehicle fleets.",
                strategic_implication="Prevents hardware vendor lock-in and eliminates expensive physical retrofit requirements during onboarding."
            ),
            SWOTItem(
                point="Purpose-Built Vertical Focus on Commercial Mid-Sized Fleets",
                explanation="Specifically tailored for mid-market fleets (15–250 vehicles) that are overlooked by enterprise telematics giants and underserved by basic GPS trackers.",
                strategic_implication="Enables rapid initial market penetration without directly confronting tier-1 enterprise incumbents."
            )
        ]

        weaknesses = [
            SWOTItem(
                point="Cold-Start Data Asymmetry for Predictive Battery Models",
                explanation="Accurate battery state-of-health (SoH) modeling requires millions of historical driving and thermal data points that early-stage startups lack at launch.",
                strategic_implication="Early prediction variance could risk customer dissatisfaction or require initial conservative buffer thresholds."
            ),
            SWOTItem(
                point="Protracted Enterprise Field Pilot Cycles",
                explanation=f"Selling to {customers} involves multi-stakeholder evaluations (Operations, Safety, IT, Finance) with pilot durations often lasting 3 to 6 months.",
                strategic_implication="Increases working capital burn rate before recurring contract revenue ramps."
            ),
            SWOTItem(
                point="Dependence on OEM API Access and Data Throttling",
                explanation="Automaker cloud APIs (e.g., Ford Pro, Rivian, Stellantis) frequently impose unpredictable access fees, rate limits, or proprietary closed protocols.",
                strategic_implication="Vulnerability to third-party API policy changes or sudden upstream data feed interruptions."
            ),
            SWOTItem(
                point="Absence of Brand Equity in High-Stakes Operations",
                explanation="Fleet managers are inherently risk-averse; routing errors directly cause missed delivery windows and contractual penalties.",
                strategic_implication="High sales friction overcoming customer switching inertia from established legacy providers."
            )
        ]

        opportunities = [
            SWOTItem(
                point="Mandated Corporate Fleet Decarbonization Policies",
                explanation="Government mandates (e.g., EU Clean Fleets Directive, California ACT rule) and corporate ESG targets are forcing thousands of commercial operators to electrify.",
                strategic_implication="Creates sustained, non-discretionary regulatory tailwinds driving inbound enterprise software demand."
            ),
            SWOTItem(
                point="Grid Demand-Response Revenue Monetization (VPPs)",
                explanation="Aggregated fleet battery capacity can participate in utility demand-response and Virtual Power Plant (VPP) balancing markets, creating auxiliary revenue streams.",
                strategic_implication="Allows transitioning from a pure software subscription to a dual SaaS plus energy flexibility revenue-sharing model."
            ),
            SWOTItem(
                point="Strategic Channel Partnerships with EV OEMs and Charger OEMs",
                explanation="Charger manufacturers (e.g., ChargePoint, ABB) and commercial EV dealers seek bundled fleet software to accelerate vehicle deliveries.",
                strategic_implication="Lowers Customer Acquisition Cost (CAC) by unlocking co-selling and pre-installation distribution channels."
            ),
            SWOTItem(
                point="Depot Infrastructure Capacity Constraints",
                explanation="Commercial depots face severe physical electrical transformer limits; smart sequential charging prevents multi-million dollar substation upgrades.",
                strategic_implication="Positions the product not just as route software, but as critical capital expenditure (CapEx) avoidance infrastructure."
            )
        ]

        threats = [
            SWOTItem(
                point="Incumbent Telematics Feature Bundling",
                explanation="Dominant telematics incumbents (e.g., Geotab, Samsara, Verizon Connect) may launch native EV charging modules and bundle them at zero incremental cost.",
                strategic_implication="Could trigger price compression or commoditize basic charge scheduling capabilities."
            ),
            SWOTItem(
                point="OEM Walled Gardens and Native Telematics Dominance",
                explanation="Commercial EV manufacturers are pre-installing proprietary fleet operating systems directly onto vehicle dashboards.",
                strategic_implication="Restricts third-party API access and forces the platform into a defensive interoperability stance."
            ),
            SWOTItem(
                point="Macroeconomic EV Transition Headwinds",
                explanation="Higher commercial vehicle financing costs or delays in EV van deliveries could cause fleet operators to postpone transition timelines.",
                strategic_implication="May temporarily shrink addressable annual vehicle deployment velocity."
            ),
            SWOTItem(
                point="Complex and Unstable Regional Utility Tariffs",
                explanation="Frequent, fragmented restructuring of commercial electric utility time-of-use tariffs and peak demand surcharges across hundreds of utility jurisdictions.",
                strategic_implication="Demands continuous engineering overhead to maintain tariff database accuracy and real-time synchronization."
            )
        ]

        risks = [
            StartupRisk(
                risk_id="RISK-01",
                category="Technical Feasibility",
                risk_title="CAN-Bus & Telematics Protocol Inconsistency Across Vehicle Makes",
                likelihood="High",
                impact="High",
                overall_severity="High",
                explanation="Commercial fleets run heterogeneous mixes of electric delivery vans (e.g., Ford E-Transit, BrightDrop, Mercedes eSprinter). Each OEM exposes distinct telemetry schemas, battery state definitions, and polling frequencies, creating data ingestion failures.",
                mitigation_strategy="1. Implement an abstracted vehicle telematics translation layer with normalized data schemas.\n2. Partner with open telematics API aggregators (e.g., Smartcar, Enode) to offload continuous OEM protocol reverse-engineering.\n3. Build extensive synthetic telemetry simulation harnesses to validate edge-case data variance before deploying to client fleets."
            ),
            StartupRisk(
                risk_id="RISK-02",
                category="Market & Adoption",
                risk_title="High Fleet Manager Operational Inertia & Extended Enterprise Sales Cycles",
                likelihood="High",
                impact="Medium",
                overall_severity="High",
                explanation="Fleet operators prioritize 99.9% uptime over experimental efficiency. If dispatchers perceive software adoption as disruptive to daily delivery schedules, adoption stalls during trials.",
                mitigation_strategy="1. Offer a 30-day non-intrusive 'Shadow Mode' where the software runs in the background analyzing fleet data without altering active routes.\n2. Provide guaranteed ROI reports comparing simulated vs actual energy expenditures.\n3. Deliver dedicated onboarding concierge support for the first two live billing cycles."
            ),
            StartupRisk(
                risk_id="RISK-03",
                category="Regulatory & Compliance",
                risk_title="Commercial Driver Privacy & Location Data Tracking Regulations",
                likelihood="Medium",
                impact="High",
                overall_severity="High",
                explanation="Strict labor union rules and data privacy laws (GDPR in Europe, CCPA in California) restrict driver telemetry, brake monitoring, and granular location surveillance.",
                mitigation_strategy="1. Implement role-based data anonymization and separate vehicle operational telemetry from driver identity metrics.\n2. Achieve SOC 2 Type II and ISO 27001 certifications early.\n3. Publish transparent fleet privacy compliance whitepapers approved by commercial transportation labor legal counsel."
            ),
            StartupRisk(
                risk_id="RISK-04",
                category="Financial & Runway",
                risk_title="Negative Unit Economics During Multi-Month Onboarding Pilots",
                likelihood="Medium",
                impact="High",
                overall_severity="High",
                explanation="Providing custom integration engineering and onsite support for pilot customers before annual contracts execute can deplete early seed runway prematurely.",
                mitigation_strategy="1. Institute a mandatory, paid 'Proof of Value' (PoV) fee structure ($2,500–$5,000 per depot) creditable against future software subscriptions.\n2. Automate self-service telemetry connection to reduce custom implementation engineering hours to under 4 hours per fleet.\n3. Structure annual prepaid billing terms with early renewal incentives."
            ),
            StartupRisk(
                risk_id="RISK-05",
                category="Competitive Defensibility",
                risk_title="Incumbent Telematics Giants Releasing Native EV Add-On Features",
                likelihood="High",
                impact="High",
                overall_severity="Critical",
                explanation="Established market leaders with deep enterprise relationships (e.g., Samsara, Geotab) can copy core EV charging features and bundle them into existing multi-year contracts.",
                mitigation_strategy="1. Defend market position by specializing deeply in battery degradation longevity modeling and bi-directional grid tariff arbitrage—domains generic telematics providers struggle to master.\n2. Build API integrations into existing incumbent platforms rather than forcing rip-and-replace software transitions.\n3. Secure proprietary data network effects where algorithmic accuracy increases with cumulative miles analyzed."
            ),
            StartupRisk(
                risk_id="RISK-06",
                category="Operational & Execution",
                risk_title="Depot Charging Hardware Incompatibility (OCPP Protocol Drift)",
                likelihood="Medium",
                impact="Medium",
                overall_severity="Medium",
                explanation="Different EV charging station vendors implement Open Charge Point Protocol (OCPP) with proprietary quirks, preventing reliable automated remote start/stop charging commands.",
                mitigation_strategy="1. Partner with established EVSE charging management software (CMS) providers to manage direct hardware command dispatch.\n2. Certify compatibility with the top 5 commercial depot charger brands.\n3. Include automatic failover defaults that revert chargers to safe scheduled autonomous charging if cloud connectivity drops."
            )
        ]
        
        exec_summary = (
            f"{name} operates in the high-growth intersection of commercial fleet logistics and electrification ({industry}). "
            f"The company's core value proposition addresses acute operational friction: unpredictable battery degradation and prohibitive "
            f"peak utility charging tariffs. By linking vehicle telemetry directly to dynamic route and charging optimization, {name} possesses "
            f"a compelling opportunity to capture mid-market fleet operators navigating regulatory decarbonization mandates.\n\n"
            f"However, the venture faces immediate strategic challenges, notably lengthy B2B enterprise procurement cycles, OEM API dependency, "
            f"and competitive threats from incumbent telematics giants with massive distribution moats. Achieving defensibility requires proving "
            f"concrete kilowatt-hour cost reductions in live depot pilots, maintaining hardware-agnostic flexibility, and executing an integration-friendly "
            f"go-to-market strategy rather than a rip-and-replace approach."
        )
        
        rec = (
            "Deploy a 30-day non-intrusive 'Shadow Mode' pilot with 3 mid-sized commercial fleets (20–50 vans each) "
            "to benchmark algorithm prediction accuracy against real-world utility tariffs. Use the resulting verified fuel savings "
            "data to create an ironclad enterprise ROI case study prior to scaling paid commercial outreach."
        )
        overall_risk = "Moderate"

    else:
        # General Technology / B2B Startup Fallback
        strengths = [
            SWOTItem(
                point="Targeted Architecture Tailored to Acute Market Problem",
                explanation=f"{name} directly addresses {problem} with a purpose-built feature set, avoiding the bloated complexity of horizontal legacy platforms.",
                strategic_implication="Enables faster time-to-value for early adopters and clear product differentiation."
            ),
            SWOTItem(
                point="Modern Cloud-Native Modular Tech Stack",
                explanation="Built on scalable API microservices and intelligent automation pipelines, allowing agile feature iteration and low maintenance overhead.",
                strategic_implication="Significantly lower infrastructure operating costs compared to legacy enterprise platforms."
            ),
            SWOTItem(
                point="Clear Value Proposition with Direct Measurable ROI",
                explanation=f"The proposed solution provides {customers} with direct time and financial savings by automating manual workflows.",
                strategic_implication="Simplifies enterprise customer justification during budgetary reviews."
            )
        ]

        weaknesses = [
            SWOTItem(
                point="Early-Stage Cold-Start Customer Traction",
                explanation="As an early-stage entrant, the startup lacks recognized enterprise case studies, third-party audits, and brand equity.",
                strategic_implication="Requires higher touch founder-led sales and extended validation cycles to close initial deals."
            ),
            SWOTItem(
                point="Capital and Bandwidth Constraints",
                explanation="Limited early-stage funding restricts simultaneous multi-channel marketing, extensive R&D, and rapid hiring.",
                strategic_implication="Forces disciplined feature prioritization and risks delays if development bottlenecks arise."
            ),
            SWOTItem(
                point="Integration Friction with Heterogeneous Legacy Systems",
                explanation=f"Target customers often rely on fragmented legacy software with limited documentation or closed APIs.",
                strategic_implication="High engineering onboarding effort per customer if self-serve connectors are not prioritized."
            )
        ]

        opportunities = [
            SWOTItem(
                point="Rapid Secular Modernization Across the Vertical",
                explanation=f"The {industry} sector is undergoing systemic digital transformation, creating rising demand for modern, intelligent solutions.",
                strategic_implication="Expands Total Addressable Market (TAM) as laggards are compelled to adopt digital tooling."
            ),
            SWOTItem(
                point="API Ecosystem and Co-Selling Partnerships",
                explanation="Complementary SaaS platforms in adjacent categories seek integration partners to provide end-to-end client experiences.",
                strategic_implication="Opens capital-efficient distribution channels through marketplace listings and reseller arrangements."
            ),
            SWOTItem(
                point="Expansion into Adjacent Customer Tiers",
                explanation="Initial traction in the core beachhead segment can easily be repurposed for upstream enterprise or international markets.",
                strategic_implication="Provides multi-year expansion runway following beachhead product-market fit."
            )
        ]

        threats = [
            SWOTItem(
                point="Incumbent Platform Feature Expansion",
                explanation="Large existing software suites may attempt to clone core features and offer them as free bundled enhancements.",
                strategic_implication="Could pressure pricing margins and lengthen enterprise contract negotiation timelines."
            ),
            SWOTItem(
                point="Macroeconomic IT Budget Scrutiny",
                explanation="Economic uncertainty frequently causes enterprise procurement departments to freeze new software vendors or delay discretionary pilots.",
                strategic_implication="Extends enterprise pipeline velocity and increases sales conversion unpredictability."
            ),
            SWOTItem(
                point="Fast-Follower Competitors & Low Barriers to Generic AI Tools",
                explanation="Proliferation of generative AI APIs lowers the technical threshold for low-cost copycat products.",
                strategic_implication="Demands building proprietary workflow moats and deep data integration defensibility."
            )
        ]

        risks = [
            StartupRisk(
                risk_id="RISK-01",
                category="Market & Adoption",
                risk_title="Customer Inertia & Extended Procurement Cycles",
                likelihood="High",
                impact="High",
                overall_severity="High",
                explanation="Target buyers are accustomed to existing workflows; switching to a new platform requires behavior change and cross-department approvals.",
                mitigation_strategy="1. Minimize upfront switching cost with self-guided data migration tools.\n2. Offer low-risk pilot structures with pre-agreed success criteria.\n3. Provide comprehensive documentation and hands-on onboarding support."
            ),
            StartupRisk(
                risk_id="RISK-02",
                category="Technical Feasibility",
                risk_title="Data Quality and API Integration Brittleness",
                likelihood="Medium",
                impact="High",
                overall_severity="High",
                explanation="Client data may be messy, incomplete, or formatted inconsistently, causing automated pipelines to fail or produce degraded analytical recommendations.",
                mitigation_strategy="1. Implement strict schema validation and data sanitization pipelines at ingestion.\n2. Build automated anomaly detection alerts.\n3. Provide fallback operational modes when third-party data inputs fail."
            ),
            StartupRisk(
                risk_id="RISK-03",
                category="Financial & Runway",
                risk_title="Customer Acquisition Cost (CAC) Outpacing Early Lifetime Value (LTV)",
                likelihood="High",
                impact="High",
                overall_severity="Critical",
                explanation="High paid advertising or outbound SDR expenses can drain cash reserves before achieving repeatable unit economic profitability.",
                mitigation_strategy="1. Focus heavily on inbound organic thought leadership, industry communities, and founder-led sales.\n2. Introduce referral incentives and partner co-marketing.\n3. Track payback periods weekly with a target of under 8 months."
            ),
            StartupRisk(
                risk_id="RISK-04",
                category="Competitive Defensibility",
                risk_title="Commoditization by Incumbent Bundling",
                likelihood="Medium",
                impact="High",
                overall_severity="High",
                explanation="Well-funded incumbents can leverage existing contracts to cross-sell simple versions of this capability.",
                mitigation_strategy="1. Focus on vertical specialization and deep proprietary domain workflows incumbents cannot easily replicate.\n2. Create strong customer switching costs via historical analytics retention and deep operational embedding."
            )
        ]

        exec_summary = (
            f"{name} targets meaningful pain points within {industry}. The platform's automated architecture and clear value proposition "
            f"position it well to attract early adopters among {customers}. However, as an early-stage venture, the company must proactively "
            f"address adoption friction, customer acquisition costs, and defensive positioning against incumbent feature bundling."
        )
        rec = "Execute a tightly controlled beta pilot program with 3-5 target customers to quantify direct operational ROI and harden core integration pipelines before accelerating paid go-to-market investments."
        overall_risk = "Moderate"

    swot = SWOTAnalysis(
        strengths=strengths,
        weaknesses=weaknesses,
        opportunities=opportunities,
        threats=threats
    )

    # RAG Retrieval: Fetch past startup post-mortems and ground risks
    query_text = f"{name} {problem} {solution}"
    historical_cases = rag_engine.retrieve_relevant_cases(
        query_text=query_text,
        industry=industry,
        target_customers=customers,
        top_k=3
    )
    grounded_risks = rag_engine.ground_risks_with_precedents(
        risks=risks,
        idea_name=name,
        industry=industry,
        problem_statement=problem
    )

    metadata = {
        "agent_name": "SWOT & Risk Analysis Agent (RAG-Augmented)",
        "model_used": "FALLBACK_RULE_BASED",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "status": f"partial (Deterministic fallback triggered: {reason})",
        "features_analyzed_count": len(features),
        "risks_evaluated_count": len(grounded_risks),
        "rag_cases_retrieved_count": len(historical_cases)
    }

    return SWOTAndRiskReport(
        idea_name=name,
        industry=industry,
        executive_summary=exec_summary,
        swot_analysis=swot,
        startup_risks=grounded_risks,
        overall_risk_level=overall_risk,
        key_strategic_recommendation=rec,
        historical_case_studies=historical_cases,
        agent_metadata=metadata
    )


# ---------------------------------------------------------------------------
# SWOT & Risk Analysis Agent Class
# ---------------------------------------------------------------------------
class SWOTRiskAgent:
    """
    LLM-Powered SWOT and Risk Analysis Agent.
    Synthesizes internal capabilities and external market forces into a comprehensive
    2x2 SWOT grid and actionable startup risk mitigation scorecard.
    """

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    def _normalize_input(self, idea_input: Union[StructuredIdeaOutput, RawStartupSubmission, Dict[str, Any]]) -> Dict[str, Any]:
        """Normalizes diverse input representations into a unified dictionary."""
        if hasattr(idea_input, "model_dump"):
            return idea_input.model_dump()
        elif hasattr(idea_input, "dict"):
            return idea_input.dict()
        elif isinstance(idea_input, dict):
            return idea_input
        else:
            raise TypeError(f"Unsupported input type for SWOTRiskAgent: {type(idea_input)}")

    def _normalize_context(self, ctx: Optional[Union[BaseModel, Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
        """Safely normalizes Pydantic models or dicts to dictionary format."""
        if ctx is None:
            return None
        if hasattr(ctx, "model_dump"):
            return ctx.model_dump()
        if hasattr(ctx, "dict"):
            return ctx.dict()
        if isinstance(ctx, dict):
            return ctx
        return None

    def _construct_user_prompt(
        self,
        idea_data: Dict[str, Any],
        market_context: Optional[Union[BaseModel, Dict[str, Any]]] = None,
        competitor_context: Optional[Union[BaseModel, Dict[str, Any]]] = None
    ) -> str:
        """Constructs a comprehensive, context-rich prompt for the LLM."""
        m_ctx = self._normalize_context(market_context)
        c_ctx = self._normalize_context(competitor_context)

        prompt_parts = [
            "--- STARTUP CONCEPT PROFILE ---",
            f"Startup Name      : {idea_data.get('idea_name') or idea_data.get('startup_name', 'Unnamed Idea')}",
            f"Industry Vertical : {idea_data.get('industry') or idea_data.get('primary_industry', 'Technology')}",
            f"Target Customers  : {idea_data.get('target_customers', 'Enterprise & Mid-Market')}",
            f"Problem Statement : {idea_data.get('problem_statement', idea_data.get('description', 'N/A'))}",
            f"Proposed Solution : {idea_data.get('proposed_solution', 'N/A')}",
        ]

        # Add key features
        features = idea_data.get("key_features")
        if features and isinstance(features, list):
            prompt_parts.append("\nKey Product Features:")
            for feat in features:
                prompt_parts.append(f"  • {feat}")

        # Add monetization if present
        if idea_data.get("monetization_hypothesis") or idea_data.get("monetization_model"):
            monetization = idea_data.get("monetization_hypothesis") or idea_data.get("monetization_model")
            prompt_parts.append(f"\nMonetization Strategy: {monetization}")

        # Add market intelligence context if provided
        if m_ctx:
            prompt_parts.append("\n--- MARKET INTELLIGENCE CONTEXT ---")
            if "market_size" in m_ctx:
                ms = m_ctx.get("market_size")
                if isinstance(ms, dict):
                    prompt_parts.append(f"Market Sizing: TAM={ms.get('tam_value')} | SAM={ms.get('sam_value')} | SOM={ms.get('som_value')}")
                else:
                    prompt_parts.append(f"Market Sizing: {ms}")
            if "cagr_growth_rate" in m_ctx:
                prompt_parts.append(f"Industry Growth Rate (CAGR): {m_ctx.get('cagr_growth_rate')}")
            if "market_tailwinds" in m_ctx:
                prompt_parts.append(f"Market Tailwinds: {m_ctx.get('market_tailwinds')}")

        # Add competitor intelligence context if provided
        if c_ctx:
            prompt_parts.append("\n--- COMPETITIVE INTELLIGENCE CONTEXT ---")
            if "direct_competitors" in c_ctx:
                direct_names = [c.get("name") if isinstance(c, dict) else str(c) for c in c_ctx.get("direct_competitors", [])]
                prompt_parts.append(f"Direct Competitors: {', '.join(direct_names)}")
            if "uncontested_white_space" in c_ctx:
                prompt_parts.append(f"Market Whitespace: {c_ctx.get('uncontested_white_space')}")
            if "unique_value_proposition" in c_ctx:
                prompt_parts.append(f"Unique Value Proposition: {c_ctx.get('unique_value_proposition')}")

        # Add RAG-retrieved historical startup cases
        query_text = f"{idea_data.get('idea_name', '')} {idea_data.get('problem_statement', '')} {idea_data.get('proposed_solution', '')}"
        rag_cases = rag_engine.retrieve_relevant_cases(
            query_text=query_text,
            industry=idea_data.get('industry', ''),
            target_customers=idea_data.get('target_customers', ''),
            top_k=3
        )
        if rag_cases:
            prompt_parts.append("\n--- HISTORICAL STARTUP POST-MORTEM & SUCCESS CASES (RETRIEVED VIA RAG) ---")
            prompt_parts.append("Learn from past startups that attempted related models. Citing these real mistakes and breakthroughs in your risks and SWOT:")
            for case in rag_cases:
                prompt_parts.append(f"  • {case.startup_name} [{case.outcome} in {case.sector}]: {case.fatal_mistake_or_key_lesson}")
                prompt_parts.append(f"    Founder Warning: {case.warning_for_founder}")

        prompt_parts.append("\nConduct your deep-dive SWOT and Startup Risk analysis and return ONLY valid JSON matching the schema.")
        return "\n".join(prompt_parts)

    def analyze(
        self,
        idea_input: Union[StructuredIdeaOutput, RawStartupSubmission, Dict[str, Any]],
        market_context: Optional[Union[BaseModel, Dict[str, Any]]] = None,
        competitor_context: Optional[Union[BaseModel, Dict[str, Any]]] = None
    ) -> SWOTAndRiskReport:
        """
        Executes the SWOT and Risk Analysis workflow.
        Returns a validated SWOTAndRiskReport Pydantic object.
        """
        idea_data = self._normalize_input(idea_input)
        m_ctx = self._normalize_context(market_context)
        c_ctx = self._normalize_context(competitor_context)
        user_prompt = self._construct_user_prompt(idea_data, m_ctx, c_ctx)

        report_instance: Optional[SWOTAndRiskReport] = None

        # 1. Attempt Google Gemini LLM
        if self.gemini_key and not self.gemini_key.startswith("your_"):
            logger.info("Engaging Google Gemini LLM for SWOT & Risk Analysis...")
            try:
                raw_response = _call_gemini_api(SYSTEM_SWOT_RISK_PROMPT, user_prompt, self.gemini_key)
                parsed_json = clean_and_parse_json(raw_response)
                
                # Attach agent metadata
                parsed_json["agent_metadata"] = {
                    "agent_name": "SWOT & Risk Analysis Agent",
                    "model_used": "gemini-1.5-flash",
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "status": "success",
                    "features_analyzed_count": len(parsed_json.get("swot_analysis", {}).get("strengths", [])),
                    "risks_evaluated_count": len(parsed_json.get("startup_risks", []))
                }
                
                report_instance = SWOTAndRiskReport.model_validate(parsed_json)
                logger.info("Successfully generated SWOT & Risk report via Gemini LLM.")
            except Exception as e:
                logger.warning(f"Gemini LLM call failed: {e}. Attempting secondary fallback...")
                report_instance = None

        # 2. Attempt OpenAI LLM
        if report_instance is None and self.openai_key and not self.openai_key.startswith("your_"):
            logger.info("Engaging OpenAI LLM for SWOT & Risk Analysis...")
            try:
                raw_response = _call_openai_api(SYSTEM_SWOT_RISK_PROMPT, user_prompt, self.openai_key)
                parsed_json = clean_and_parse_json(raw_response)
                
                parsed_json["agent_metadata"] = {
                    "agent_name": "SWOT & Risk Analysis Agent",
                    "model_used": "gpt-4o-mini",
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "status": "success",
                    "features_analyzed_count": len(parsed_json.get("swot_analysis", {}).get("strengths", [])),
                    "risks_evaluated_count": len(parsed_json.get("startup_risks", []))
                }
                
                report_instance = SWOTAndRiskReport.model_validate(parsed_json)
                logger.info("Successfully generated SWOT & Risk report via OpenAI LLM.")
            except Exception as e:
                logger.warning(f"OpenAI LLM call failed: {e}. Falling back to deterministic engine...")
                report_instance = None

        # 3. Deterministic Domain Fallback Engine
        if report_instance is None:
            reason = "No valid GEMINI_API_KEY or OPENAI_API_KEY set in .env" if (not self.gemini_key and not self.openai_key) else "LLM API connection failure"
            report_instance = _generate_deterministic_fallback(
                idea_data,
                reason=reason,
                market_context=market_context,
                competitor_context=competitor_context
            )
        else:
            # Enrich LLM report with RAG historical cases and precedent tags if missing
            if not report_instance.historical_case_studies:
                q_text = f"{idea_data.get('idea_name', '')} {idea_data.get('problem_statement', '')} {idea_data.get('proposed_solution', '')}"
                report_instance.historical_case_studies = rag_engine.retrieve_relevant_cases(
                    query_text=q_text,
                    industry=idea_data.get('industry', ''),
                    target_customers=idea_data.get('target_customers', ''),
                    top_k=3
                )
            report_instance.startup_risks = rag_engine.ground_risks_with_precedents(
                risks=report_instance.startup_risks,
                idea_name=idea_data.get('idea_name', ''),
                industry=idea_data.get('industry', ''),
                problem_statement=idea_data.get('problem_statement', '')
            )

        return report_instance

    def analyze_to_json(
        self,
        idea_input: Union[StructuredIdeaOutput, RawStartupSubmission, Dict[str, Any]],
        market_context: Optional[Dict[str, Any]] = None,
        competitor_context: Optional[Dict[str, Any]] = None,
        indent: int = 2
    ) -> str:
        """
        Executes analysis and directly outputs a formatted JSON string for API integration.
        """
        report = self.analyze(idea_input, market_context, competitor_context)
        return json.dumps(report.model_dump(), indent=indent)


# ---------------------------------------------------------------------------
# Global Agent Helper Function
# ---------------------------------------------------------------------------
def run_swot_and_risk_analysis(
    idea_input: Union[StructuredIdeaOutput, RawStartupSubmission, Dict[str, Any]],
    market_context: Optional[Dict[str, Any]] = None,
    competitor_context: Optional[Dict[str, Any]] = None
) -> SWOTAndRiskReport:
    """Helper entry point for pipeline orchestrators."""
    agent = SWOTRiskAgent()
    return agent.analyze(idea_input, market_context, competitor_context)


# ---------------------------------------------------------------------------
# Interactive CLI Demonstration Runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("      AI STARTUP IDEA VALIDATOR — SWOT & RISK ANALYSIS AGENT")
    print("=" * 80)

    # 1. Load or define sample input
    sample_file = root_dir / "data" / "sample_submission_output.json"
    if sample_file.exists():
        print(f"\n[+] Loading ingested idea from: {sample_file.name}")
        with open(sample_file, "r", encoding="utf-8") as f:
            idea_data = json.load(f)
    else:
        print("\n[+] Using default sample startup: FleetPulse EV")
        idea_data = {
            "idea_name": "FleetPulse EV",
            "problem_statement": "Commercial delivery fleets face unpredictable battery drain, charging delays, and peak electric tariffs during EV transitions.",
            "proposed_solution": "AI-powered dynamic routing, battery state-of-health management, and smart off-peak charging scheduling platform.",
            "target_customers": "Fleet operations managers with 15 to 250 electric delivery vans",
            "industry": "Logistics & CleanTech",
            "key_features": [
                "Dynamic routing and schedule optimization engine",
                "Battery health telemetry and real-time degradation monitor",
                "Automated off-peak charging scheduler with utility tariff integration",
                "Interactive operations dashboard and vehicle analytics"
            ]
        }

    # Optional competitor and market context
    market_context = {
        "market_size": "Commercial EV fleet telematics TAM estimated at $18.4B by 2030 (24.6% CAGR)",
        "tailwinds": "Accelerated by EU Clean Fleets Directive and state-level zero-emission mandates"
    }
    competitor_context = {
        "direct_competitors": "Geotab, Samsara, Ampcontrol, OptimoRoute",
        "competitive_gaps": "Incumbents offer generic GPS tracking but lack battery electrochemistry-aware routing"
    }

    print(f"\nStartup Analyzed : {idea_data.get('idea_name')}")
    print(f"Industry         : {idea_data.get('industry')}")
    print(f"Target Customers : {idea_data.get('target_customers')}")
    print("\n[RUNNING AGENT REASONING ENGINE...]")

    agent = SWOTRiskAgent()
    report = agent.analyze(idea_data, market_context=market_context, competitor_context=competitor_context)

    # Format human-readable presentation in terminal
    print("\n" + "-" * 80)
    print("EXECUTIVE SUMMARY:")
    print("-" * 80)
    print(report.executive_summary)

    print("\n" + "-" * 80)
    print("SWOT MATRIX (4 QUADRANTS):")
    print("-" * 80)

    print("\n[1. STRENGTHS (Internal Advantages)]")
    for s in report.swot_analysis.strengths:
        print(f"  + {s.point}")
        print(f"    Reason: {s.explanation}")
        if s.strategic_implication:
            print(f"    Impact: {s.strategic_implication}")

    print("\n[2. WEAKNESSES (Internal Vulnerabilities)]")
    for w in report.swot_analysis.weaknesses:
        print(f"  - {w.point}")
        print(f"    Reason: {w.explanation}")
        if w.strategic_implication:
            print(f"    Impact: {w.strategic_implication}")

    print("\n[3. OPPORTUNITIES (External Tailwinds)]")
    for o in report.swot_analysis.opportunities:
        print(f"  * {o.point}")
        print(f"    Reason: {o.explanation}")
        if o.strategic_implication:
            print(f"    Impact: {o.strategic_implication}")

    print("\n[4. THREATS (External Hazards)]")
    for t in report.swot_analysis.threats:
        print(f"  ! {t.point}")
        print(f"    Reason: {t.explanation}")
        if t.strategic_implication:
            print(f"    Impact: {t.strategic_implication}")

    print("\n" + "-" * 80)
    print(f"STARTUP RISKS & ACTIONABLE MITIGATION STRATEGIES (Overall Risk: {report.overall_risk_level.upper()}):")
    print("-" * 80)
    for r in report.startup_risks:
        print(f"\n[{r.risk_id}] [{r.category}] {r.risk_title}")
        print(f"  Likelihood: {r.likelihood} | Impact: {r.impact} | Severity: {r.overall_severity}")
        print(f"  Explanation: {r.explanation}")
        print(f"  Mitigation Strategy:\n  {r.mitigation_strategy}")

    print("\n" + "-" * 80)
    print("PRIMARY STRATEGIC RECOMMENDATION:")
    print("-" * 80)
    print(f">>> {report.key_strategic_recommendation}\n")

    # Save structured JSON output for integration
    data_dir = root_dir / "data"
    data_dir.mkdir(exist_ok=True)
    out_file = data_dir / "sample_swot_output.json"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(report.model_dump(), indent=2))

    print(f"[SUCCESS] Structured JSON output saved to: {out_file}")
    print(f"[METADATA] Generated by: {report.agent_metadata.get('model_used')} at {report.agent_metadata.get('generated_at')}")
    print("=" * 80 + "\n")
