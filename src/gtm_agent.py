"""
Go-To-Market (GTM) Strategy Generation Module (Module 7)
Project: AI Startup Idea Validator

Responsibilities:
1. Ingests structured startup idea, customer personas, competitor pricing, and MVP scope.
2. Formulates multi-channel customer acquisition playbooks (Inbound, Outbound, OEM/Partnerships).
3. Defines a tiered monetization model (Starter, Professional, Enterprise) with price points.
4. Maps a 3-phase commercial launch roadmap (Private Alpha, Public Beta, Commercial Scale).
5. Projects sales cycle velocity and CAC:LTV unit economic targets.
6. Crafts high-converting positioning copy and elevator pitch.
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

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

load_dotenv(root_dir / ".env")

from src.models import (
    StructuredIdeaOutput,
    MarketOpportunityReport,
    CompetitorAnalysisReport,
    MVPRecommendationReport,
    AcquisitionChannel,
    PricingTier,
    LaunchPhase,
    GTMStrategyReport
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GTMAgent")

SYSTEM_GTM_PROMPT = """You are a Chief Commercial Officer, Venture Growth Strategist, and Go-To-Market Expert.
Your task is to craft an aggressive, capital-efficient, and realistic Go-To-Market (GTM) strategy for an early-stage startup.

You will receive the Startup Concept Profile, Target Customer Personas, and Competitor Benchmarks.
Produce a structured JSON report matching this EXACT schema:
{
  "idea_name": "Startup name",
  "positioning_headline": "A bold, punchy positioning headline tailored to the target audience",
  "elevator_pitch": "A 30-second crisp elevator pitch explaining Problem, Solution, and tangible ROI",
  "acquisition_channels": [
    {
      "channel_name": "Channel name (e.g., Viral Short-Form Video, Direct Founder-Led Outbound, Strategic Partner Ecosystem)",
      "channel_type": "Outbound | Inbound | Partnership | Product-Led",
      "strategy_details": "Tactical, step-by-step execution playbook",
      "expected_cac": "Estimated cost range per acquired customer matching the market",
      "scalability": "High | Medium | Low"
    }
  ],
  "pricing_model_structure": "Overview of monetization model matching customer purchasing habits",
  "pricing_tiers": [
    {
      "tier_name": "Appropriate tier name (e.g. Free Tier, Pro Member, Annual Household Plan for B2C; or Starter, Growth, Enterprise for B2B)",
      "price_point": "Realistic price and billing cadence (e.g. Free ($0), $4.99/mo, $39.99/yr for consumers; or $35/vehicle/mo for fleet; or $49/mo for SMB SaaS)",
      "target_customer_size": "Account size or customer profile",
      "included_features": [
        "Feature 1 tailored to the startup idea",
        "Feature 2 tailored to the startup idea"
      ]
    }
  ],
  "launch_phases": [
    {
      "phase_name": "Phase 1: Private Alpha | Phase 2: Public Beta Launch | Phase 3: Commercial Scale",
      "duration": "Duration (e.g. Months 1-3)",
      "objectives": [
        "Key objective 1",
        "Key objective 2"
      ],
      "target_metric": "Measurable gate to graduate to next phase"
    }
  ],
  "sales_cycle_estimate": "Estimated duration (e.g., Instant consumer impulse download <5 mins; or 14-30 days for SMB; or 60-90 days for Enterprise)",
  "cac_to_ltv_target": "Target unit economic metric (e.g., LTV:CAC > 4:1 with <3 month payback for B2C; or LTV:CAC > 5:1 for B2B)"
}

CRITICAL REALISTIC PRICING GUIDELINES:
1. Always align pricing with the real purchasing authority of the target customer:
   - For B2C Consumer / Mobile / Food / Lifestyle: Use freemium app pricing (e.g., Free Forever, $3.99 - $7.99/month Pro, $29.99 - $49.99/year Family). NEVER charge everyday consumers $99 or $249/month!
   - For Marketplaces: Use realistic take-rates (e.g., 5%-12% per transaction fee) + optional pro vendor subscription ($19 - $39/mo).
   - For Creator / Prosumer Tools: Free starter tier, $12 - $19/mo Pro, $49 - $79/mo Studio/Agency.
   - For SMB SaaS: $29 - $49/mo Starter, $79 - $149/mo Growth, $249 - $349/mo Scale.
   - For Enterprise / Industrial / Fleet B2B: $350 - $500/mo Pilot or $35 - $55 / unit / month with custom annual volume tiers.
2. Provide at least 3 distinct acquisition channels matching the customer journey.
3. Provide 3 realistic, specific pricing tiers with features tailored directly to the startup.
4. Provide 3 clear sequential launch phases.
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
    market: Optional[Union[MarketOpportunityReport, Dict[str, Any]]] = None,
    comp: Optional[Union[CompetitorAnalysisReport, Dict[str, Any]]] = None,
    mvp: Optional[Union[MVPRecommendationReport, Dict[str, Any]]] = None,
    reason: str = "Fallback"
) -> GTMStrategyReport:
    """High-fidelity deterministic GTM playbook for offline use."""
    logger.warning(f"Generating deterministic GTM strategy. Reason: {reason}")
    text = (idea.industry + " " + idea.idea_name + " " + idea.problem_statement).lower()

    if any(k in text for k in ["pantry", "grocery", "groceries", "food", "fridge", "recipe", "spoil", "waste", "kitchen"]):
        headline = "Stop Throwing Away Groceries. Cook Delicious Meals and Save $1,500 a Year with a Single Photo."
        pitch = (
            f"{idea.idea_name} is the smart mobile kitchen assistant that saves everyday households $1,500 a year. "
            "Simply snap a photo of your supermarket grocery receipt; our AI automatically tracks expiration dates, alerts you "
            "before food spoils, and suggests delicious 15-minute recipes using what is already in your fridge. "
            "No tedious typing, no food waste, and more money in your pocket every month."
        )
        channels = [
            AcquisitionChannel(
                channel_name="Viral Short-Form Cooking Video Content (TikTok, Instagram Reels, YouTube Shorts)",
                channel_type="Inbound",
                strategy_details="Publish 3x weekly organic videos showing 'Making a $30 restaurant dinner out of leftovers expiring in my fridge today'. Include clear call-to-action to download SmartPantry AI.",
                expected_cac="$0.40 – $1.20 per acquired app install (Organic & Creator partnerships)",
                scalability="High"
            ),
            AcquisitionChannel(
                channel_name="College Campus Student Ambassadors & Apartment Community Partnerships",
                channel_type="Outbound",
                strategy_details="Partner with university sustainability student clubs and residential student housing groups to run 'Zero Food Waste Dorm Challenges' with free 3-month Pro trials.",
                expected_cac="$1.50 – $3.00 per activated user",
                scalability="Medium"
            ),
            AcquisitionChannel(
                channel_name="Grocery Delivery & Supermarket Loyalty App Cross-Promotions",
                channel_type="Partnership",
                strategy_details="Co-marketing integrations with digital grocery delivery services and digital coupon blogs to offer SmartPantry Pro as a bundled pantry efficiency tool.",
                expected_cac="$2.00 – $4.00 per paid subscriber",
                scalability="High"
            )
        ]
        pricing_tiers = [
            PricingTier(
                tier_name="Free (Basic Pantry)",
                price_point="Free Forever ($0)",
                target_customer_size="Casual cooks and early adopters",
                included_features=[
                    "Manual pantry inventory tracking (up to 30 items)",
                    "Basic expiration date alerts (24 hours before)",
                    "3 AI recipe recommendations per week",
                    "Standard grocery shopping checklist"
                ]
            ),
            PricingTier(
                tier_name="SmartPantry Pro (Monthly)",
                price_point="$4.99 / month (Cancel anytime)",
                target_customer_size="Busy professionals and young couples cooking at home",
                included_features=[
                    "Unlimited 1-second grocery receipt photo scanning",
                    "Smart 48-hour and 24-hour perishable expiration push alerts",
                    "Unlimited 'What's in my fridge' recipe generation",
                    "Household '$ Saved This Month' financial analytics dashboard",
                    "Dietary preferences & allergy customizer (Gluten-free, Vegan, Keto)"
                ]
            ),
            PricingTier(
                tier_name="Annual Household Plan",
                price_point="$39.99 / year ($3.33/month — Save 33%)",
                target_customer_size="Families and budget-conscious multi-person households",
                included_features=[
                    "All Pro Monthly features",
                    "Multi-device household family sharing (up to 5 family members)",
                    "Weekly automated meal planning & leftover reduction schedule",
                    "Priority customer support & early access to new AI features"
                ]
            )
        ]
        phases = [
            LaunchPhase(
                phase_name="Phase 1: Private Alpha (50 Beta Households)",
                duration="Months 1 to 2",
                objectives=[
                    "Recruit 50 test households across young professionals and college students",
                    "Refine receipt OCR accuracy to >92% across top 5 supermarket chains",
                    "Measure verified monthly grocery dollar savings per household"
                ],
                target_metric="Achieve >65% Day-14 retention and verify average $45/month savings per beta user"
            ),
            LaunchPhase(
                phase_name="Phase 2: App Store & Social Viral Launch",
                duration="Months 3 to 5",
                objectives=[
                    "Launch iOS App Store and Google Play apps with $4.99/mo freemium paywall",
                    "Execute influencer seeding campaign with 15 food waste and frugal living TikTok creators",
                    "Implement in-app 'Invite a Friend, Get 1 Month Pro Free' referral loop"
                ],
                target_metric="Reach 25,000 active app downloads and $8,000 Monthly Recurring Revenue"
            ),
            LaunchPhase(
                phase_name="Phase 3: National Scale & Grocery API Integrations",
                duration="Months 6 to 12",
                objectives=[
                    "Launch direct digital e-receipt sync with Instacart, Walmart, and Target accounts",
                    "Introduce CPG brand-sponsored recipe ingredient partnerships",
                    "Scale paid acquisition with target 4-month payback period"
                ],
                target_metric="150,000+ active users and $50,000+ Monthly Recurring Revenue run-rate"
            )
        ]
        sales_cycle = "Instant consumer decision (<5 minutes from app download to free trial activation)"
        cac_ltv = "Target LTV:CAC > 4:1 with an average payback period under 3 months based on $50 annual customer value."

    elif any(k in text for k in ["ev", "electric", "battery", "fleet", "logistics", "charging"]):
        headline = "Slash Commercial EV Depot Electricity Costs by 30% While Eliminating Delivery Route Range Anxiety."
        pitch = (
            f"{idea.idea_name} is the intelligent operations platform for commercial fleets transitioning to electric vans. "
            "Unlike legacy telematics that treat EVs like diesel trucks, our software couples real-time battery electrochemistry "
            "with dynamic delivery routing and automated depot charging. We eliminate mid-shift vehicle discharge while scheduling "
            "charging during off-peak hours, cutting thousands of dollars in utility peak demand charges from day one."
        )
        channels = [
            AcquisitionChannel(
                channel_name="Account-Based Outbound to Regional Logistics Operators",
                channel_type="Outbound",
                strategy_details="Target Operations Directors at regional parcel carriers operating 15–200 vans in zero-emission zones via personalized video audits of their depot utility tariffs.",
                expected_cac="$1,500 – $3,000 per closed fleet account",
                scalability="High"
            ),
            AcquisitionChannel(
                channel_name="Co-Selling Partnerships with Commercial EV Dealers & Charger OEMs",
                channel_type="Partnership",
                strategy_details="Partner with EV commercial truck dealerships (Ford Pro, BrightDrop) and charger manufacturers (ChargePoint, ABB) to bundle software at point of vehicle sale.",
                expected_cac="$600 – $1,200 per fleet account (Shared margin)",
                scalability="High"
            ),
            AcquisitionChannel(
                channel_name="Inbound Fleet Decarbonization ROI Calculator & Whitepapers",
                channel_type="Inbound",
                strategy_details="Publish monthly benchmark studies on utility demand charges and real-world commercial van cold-weather range loss to capture organic search traffic.",
                expected_cac="$800 – $1,500 per inbound lead",
                scalability="Medium"
            )
        ]
        pricing_tiers = [
            PricingTier(
                tier_name="Pilot Depot (10-25 Vans)",
                price_point="$55 / vehicle / month",
                target_customer_size="Initial depot testing & regional couriers",
                included_features=["Dynamic route range feasibility checker", "Standard OBD-II telematics sync", "Basic off-peak charging scheduler", "Weekly PDF executive savings report"]
            ),
            PricingTier(
                tier_name="Commercial Growth (25-100 Vans)",
                price_point="$45 / vehicle / month (Billed Annually)",
                target_customer_size="Mid-sized delivery logistics companies",
                included_features=["All Pilot features", "Real-time utility TOU tariff automated command dispatch", "Battery degradation & thermal health alerts", "Dedicated Customer Success Manager"]
            ),
            PricingTier(
                tier_name="Enterprise Fleet (100+ Vans)",
                price_point="Custom Quote ($35-$40/vehicle/mo + API fees)",
                target_customer_size="Large multi-depot carriers and enterprise shippers",
                included_features=["All Growth features", "Custom TMS / ERP API bi-directional connectors", "Virtual Power Plant (VPP) grid revenue sharing", "99.9% Uptime SLA & 24/7 dedicated support"]
            )
        ]
        phases = [
            LaunchPhase(
                phase_name="Phase 1: Private Alpha (Design Partners)",
                duration="Months 1 to 3",
                objectives=["Recruit 3 regional delivery fleets (30-60 vans total) for zero-risk shadow mode", "Harden telematics data ingestion and tariff calculation accuracy", "Document verified utility cost savings case studies"],
                target_metric="3 signed case studies demonstrating >20% utility peak cost reduction"
            ),
            LaunchPhase(
                phase_name="Phase 2: Commercial Beta & Partner Channels",
                duration="Months 4 to 6",
                objectives=["Convert alpha partners to paid annual contracts", "Launch co-selling pilot with 2 commercial EV charger distributors", "Initiate targeted outbound ABM campaign across 150 regional fleets"],
                target_metric="Reach 500 active vehicles on platform ($25,000 Monthly Recurring Revenue)"
            ),
            LaunchPhase(
                phase_name="Phase 3: National Scale & VPP Expansion",
                duration="Months 7 to 12",
                objectives=["Scale outbound sales team to 3 Account Executives", "Activate Virtual Power Plant utility demand-response revenue sharing", "Expand OEM API direct integrations"],
                target_metric="2,500+ vehicles under management ($1.2M Annual Recurring Revenue run-rate)"
            )
        ]
        sales_cycle = "30 to 60 days for mid-market fleets (15-100 vans); 90 days for 100+ enterprise vans"
        cac_ltv = "Target LTV:CAC > 5:1 with an average payback period under 7 months based on $540 annual contract value per van."

    else:
        # Dynamic, Realistic Archetype Detection (Consumer vs Marketplace vs Creator vs SMB vs Enterprise)
        is_consumer = any(k in text for k in ["consumer", "b2c", "mobile", "app", "student", "personal", "fitness", "pet", "shopping", "social", "family", "lifestyle", "habit", "home"])
        is_marketplace = any(k in text for k in ["marketplace", "platform", "freelance", "matching", "rent", "rental", "booking", "gig", "two-sided"])
        is_creator = any(k in text for k in ["creator", "writer", "design", "video", "podcast", "influencer", "youtube", "music", "portfolio"])
        is_smb = any(k in text for k in ["smb", "shop", "restaurant", "salon", "clinic", "small business", "boutique", "retail"])

        if is_consumer:
            headline = f"The Effortless Mobile Companion That Solves {idea.problem_statement[:60]}... From Day One."
            pitch = f"{idea.idea_name} gives {idea.target_customers} an intuitive smartphone experience that eliminates daily friction, saving hours of manual effort and providing immediate personal value."
            channels = [
                AcquisitionChannel(channel_name="Organic Short-Form Social Videos (TikTok, Reels, Shorts)", channel_type="Inbound", strategy_details="Post weekly relatable problem/solution video demos with a frictionless direct app store install link.", expected_cac="$0.40 – $1.50 per install", scalability="High"),
                AcquisitionChannel(channel_name="Student & Community Campus Ambassador Program", channel_type="Outbound", strategy_details="Onboard active community ambassadors to organize local challenges with 30-day free Pro upgrades.", expected_cac="$1.20 – $2.50 per user", scalability="Medium"),
                AcquisitionChannel(channel_name="In-App Peer Referral Loops ('Give 1 Month, Get 1 Month')", channel_type="Product-Led", strategy_details="Reward users with free Pro access when friends sign up and activate their accounts.", expected_cac="$0.60 – $1.00 per activated user", scalability="High")
            ]
            pricing_tiers = [
                PricingTier(tier_name="Free Forever", price_point="Free ($0)", target_customer_size="Casual users exploring the product", included_features=["Core essential functionality", "Standard mobile notifications", "Community access"]),
                PricingTier(tier_name="Pro Member", price_point="$4.99 / month (Cancel anytime)", target_customer_size="Active everyday users seeking full features", included_features=["Unlimited automated scans & tracking", "Smart proactive alerts", "Detailed monthly analytics & insights", "Priority feature updates"]),
                PricingTier(tier_name="Annual Household Plan", price_point="$39.99 / year ($3.33/mo — Save 33%)", target_customer_size="Power users and multi-person households", included_features=["All Pro features", "Multi-device family sync", "Advanced custom preferences", "Premium 24/7 support"])
            ]
            phases = [
                LaunchPhase(phase_name="Phase 1: Private Alpha (50 Beta Users)", duration="Months 1-2", objectives=["Test onboarding speed and Day-7 retention with beta cohort", "Optimize user workflow completion under 60 seconds"], target_metric="Achieve >60% Day-14 user retention"),
                LaunchPhase(phase_name="Phase 2: App Store & Social Viral Push", duration="Months 3-5", objectives=["Launch iOS and Android apps with $4.99/mo freemium paywall", "Partner with 10 niche content creators"], target_metric="Reach 15,000 active downloads and $5,000 MRR"),
                LaunchPhase(phase_name="Phase 3: National Scale & Partnerships", duration="Months 6-12", objectives=["Launch digital cross-promotions with complementary lifestyle brands", "Scale organic referral loop"], target_metric="100,000+ active users and $35,000+ MRR")
            ]
            sales_cycle = "Instant impulse decision (<5 minutes from download to trial activation)"
            cac_ltv = "LTV:CAC > 4:1 with payback period under 3 months based on $45 annual customer value"

        elif is_marketplace:
            headline = f"The Trusted Two-Sided Platform Connecting {idea.target_customers} with Verified Quality."
            pitch = f"{idea.idea_name} removes discovery and transaction friction, providing seamless matching, transparent reviews, and secure transactions for both buyers and providers."
            channels = [
                AcquisitionChannel(channel_name="Direct Supply-Side Onboarding & Concierge Setup", channel_type="Outbound", strategy_details="Manually recruit and verify top 50 local service providers to guarantee high-quality supply at launch.", expected_cac="$20 – $40 per active provider", scalability="Medium"),
                AcquisitionChannel(channel_name="Hyper-Local SEO Directory & Community Groups", channel_type="Inbound", strategy_details="Target high-intent local search queries and establish presence in community neighborhood groups.", expected_cac="$4 – $10 per demand user", scalability="High"),
                AcquisitionChannel(channel_name="Two-Sided Referral Incentive Engine", channel_type="Product-Led", strategy_details="Give $15 booking credits to both referrer and referee upon successful booking completion.", expected_cac="$8 – $15 per verified transaction", scalability="High")
            ]
            pricing_tiers = [
                PricingTier(tier_name="Free Member", price_point="Free ($0)", target_customer_size="Everyday buyers searching and booking", included_features=["Unlimited browsing & matching", "In-app messaging", "Standard customer protection"]),
                PricingTier(tier_name="Verified Provider", price_point="$19 / month + 8% per transaction", target_customer_size="Active independent providers and sellers", included_features=["Verified credibility badge", "Instant direct booking dispatch", "Automated client reviews & invoicing", "Lower 8% commission rate"]),
                PricingTier(tier_name="Featured Agency / Partner", price_point="$49 / month + 5% volume commission", target_customer_size="High-volume agencies and top providers", included_features=["Top sponsored search placement", "Multi-staff calendar management", "Custom booking widgets", "Dedicated account support"])
            ]
            phases = [
                LaunchPhase(phase_name="Phase 1: Seed Supply in 1 Pilot City", duration="Months 1-3", objectives=["Manually onboard 30 vetted providers", "Complete 100 successful client transactions"], target_metric="90%+ positive review rating"),
                LaunchPhase(phase_name="Phase 2: Local Demand Flywheel", duration="Months 4-6", objectives=["Activate hyper-local marketing", "Introduce 8% transaction monetization"], target_metric="$15,000 monthly Gross Merchandise Value (GMV)"),
                LaunchPhase(phase_name="Phase 3: Multi-City Expansion", duration="Months 7-12", objectives=["Expand to 3 adjacent metropolitan areas", "Roll out Verified Provider subscriptions"], target_metric="$100,000+ monthly GMV")
            ]
            sales_cycle = "1 to 3 days from initial search to completed first transaction"
            cac_ltv = "LTV:CAC > 3.5:1 with payback period under 4 months"

        elif is_creator:
            headline = f"The High-Velocity Creative Workspace Built for Modern {idea.target_customers}."
            pitch = f"{idea.idea_name} simplifies complex workflows into a streamlined canvas, empowering creators to produce and monetize content 3x faster without tech headaches."
            channels = [
                AcquisitionChannel(channel_name="Product Hunt & Creative Community Showcases", channel_type="Inbound", strategy_details="Launch high-converting demo videos on Product Hunt, Reddit communities, and Twitter/X.", expected_cac="$2 – $6 per active user", scalability="High"),
                AcquisitionChannel(channel_name="YouTube Creator Tutorials & Workflow Breakdowns", channel_type="Partnership", strategy_details="Sponsor micro-creators to film 'How I build with {idea.idea_name}' workflow tutorials.", expected_cac="$10 – $25 per paying subscriber", scalability="High"),
                AcquisitionChannel(channel_name="Product-Led Freemium Watermark Virality", channel_type="Product-Led", strategy_details="Free exports carry a discreet 'Made with {idea.idea_name}' link driving organic creator signups.", expected_cac="$0.80 per viral signup", scalability="High")
            ]
            pricing_tiers = [
                PricingTier(tier_name="Starter Creator", price_point="Free Forever ($0)", target_customer_size="Hobbyists and beginners", included_features=["Up to 3 active projects", "Standard export quality", "Community templates"]),
                PricingTier(tier_name="Creator Pro", price_point="$12 / month (or $9/mo Annual)", target_customer_size="Solo professionals and active content creators", included_features=["Unlimited projects & high-res exports", "Remove all watermarks", "Custom branding & fonts", "Cloud asset library"]),
                PricingTier(tier_name="Studio / Team", price_point="$39 / month", target_customer_size="Creative boutiques and multi-seat agencies", included_features=["All Pro features", "Up to 5 team collaborator seats", "Shared brand kits", "Priority rendering"])
            ]
            phases = [
                LaunchPhase(phase_name="Phase 1: Public Beta & Creator Feedback", duration="Months 1-2", objectives=["Recruit 100 beta creators", "Refine export rendering speed under 2 seconds"], target_metric="Achieve >40% weekly active creator usage"),
                LaunchPhase(phase_name="Phase 2: Product Hunt & Pro Tier Launch", duration="Months 3-5", objectives=["Execute top-3 Product Hunt launch", "Launch $12/mo Creator Pro subscription"], target_metric="5,000 registered creators and $4,000 MRR"),
                LaunchPhase(phase_name="Phase 3: Studio Collaboration Scale", duration="Months 6-12", objectives=["Release multi-seat team workspace", "Integrate third-party cloud plugins"], target_metric="30,000+ creators and $25,000+ MRR")
            ]
            sales_cycle = "Same-day self-serve trial conversion (<24 hours)"
            cac_ltv = "LTV:CAC > 4:1 with payback period under 2 months"

        elif is_smb:
            headline = f"The All-In-One Modern Operating System for {idea.target_customers}."
            pitch = f"{idea.idea_name} replaces cluttered spreadsheets and fragmented tools with an intelligent, automated dashboard designed specifically for local and mid-market operators."
            channels = [
                AcquisitionChannel(channel_name="Targeted Local Business Outbound & Demos", channel_type="Outbound", strategy_details="Direct founder-led phone/video walkthroughs demonstrating immediate 5-hour weekly time savings.", expected_cac="$80 – $180 per closed account", scalability="Medium"),
                AcquisitionChannel(channel_name="Inbound Niche Industry Content & ROI Calculators", channel_type="Inbound", strategy_details="Publish step-by-step guides and cost-saving templates addressing acute operational pain points.", expected_cac="$40 – $90 per inbound trial", scalability="High"),
                AcquisitionChannel(channel_name="Local Industry Association & Reseller Partnerships", channel_type="Partnership", strategy_details="Co-market through regional trade associations with exclusive 20% member discounts.", expected_cac="$50 – $100 per member account", scalability="Medium")
            ]
            pricing_tiers = [
                PricingTier(tier_name="Starter Business", price_point="$29 / month", target_customer_size="Small single-location operators (1-3 staff)", included_features=["Core operational dashboard", "Automated client reminders", "Basic reporting & export", "Email support"]),
                PricingTier(tier_name="Growth Operator", price_point="$79 / month (Billed Annually)", target_customer_size="Growing businesses (4-15 staff)", included_features=["All Starter features", "Multi-user staff logins", "Advanced workflow automation", "Custom client portal", "Priority live chat support"]),
                PricingTier(tier_name="Multi-Location Scale", price_point="$199 / month", target_customer_size="Multi-location businesses and franchises", included_features=["All Growth features", "Centralized multi-location dashboard", "Custom software integrations", "Dedicated onboarding specialist", "Custom SLA"])
            ]
            phases = [
                LaunchPhase(phase_name="Phase 1: 10 Design Partner Local Audits", duration="Months 1-3", objectives=["Manually shadow 10 local operators", "Verify direct 5+ hour weekly administrative time savings"], target_metric="8 of 10 pilot partners convert to paid"),
                LaunchPhase(phase_name="Phase 2: Self-Serve SaaS Onboarding", duration="Months 4-6", objectives=["Launch 14-day free trial on web", "Scale targeted search marketing"], target_metric="Reach 75 paying business accounts ($6,000 MRR)"),
                LaunchPhase(phase_name="Phase 3: Regional Expansion & API Connectors", duration="Months 7-12", objectives=["Release third-party accounting & CRM integrations", "Hire 2 inside sales reps"], target_metric="350+ paying businesses ($30,000+ MRR)")
            ]
            sales_cycle = "7 to 14 days from free trial initiation to paid activation"
            cac_ltv = "LTV:CAC > 4:1 with payback period under 4 months"

        else:
            # General Enterprise / Mid-Market Technology
            headline = f"The Intelligent Platform Automating Complex Workflows for {idea.industry}."
            pitch = f"{idea.idea_name} transforms manual operational bottlenecks for {idea.target_customers} into streamlined, data-backed workflows that deliver measurable cost reductions."
            channels = [
                AcquisitionChannel(channel_name="Account-Based Outbound to Department Leaders", channel_type="Outbound", strategy_details="Personalized outreach targeting VP/Director level decision makers with custom efficiency audits.", expected_cac="$450 – $950 per qualified account", scalability="Medium"),
                AcquisitionChannel(channel_name="Inbound Industry Whitepapers & Benchmark Reports", channel_type="Inbound", strategy_details="Publish proprietary industry workflow benchmark data to capture high-intent enterprise buyers.", expected_cac="$200 – $400 per inbound MQL", scalability="High"),
                AcquisitionChannel(channel_name="Platform Ecosystem & Marketplace App Listings", channel_type="Partnership", strategy_details="List on complementary software marketplaces to capture buyers seeking certified connectors.", expected_cac="$150 – $300 per activated lead", scalability="High")
            ]
            pricing_tiers = [
                PricingTier(tier_name="Department Starter", price_point="$49 / month", target_customer_size="Single team or departmental pilot", included_features=["Core automated workflow execution", "Standard analytics dashboard", "Role-based user permissions", "Standard email support"]),
                PricingTier(tier_name="Professional Business", price_point="$149 / month (Billed Annually)", target_customer_size="Mid-sized growing companies (20-100 staff)", included_features=["All Starter features", "Advanced bi-directional API connectors", "Custom automated alert triggers", "Audit log compliance", "Priority support"]),
                PricingTier(tier_name="Enterprise Commercial", price_point="Custom Quote ($399+/month)", target_customer_size="Large corporate accounts with custom security requirements", included_features=["All Professional features", "Dedicated Customer Success Manager", "Custom SSO / SAML integration", "99.9% Uptime SLA", "Custom data retention"])
            ]
            phases = [
                LaunchPhase(phase_name="Phase 1: Private Alpha (5 Pilot Accounts)", duration="Months 1-3", objectives=["5 enterprise pilots validating core data workflow", "Harden API connection stability"], target_metric="3 signed reference case studies"),
                LaunchPhase(phase_name="Phase 2: Commercial Launch", duration="Months 4-6", objectives=["Launch public commercial pricing", "Activate outbound account-based marketing"], target_metric="Reach 25 paying accounts ($10,000 MRR)"),
                LaunchPhase(phase_name="Phase 3: Scale & Channel Partnerships", duration="Months 7-12", objectives=["Scale sales team", "Expand certified technology integrations"], target_metric="100+ enterprise accounts ($50,000+ MRR)")
            ]
            sales_cycle = "30 to 60 days for commercial accounts; 90 days for enterprise"
            cac_ltv = "LTV:CAC > 4.5:1 with payback period under 6 months"

    return GTMStrategyReport(
        idea_name=idea.idea_name,
        positioning_headline=headline,
        elevator_pitch=pitch,
        acquisition_channels=channels,
        pricing_model_structure=idea.monetization_model or "Tiered B2B SaaS with annual prepaid incentives",
        pricing_tiers=pricing_tiers,
        launch_phases=phases,
        sales_cycle_estimate=sales_cycle,
        cac_to_ltv_target=cac_ltv,
        agent_metadata={
            "agent_name": "Go-To-Market Strategy Module",
            "model_used": "FALLBACK_RULE_BASED",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "status": f"partial ({reason})"
        }
    )


class GTMAgent:
    """Module 7: Synthesizes commercial Go-To-Market playbook, channels, and pricing models."""

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    def analyze(
        self,
        idea: StructuredIdeaOutput,
        market: Optional[Union[MarketOpportunityReport, Dict[str, Any]]] = None,
        comp: Optional[Union[CompetitorAnalysisReport, Dict[str, Any]]] = None,
        mvp: Optional[Union[MVPRecommendationReport, Dict[str, Any]]] = None
    ) -> GTMStrategyReport:
        """Executes Go-To-Market strategy formulation."""
        user_prompt = (
            f"Startup Name: {idea.idea_name}\n"
            f"Tagline: {idea.tagline}\n"
            f"Industry: {idea.industry}\n"
            f"Target Customers: {idea.target_customers}\n"
            f"Problem: {idea.problem_statement}\n"
            f"Proposed Solution: {idea.proposed_solution}\n"
            f"Monetization Idea: {idea.monetization_model}\n"
        )
        if comp:
            c_dict = comp.model_dump() if hasattr(comp, "model_dump") else comp
            user_prompt += f"Unique Value Proposition: {c_dict.get('unique_value_proposition')}\n"

        # 1. Try Gemini
        if self.gemini_key and not self.gemini_key.startswith("your_"):
            logger.info("Calling Gemini LLM for GTM Strategy...")
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    generation_config={"response_mime_type": "application/json", "temperature": 0.25},
                    system_instruction=SYSTEM_GTM_PROMPT
                )
                resp = model.generate_content(user_prompt)
                parsed = _clean_and_parse_json(resp.text)
                parsed["agent_metadata"] = {
                    "agent_name": "Go-To-Market Strategy Module",
                    "model_used": "gemini-1.5-flash",
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "status": "success"
                }
                return GTMStrategyReport.model_validate(parsed)
            except Exception as e:
                logger.warning(f"Gemini GTM formulation failed: {e}. Trying fallback...")

        # 2. Try OpenAI
        if self.openai_key and not self.openai_key.startswith("your_"):
            logger.info("Calling OpenAI LLM for GTM Strategy...")
            try:
                import requests
                headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": SYSTEM_GTM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.25
                }
                r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=45)
                r.raise_for_status()
                parsed = _clean_and_parse_json(r.json()["choices"][0]["message"]["content"])
                parsed["agent_metadata"] = {
                    "agent_name": "Go-To-Market Strategy Module",
                    "model_used": "gpt-4o-mini",
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "status": "success"
                }
                return GTMStrategyReport.model_validate(parsed)
            except Exception as e:
                logger.warning(f"OpenAI GTM formulation failed: {e}. Trying fallback...")

        return _generate_domain_fallback(idea, market, comp, mvp, "No active LLM API key configured")


if __name__ == "__main__":
    from src.idea_extractor import extract_idea_structure
    from src.models import RawStartupSubmission
    idea = extract_idea_structure(RawStartupSubmission(
        startup_name="FleetPulse EV",
        description="Smart EV route optimization and charging software."
    ))
    agent = GTMAgent()
    rep = agent.analyze(idea)
    print(f"Headline: {rep.positioning_headline}")
    print(f"Channels: {len(rep.acquisition_channels)}")
    print(f"Pricing Tiers: {len(rep.pricing_tiers)}")
    print(f"Launch Phases: {len(rep.launch_phases)}")
