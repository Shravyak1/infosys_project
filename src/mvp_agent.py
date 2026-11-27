"""
MVP Feature Recommendation Agent (Agent 5)
Project: AI Startup Idea Validator

Responsibilities:
1. Ingests structured startup idea, SWOT matrix, competitor gaps, and risk profile.
2. Formulates the core testable Value Hypothesis.
3. Categorizes features using the MoSCoW Prioritization Framework (Must-Have, Should-Have, Could-Have, Won't-Have).
4. Recommends a modern, scalable technology stack with architectural justification.
5. Structures an 8-week agile development sprint roadmap.
6. Defines pre-build validation experiments with quantitative success KPIs.
7. Multi-model LLM connectivity (Gemini / OpenAI) with deterministic domain fallback.
"""

import os
import sys
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv
from pydantic import BaseModel

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

load_dotenv(root_dir / ".env")

from src.models import (
    StructuredIdeaOutput,
    SWOTAndRiskReport,
    CompetitorAnalysisReport,
    MVPFeatureItem,
    TechStackComponent,
    SprintMilestone,
    ValidationExperiment,
    MVPRecommendationReport
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MVPAgent")

SYSTEM_MVP_PROMPT = """You are a Principal Product Manager, Chief Technology Officer, and Agile Product Strategist.
Your mission is to define a lean, laser-focused Minimum Viable Product (MVP) scope for a proposed startup.
Prevent feature bloat and align technical architecture with risk mitigation.

You will receive the Startup Concept Profile, SWOT/Risk Intelligence, and Competitor Whitespaces.
Produce a structured JSON report matching this EXACT schema:
{
  "idea_name": "Startup name",
  "core_value_hypothesis": "The single critical leap-of-faith hypothesis that this MVP must validate.",
  "features": [
    {
      "feature_id": "FEAT-01",
      "title": "Descriptive Feature Name",
      "description": "What this feature specifically does and how the user interacts with it",
      "moscow_category": "Must-Have | Should-Have | Could-Have | Won't-Have (v1.0)",
      "complexity": "Low | Medium | High",
      "validation_goal": "The specific metric or risk this feature tests"
    }
  ],
  "tech_stack": [
    {
      "layer": "Frontend | Backend & APIs | Database & Cache | Cloud & DevOps | AI/ML & 3rd-Party APIs",
      "recommended_tech": "Specific tool or framework (e.g. Next.js, FastAPI, PostgreSQL)",
      "rationale": "Why this technology is optimal for rapid MVP velocity and scale"
    }
  ],
  "roadmap_sprints": [
    {
      "sprint_name": "Weeks 1-2: Architecture & Foundation",
      "deliverables": [
        "Concrete deliverable 1",
        "Concrete deliverable 2"
      ],
      "exit_criteria": "Measurable gate to move to next sprint"
    }
  ],
  "validation_experiments": [
    {
      "experiment_name": "Name of experiment (e.g. Concierge MVP, Smoke Test Landing Page, Paid Pilot LOI)",
      "description": "Step-by-step setup and execution instructions",
      "success_kpi": "Specific numeric threshold that validates proceeding (e.g. 5 LOIs signed, 12% conversion)"
    }
  ],
  "estimated_mvp_timeline": "6 to 8 weeks"
}

INSTRUCTIONS:
1. Provide at least 6-8 features covering all 4 MoSCoW categories (at least 3 Must-Haves, 2 Should-Haves, 1 Could-Have, 2 Won't-Haves).
2. Tech stack must cover 5 distinct architectural layers.
3. Roadmap must span 4 distinct 2-week sprints (8 weeks total).
4. Provide at least 2 concrete validation experiments.
5. Return ONLY raw valid JSON.
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
    swot: Optional[Union[SWOTAndRiskReport, Dict[str, Any]]] = None,
    comp: Optional[Union[CompetitorAnalysisReport, Dict[str, Any]]] = None,
    reason: str = "Fallback"
) -> MVPRecommendationReport:
    """High-fidelity deterministic MVP scoping for offline use."""
    logger.warning(f"Generating deterministic MVP scoping. Reason: {reason}")
    text = (idea.industry + " " + idea.idea_name + " " + idea.problem_statement).lower()

    if any(k in text for k in ["pantry", "grocery", "groceries", "food", "fridge", "recipe", "spoil", "waste", "kitchen"]):
        core_hypo = (
            "Everyday households will regularly scan their grocery receipt if the app automatically alerts them before food spoils "
            "and suggests quick, delicious meals that visibly save them at least $50 a month."
        )
        features = [
            MVPFeatureItem(
                feature_id="FEAT-01",
                title="1-Second Receipt Photo OCR Scanner",
                description="Takes a photo of any grocery supermarket receipt and automatically extracts purchased items, categorizes them, and assigns default shelf-life expiration dates.",
                moscow_category="Must-Have",
                complexity="Medium",
                validation_goal="Over 90% parsing accuracy with zero manual typing required by the user."
            ),
            MVPFeatureItem(
                feature_id="FEAT-02",
                title="Pantry Expiration Timeline & Push Alerts",
                description="Visual digital pantry sorted by expiration proximity with automated push warnings 48h and 24h before perishable items spoil.",
                moscow_category="Must-Have",
                complexity="Low",
                validation_goal="Over 70% of alerted users open the app to cook or freeze the expiring food item."
            ),
            MVPFeatureItem(
                feature_id="FEAT-03",
                title="'Cook It Before It Spoils' Recipe Generator",
                description="AI recipe engine that generates quick 15-to-30 minute meals prioritizing ingredients expiring soonest in the user's fridge.",
                moscow_category="Must-Have",
                complexity="Medium",
                validation_goal="Users cook at least 2 recommended recipes per week using leftover items."
            ),
            MVPFeatureItem(
                feature_id="FEAT-04",
                title="Household '$ Saved This Month' Financial Dashboard",
                description="Tracks every saved ingredient and displays cumulative money saved and food waste avoided in dollars and pounds.",
                moscow_category="Should-Have",
                complexity="Low",
                validation_goal="Direct visual proof of ROI driving freemium subscription conversion."
            ),
            MVPFeatureItem(
                feature_id="FEAT-05",
                title="Smart Grocery Replenishment Shopping List",
                description="Auto-generates shopping checklists as pantry items run low, categorized by supermarket aisle.",
                moscow_category="Should-Have",
                complexity="Low",
                validation_goal="Increases weekly app open frequency during grocery trips."
            ),
            MVPFeatureItem(
                feature_id="FEAT-06",
                title="Dietary Preference & Allergy Customizer",
                description="Filters recipe suggestions based on vegetarian, vegan, gluten-free, keto, or nut allergy restrictions.",
                moscow_category="Could-Have",
                complexity="Low",
                validation_goal="Expands addressability to specialized diet households."
            ),
            MVPFeatureItem(
                feature_id="FEAT-07",
                title="Smart Fridge Hardware Camera IoT Integration (Won't-Have)",
                description="Proprietary refrigerator hardware cameras or barcode lasers. Strictly out of scope for mobile MVP to avoid manufacturing CapEx.",
                moscow_category="Won't-Have (v1.0)",
                complexity="High",
                validation_goal="Prevent expensive hardware trap during software validation."
            ),
            MVPFeatureItem(
                feature_id="FEAT-08",
                title="Direct In-App Grocery Delivery Ordering (Won't-Have)",
                description="Building full fulfillment grocery delivery integration. Deferred to v2.0 after proving core retention.",
                moscow_category="Won't-Have (v1.0)",
                complexity="High",
                validation_goal="Focus solely on food waste elimination."
            )
        ]
        tech_stack = [
            TechStackComponent(layer="Mobile App Frontend", recommended_tech="React Native / Expo with Tailwind CSS", rationale="Rapid cross-platform iOS and Android app release with camera and push notification support from a single codebase."),
            TechStackComponent(layer="Backend & OCR Services", recommended_tech="Python 3.11 / FastAPI & Google Gemini 1.5 Flash Vision API", rationale="High-accuracy, low-cost multimodal image parsing for diverse supermarket receipts with near-instant sub-second latency."),
            TechStackComponent(layer="Database & User Auth", recommended_tech="PostgreSQL (Supabase) + Row-Level Security", rationale="Scalable cloud database with built-in user authentication, instant photo storage, and real-time data sync."),
            TechStackComponent(layer="Cloud & Deployment", recommended_tech="Render / AWS Lambda Serverless", rationale="Low maintenance cost that scales automatically with user traffic surges."),
            TechStackComponent(layer="In-App Purchases & Analytics", recommended_tech="RevenueCat + PostHog Analytics", rationale="Seamless App Store and Google Play subscription management and user funnel tracking.")
        ]
        sprints = [
            SprintMilestone(sprint_name="Weeks 1-2: Camera OCR & Receipt Parsing Engine", deliverables=["Build mobile camera photo capture interface", "Integrate Gemini Vision API receipt parser", "Create grocery item shelf-life database"], exit_criteria="Receipt photo reliably parses 20+ grocery items with correct expiration estimates in <3 seconds."),
            SprintMilestone(sprint_name="Weeks 3-4: Digital Pantry & Expiration Alerting", deliverables=["Develop visual pantry inventory grid", "Implement local push notifications for expiring food", "Add manual one-tap item edit controls"], exit_criteria="User receives accurate 48h expiration notification for perishables."),
            SprintMilestone(sprint_name="Weeks 5-6: AI Recipe Generator & Savings Dashboard", deliverables=["Develop perishable-first recipe recommendation engine", "Build '$ Saved This Month' visual tracker", "Implement basic user profile and dietary preferences"], exit_criteria="Recipe generator produces delicious, step-by-step meals matching at least 3 fridge ingredients."),
            SprintMilestone(sprint_name="Weeks 7-8: Beta Testing & App Store Launch", deliverables=["Onboard 50 beta testing households", "Integrate RevenueCat $4.99/mo freemium paywall", "Submit iOS App Store and Google Play builds"], exit_criteria="Achieve >60% Day-14 user retention across beta cohort.")
        ]
        experiments = [
            ValidationExperiment(
                experiment_name="14-Day 'Fridge Cleanout' Challenge",
                description="Run a 14-day WhatsApp / Telegram pilot with 30 families where they text photos of receipts and expiring fridge items. Manually send them daily 15-minute dinner recipes using their leftover food.",
                success_kpi="Over 80% of families report saving >$30 during the 2 weeks and express willingness to pay $4.99/month for the automated app."
            ),
            ValidationExperiment(
                experiment_name="TikTok / Instagram Recipe Smoke Test Video",
                description="Post 3 short-form videos showing: 'Here is how I made a gourmet pasta dinner using 3 ingredients that were about to spoil in my fridge, saving $25'. Direct viewers to a mobile app waitlist landing page.",
                success_kpi="Obtain >500 email waitlist signups with a landing page conversion rate >15%."
            )
        ]

    elif any(k in text for k in ["ev", "electric", "battery", "fleet", "logistics", "charging"]):
        core_hypo = (
            "Mid-sized delivery fleet operators will pay $50/vehicle/month for automated charge scheduling "
            "if we prove it reduces utility peak demand charges by at least 20% and prevents unexpected battery range exhaustion."
        )
        features = [
            MVPFeatureItem(
                feature_id="FEAT-01",
                title="OBD-II & Cloud Telematics Ingestion Connector",
                description="Ingests real-time vehicle State of Charge (SoC), odometer, and location telemetry via standard OBD-II dongles and Ford/Stellantis cloud APIs.",
                moscow_category="Must-Have",
                complexity="Medium",
                validation_goal="Prove reliable live battery telemetry ingestion across mixed vehicle fleets."
            ),
            MVPFeatureItem(
                feature_id="FEAT-02",
                title="Automated Off-Peak Depot Smart Charging Scheduler",
                description="Calculates lowest-cost charging windows based on localized utility Time-of-Use (TOU) tariffs and depot electrical transformer capacity limits.",
                moscow_category="Must-Have",
                complexity="High",
                validation_goal="Achieve 20-30% verified kWh cost reductions during depot charging."
            ),
            MVPFeatureItem(
                feature_id="FEAT-03",
                title="Dispatch Energy Feasibility & Route Range Checker",
                description="Calculates whether assigned delivery routes can be completed given ambient temperature, payload weight, elevation, and battery degradation.",
                moscow_category="Must-Have",
                complexity="Medium",
                validation_goal="Zero mid-shift battery depletion incidents across trial delivery shifts."
            ),
            MVPFeatureItem(
                feature_id="FEAT-04",
                title="Fleet Operations Executive Dashboard",
                description="Real-time map tracking vehicle battery levels, active charging status, and cumulative electricity dollar savings.",
                moscow_category="Should-Have",
                complexity="Medium",
                validation_goal="Driver and fleet dispatcher daily engagement (>4 logins per week)."
            ),
            MVPFeatureItem(
                feature_id="FEAT-05",
                title="Automated Utility Bill & Carbon Savings PDF Exporter",
                description="Generates weekly reports quantifying peak kilowatt demand avoided, financial savings, and Scope 1 emissions reductions.",
                moscow_category="Should-Have",
                complexity="Low",
                validation_goal="CFO proof of ROI to support annual contract renewal."
            ),
            MVPFeatureItem(
                feature_id="FEAT-06",
                title="Driver Mobile Companion App (iOS / Android)",
                description="Lightweight mobile screen displaying remaining route range buffer and assigned depot charging stall.",
                moscow_category="Could-Have",
                complexity="Medium",
                validation_goal="Driver behavioral adherence to assigned charging stalls."
            ),
            MVPFeatureItem(
                feature_id="FEAT-07",
                title="Autonomous Hardware Charger Microgrid Control (Won't-Have)",
                description="Custom physical battery storage hardware or inverter direct firmware control. Out of scope for MVP; utilize cloud OCPP commands.",
                moscow_category="Won't-Have (v1.0)",
                complexity="High",
                validation_goal="Prevent expensive hardware CapEx trap during software validation."
            ),
            MVPFeatureItem(
                feature_id="FEAT-08",
                title="Multi-National Cross-Border Tax & Toll Rebalancing (Won't-Have)",
                description="Complex international cross-border road taxing. Deferred until regional domestic market traction is secured.",
                moscow_category="Won't-Have (v1.0)",
                complexity="High",
                validation_goal="Eliminate non-core engineering overhead."
            )
        ]
        tech_stack = [
            TechStackComponent(layer="Frontend & Operations UI", recommended_tech="React 18 / Next.js with Tailwind CSS & Mapbox GL", rationale="Fast, reactive geospatial vehicle mapping with minimal state management overhead."),
            TechStackComponent(layer="Backend & Dispatch Services", recommended_tech="Python 3.11 / FastAPI & Celery with Redis", rationale="High-throughput asynchronous telemetry ingestion and algorithmic route calculation."),
            TechStackComponent(layer="Database & Telemetry Storage", recommended_tech="PostgreSQL with TimescaleDB extension", rationale="Native relational structure for customer fleets coupled with hypertable time-series optimization for high-frequency battery telemetry."),
            TechStackComponent(layer="Cloud & DevOps Infrastructure", recommended_tech="Docker, AWS ECS Fargate, AWS RDS, Terraform", rationale="Zero server management, automated horizontal scaling, and secure VPC deployment."),
            TechStackComponent(layer="AI/ML & External Protocols", recommended_tech="Open-source OR-Tools (Routing) + OCPP 1.6J over WebSockets + Smartcar API", rationale="Industry-standard vehicle and EV charger protocols avoiding custom hardware reverse engineering.")
        ]
        sprints = [
            SprintMilestone(sprint_name="Weeks 1-2: Architecture & Telemetry Ingestion", deliverables=["Setup PostgreSQL/TimescaleDB schema", "Build Smartcar & OBD-II ingestion webhook endpoints", "Mock synthetic 50-van telemetry data stream"], exit_criteria="Successfully ingest and store continuous battery telemetry without data drop."),
            SprintMilestone(sprint_name="Weeks 3-4: Core Optimization Engine", deliverables=["Develop Time-of-Use utility tariff calculator", "Implement linear programming charging schedule optimizer", "Build route range feasibility checker"], exit_criteria="Optimizer outputs valid off-peak charging schedules matching depot load constraints."),
            SprintMilestone(sprint_name="Weeks 5-6: UI Dashboard & Depot Dispatcher View", deliverables=["Build interactive Mapbox vehicle tracking UI", "Develop live charging status and depot monitor", "Implement user authentication and fleet role permissions"], exit_criteria="Dispatcher can assign routes and view battery health alerts in under 3 clicks."),
            SprintMilestone(sprint_name="Weeks 7-8: Pilot Deployment & Verification", deliverables=["Deploy 30-day 'Shadow Mode' with 2 pilot fleet partners", "Benchmark calculated utility savings against actual electric bills", "Fix protocol edge cases and collect feedback"], exit_criteria="Demonstrate >20% simulated or real electricity cost savings across pilot fleets.")
        ]
        experiments = [
            ValidationExperiment(
                experiment_name="30-Day Non-Intrusive 'Shadow Mode' Pilot",
                description="Connect software to read-only vehicle telematics and historical utility bills for 2 target delivery fleets. Calculate what electricity costs would have been with automated smart scheduling without altering active delivery operations.",
                success_kpi="Deliver a verified proof-of-savings audit showing >20% cost reduction, converting both fleets to paid beta contracts."
            ),
            ValidationExperiment(
                experiment_name="Interactive ROI Calculator Landing Page Smoke Test",
                description="Launch a targeted landing page with an interactive EV Fleet ROI Calculator for fleet operations directors, promoted via LinkedIn founder outreach.",
                success_kpi="Attain >10 qualified demo requests and 3 signed Letters of Intent (LOIs) from fleets managing >20 vehicles."
            )
        ]

    else:
        # General Technology / SaaS
        core_hypo = f"Target customers will adopt {idea.idea_name} if it automates manual workflows and demonstrates a 3x time-saving ROI within the first 14 days."
        features = [
            MVPFeatureItem(feature_id="FEAT-01", title="Core Automated Workflow Engine", description="Automates the primary end-to-end user workflow.", moscow_category="Must-Have", complexity="High", validation_goal="Prove core workflow reduction from hours to minutes."),
            MVPFeatureItem(feature_id="FEAT-02", title="Central Operational Intelligence Dashboard", description="Real-time visibility into active tasks and key metrics.", moscow_category="Must-Have", complexity="Medium", validation_goal="Daily active user engagement (>60% retention)."),
            MVPFeatureItem(feature_id="FEAT-03", title="Data Import & CSV/API Connectors", description="Self-service onboarding connectors for existing legacy data.", moscow_category="Must-Have", complexity="Medium", validation_goal="Onboarding completed in under 30 minutes without developer assistance."),
            MVPFeatureItem(feature_id="FEAT-04", title="Automated Alerting & Notifications", description="Slack, email, or webhook triggers for critical operational thresholds.", moscow_category="Should-Have", complexity="Low", validation_goal="Immediate notification of high-priority events."),
            MVPFeatureItem(feature_id="FEAT-05", title="Role-Based Access & Team Permissions", description="Admin, editor, and viewer roles for team collaboration.", moscow_category="Should-Have", complexity="Medium", validation_goal="Enterprise multi-seat expansion."),
            MVPFeatureItem(feature_id="FEAT-06", title="Advanced Predictive Analytics (Could-Have)", description="Long-range forecasting algorithms. Deferred until data baseline is established.", moscow_category="Could-Have", complexity="High", validation_goal="Upsell premium tier."),
            MVPFeatureItem(feature_id="FEAT-07", title="Custom On-Premises Deployment (Won't-Have)", description="Self-hosted customer server installations. Strictly cloud-native SaaS for v1.0.", moscow_category="Won't-Have (v1.0)", complexity="High", validation_goal="Eliminate high enterprise support overhead.")
        ]
        tech_stack = [
            TechStackComponent(layer="Frontend", recommended_tech="Next.js 14 / React / Tailwind CSS", rationale="High-performance server rendering with modern UI components."),
            TechStackComponent(layer="Backend & API", recommended_tech="Python FastAPI / Node.js", rationale="Lightweight asynchronous microservices with auto-generated OpenAPI documentation."),
            TechStackComponent(layer="Database", recommended_tech="PostgreSQL (Supabase / AWS RDS)", rationale="ACID compliance, relational integrity, and rapid prototyping."),
            TechStackComponent(layer="Hosting & Cloud", recommended_tech="Vercel (Frontend) + AWS / Render (Backend)", rationale="Cost-effective serverless deployment with automated CI/CD."),
            TechStackComponent(layer="AI & Integrations", recommended_tech="OpenAI / Google Gemini API + Stripe", rationale="Production-ready LLM inference and automated SaaS subscription billing.")
        ]
        sprints = [
            SprintMilestone(sprint_name="Weeks 1-2: Core Data Modeling & Auth", deliverables=["Database schema design", "Authentication and tenant management", "Core API endpoints"], exit_criteria="Verified user signup and authenticated workspace creation."),
            SprintMilestone(sprint_name="Weeks 3-4: Core Workflow Engine", deliverables=["Implement primary processing logic", "Build input ingestion connectors", "Automated validation tests"], exit_criteria="End-to-end data processing succeeds in under 5 seconds."),
            SprintMilestone(sprint_name="Weeks 5-6: UI Dashboard & User Flow", deliverables=["Build interactive dashboard", "Connect frontend to backend APIs", "Implement notification system"], exit_criteria="Alpha testers can complete the primary workflow without guidance."),
            SprintMilestone(sprint_name="Weeks 7-8: Beta Testing & Polishing", deliverables=["Run pilot tests with 3 design partners", "Squash UI bugs and optimize performance", "Setup billing integration"], exit_criteria="First paying or committed beta customer onboarded.")
        ]
        experiments = [
            ValidationExperiment(
                experiment_name="Concierge MVP Pilot",
                description="Manually execute the underlying workflow for 3 target customers using off-the-shelf tools to validate value before writing extensive code.",
                success_kpi="Customers agree to convert to the automated software version once launched."
            ),
            ValidationExperiment(
                experiment_name="High-Intent Landing Page Pre-Sale",
                description="Launch a product landing page with product mockups and a $50 refundable early-access deposit.",
                success_kpi="Obtain 10+ paid deposits or signed Letters of Intent within 2 weeks."
            )
        ]

    return MVPRecommendationReport(
        idea_name=idea.idea_name,
        core_value_hypothesis=core_hypo,
        features=features,
        tech_stack=tech_stack,
        roadmap_sprints=sprints,
        validation_experiments=experiments,
        estimated_mvp_timeline="6 to 8 weeks",
        agent_metadata={
            "agent_name": "MVP Feature Recommendation Agent",
            "model_used": "FALLBACK_RULE_BASED",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "status": f"partial ({reason})"
        }
    )


class MVPAgent:
    """Agent 5: Scopes the Minimum Viable Product, MoSCoW backlog, tech stack, and roadmap."""

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    def analyze(
        self,
        idea: StructuredIdeaOutput,
        swot: Optional[Union[SWOTAndRiskReport, Dict[str, Any]]] = None,
        comp: Optional[Union[CompetitorAnalysisReport, Dict[str, Any]]] = None
    ) -> MVPRecommendationReport:
        """Executes MVP feature scoping and roadmap planning."""
        user_prompt = (
            f"Startup Name: {idea.idea_name}\n"
            f"Tagline: {idea.tagline}\n"
            f"Industry: {idea.industry}\n"
            f"Target Customers: {idea.target_customers}\n"
            f"Problem Statement: {idea.problem_statement}\n"
            f"Proposed Solution: {idea.proposed_solution}\n"
            f"Key Proposed Features: {', '.join(idea.key_features)}\n"
        )
        if comp:
            c_dict = comp.model_dump() if hasattr(comp, "model_dump") else comp
            user_prompt += f"\nCompetitive Whitespace: {c_dict.get('uncontested_white_space')}\n"
            user_prompt += f"Unique Value Proposition: {c_dict.get('unique_value_proposition')}\n"

        if swot:
            s_dict = swot.model_dump() if hasattr(swot, "model_dump") else swot
            user_prompt += f"\nKey Recommendation: {s_dict.get('key_strategic_recommendation')}\n"

        # 1. Try Gemini
        if self.gemini_key and not self.gemini_key.startswith("your_"):
            logger.info("Calling Gemini LLM for MVP Scoping...")
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    generation_config={"response_mime_type": "application/json", "temperature": 0.25},
                    system_instruction=SYSTEM_MVP_PROMPT
                )
                resp = model.generate_content(user_prompt)
                parsed = _clean_and_parse_json(resp.text)
                parsed["agent_metadata"] = {
                    "agent_name": "MVP Feature Recommendation Agent",
                    "model_used": "gemini-1.5-flash",
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "status": "success"
                }
                return MVPRecommendationReport.model_validate(parsed)
            except Exception as e:
                logger.warning(f"Gemini MVP scoping failed: {e}. Trying fallback...")

        # 2. Try OpenAI
        if self.openai_key and not self.openai_key.startswith("your_"):
            logger.info("Calling OpenAI LLM for MVP Scoping...")
            try:
                import requests
                headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": SYSTEM_MVP_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.25
                }
                r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=45)
                r.raise_for_status()
                parsed = _clean_and_parse_json(r.json()["choices"][0]["message"]["content"])
                parsed["agent_metadata"] = {
                    "agent_name": "MVP Feature Recommendation Agent",
                    "model_used": "gpt-4o-mini",
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "status": "success"
                }
                return MVPRecommendationReport.model_validate(parsed)
            except Exception as e:
                logger.warning(f"OpenAI MVP scoping failed: {e}. Trying fallback...")

        return _generate_domain_fallback(idea, swot, comp, "No active LLM API key configured")


if __name__ == "__main__":
    from src.idea_extractor import extract_idea_structure
    from src.models import RawStartupSubmission
    idea = extract_idea_structure(RawStartupSubmission(
        startup_name="FleetPulse EV",
        description="Smart EV route optimization and charging software."
    ))
    agent = MVPAgent()
    rep = agent.analyze(idea)
    print(f"Core Hypothesis: {rep.core_value_hypothesis}")
    print(f"Features: {len(rep.features)}")
    print(f"Tech Stack Layers: {len(rep.tech_stack)}")
    print(f"Sprints: {len(rep.roadmap_sprints)}")
