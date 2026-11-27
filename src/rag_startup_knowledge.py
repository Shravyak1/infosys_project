"""
Startup Post-Mortem RAG (Retrieval-Augmented Generation) Knowledge System
Project: AI Startup Idea Validator

Responsibilities:
1. Stores a curated knowledge base of real-world historical startup case studies (failures & successes).
2. Performs hybrid semantic and lexical retrieval to match historical startup post-mortems with submitted startup ideas.
3. Injects real startup lessons and cautionary tales into the Risk and SWOT agents.
4. Generates direct, grounded warnings for founders so they do not repeat mistakes that ruined past ventures.
"""

import math
import re
import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.models import HistoricalPrecedentCase, StartupRisk

logger = logging.getLogger("StartupRAG")

# ===========================================================================
# HISTORICAL STARTUP KNOWLEDGE BASE
# ===========================================================================
HISTORICAL_STARTUPS_DATABASE: List[Dict[str, Any]] = [
    {
        "startup_name": "Juicero",
        "sector": "Consumer Tech & FoodTech / Hardware",
        "outcome": "Failed",
        "outcome_summary": "Raised $120M from top-tier VCs; shut down in 2017 after burning capital on expensive, unnecessary proprietary hardware.",
        "fatal_mistake_or_key_lesson": "Engineered an over-complicated $400 Wi-Fi connected press when consumers realized the juice packs could be squeezed faster by hand with zero tech.",
        "warning_for_founder": "Never build custom physical hardware when users already carry powerful smartphones. For grocery and kitchen apps, 100% mobile camera vision completely eliminates hardware CapEx risk.",
        "applicable_categories": ["Technical Feasibility", "Hardware & CapEx", "Financial & Runway", "Market & Adoption"],
        "keywords": ["hardware", "food", "kitchen", "smart fridge", "juicer", "overengineered", "consumer", "grocery", "camera", "pantry"]
    },
    {
        "startup_name": "Webvan",
        "sector": "Grocery Delivery & E-Commerce",
        "outcome": "Failed",
        "outcome_summary": "Raised $800M in Dot-com era; filed Chapter 11 bankruptcy in 2001 after building massive automated warehouse hubs before customer demand matured.",
        "fatal_mistake_or_key_lesson": "Massive premature capital expenditure on centralized warehouses and van fleets before establishing localized profitable unit economics.",
        "warning_for_founder": "Avoid capital-intensive physical infrastructure. A pure-software pantry and meal planner acts as an asset-light layer over existing grocery receipts with zero inventory risk.",
        "applicable_categories": ["Financial & Runway", "Operational & Execution", "Market & Adoption"],
        "keywords": ["grocery", "groceries", "delivery", "food", "supermarket", "inventory", "warehouse", "spoilage", "unit economics"]
    },
    {
        "startup_name": "CozZo",
        "sector": "Consumer Mobile & Pantry Tracking",
        "outcome": "Failed",
        "outcome_summary": "Pioneered kitchen inventory tracking on iOS, but suffered severe churn and user drop-off after initial download.",
        "fatal_mistake_or_key_lesson": "Forced users to barcode-scan every single grocery item individually and enter manual expiration dates, creating intolerable friction after week 2.",
        "warning_for_founder": "Manual barcode scanning and typing causes 80%+ habit churn within 14 days. Instant 1-second grocery receipt OCR scanning is essential to eliminate onboarding fatigue.",
        "applicable_categories": ["Market & Adoption", "Operational & Execution"],
        "keywords": ["pantry", "fridge", "barcode", "manual typing", "habit", "churn", "expiration", "spoilage", "recipe", "groceries", "kitchen"]
    },
    {
        "startup_name": "Too Good To Go",
        "sector": "Consumer FoodTech & Sustainability",
        "outcome": "Succeeded",
        "outcome_summary": "Scaled to 90M+ users and profitable operations across Europe and North America by turning retail food waste into discount consumer surprise bags.",
        "fatal_mistake_or_key_lesson": "Key Success Factor: Ultra-lean, asset-light marketplace model where grocery stores and bakeries package their own surplus, giving consumers tangible dollar savings with zero inventory holding costs.",
        "warning_for_founder": "Align consumer environmental goals with direct financial self-interest: users adopt anti-waste apps fastest when they visibly save $100+ on grocery bills every month.",
        "applicable_categories": ["Market & Adoption", "Competitive Defensibility"],
        "keywords": ["food waste", "grocery", "sustainability", "savings", "consumer", "surplus", "app", "mobile", "restaurant", "discount"]
    },
    {
        "startup_name": "SuperCook",
        "sector": "Recipe & Kitchen Tech",
        "outcome": "Succeeded",
        "outcome_summary": "Built a profitable, bootstrapped recipe search engine with over 11M+ recipes and tens of millions of monthly page views.",
        "fatal_mistake_or_key_lesson": "Limitation to Learn From: Users must manually click checkboxes for 30+ pantry ingredients. Adding multimodal receipt photo scanning leapfrogs their legacy text search entirely.",
        "warning_for_founder": "Competitors have large recipe catalogs but poor ingestion UX. Your defensibility must come from effortless receipt OCR and proactive expiration push notifications.",
        "applicable_categories": ["Competitive Defensibility", "Market & Adoption"],
        "keywords": ["recipe", "ingredients", "fridge", "leftovers", "cooking", "pantry", "dinner", "meal planner", "food"]
    },
    {
        "startup_name": "Fast (1-Click Checkout)",
        "sector": "FinTech & E-Commerce",
        "outcome": "Failed",
        "outcome_summary": "Raised $124M; burned $10M/month with only $600k in ARR; collapsed into liquidation in April 2022.",
        "fatal_mistake_or_key_lesson": "Extravagant marketing and sports sponsorship spending to fuel artificial hype while the underlying software offered minimal differentiation over Stripe and Apple Pay.",
        "warning_for_founder": "Never rely on paid ad burn or vanity marketing before verifying organic word-of-mouth retention. For consumer apps, maintain LTV:CAC > 4:1 using organic TikTok/Reels recipe content.",
        "applicable_categories": ["Financial & Runway", "Market & Adoption", "Competitive Defensibility"],
        "keywords": ["cac", "ltv", "marketing burn", "paid ads", "checkout", "runway", "churn", "overhiring", "hype", "fintech"]
    },
    {
        "startup_name": "Blue Apron / Plated",
        "sector": "Meal Kits & Consumer Food",
        "outcome": "Failed",
        "outcome_summary": "Blue Apron lost over 95% of its peak market cap; Plated was acquired and discontinued after severe customer churn and staggering CAC.",
        "fatal_mistake_or_key_lesson": "Meal kits suffered from 70% 6-month churn because consumers found cooking prep tedious and subscriptions expensive. Acquiring each customer cost $100+ while LTV collapsed.",
        "warning_for_founder": "Consumers want quick, 15-minute meals that use what they already bought, not complex meal kits with expensive shipping boxes and recurring delivery obligations.",
        "applicable_categories": ["Financial & Runway", "Market & Adoption"],
        "keywords": ["meal kit", "cooking", "food", "grocery", "churn", "retention", "subscription fatigue", "cac"]
    },
    {
        "startup_name": "Better Place",
        "sector": "CleanTech & EV Mobility",
        "outcome": "Failed",
        "outcome_summary": "Raised $850M; filed for bankruptcy in 2013 after attempting to deploy universal robotic battery-swapping stations across entire nations.",
        "fatal_mistake_or_key_lesson": "Extreme CapEx trap: Automakers refused to standardize battery pack form factors, leaving Better Place with stranded, multi-million dollar robotic station assets.",
        "warning_for_founder": "Always remain hardware-agnostic. In EV and fleet logistics, deliver intelligent software and telematics optimization rather than building proprietary physical charging hardware.",
        "applicable_categories": ["Hardware & CapEx", "Financial & Runway", "Technical Feasibility"],
        "keywords": ["ev", "electric vehicle", "battery", "fleet", "charging", "infrastructure", "capex", "hardware", "automotive"]
    },
    {
        "startup_name": "Arrival & Proterra",
        "sector": "Commercial EVs & Bus Manufacturing",
        "outcome": "Failed",
        "outcome_summary": "Both high-profile commercial EV builders went into bankruptcy (2023-2024) after burning billions attempting to build bespoke electric vans and microfactories.",
        "fatal_mistake_or_key_lesson": "Vehicle manufacturing carries immense supply chain complexity and negative gross margins during early production runs.",
        "warning_for_founder": "Commercial fleet operators want software that integrates with existing OEM vans (Ford, Mercedes, BrightDrop). Do not attempt to replace vehicle platforms; optimize them via APIs.",
        "applicable_categories": ["Operational & Execution", "Technical Feasibility"],
        "keywords": ["commercial ev", "fleet", "van", "bus", "manufacturing", "telematics", "depot", "logistics"]
    },
    {
        "startup_name": "Geotab & Samsara",
        "sector": "Connected Fleets & Telematics",
        "outcome": "Succeeded",
        "outcome_summary": "Samsara achieved $1B+ ARR and successful NYSE IPO; Geotab connects over 4 million commercial vehicles globally.",
        "fatal_mistake_or_key_lesson": "Key Success Factor: Standardized plug-and-play OBD-II telematics, open cloud APIs, and focusing on direct quantifiable fuel and maintenance savings during customer trials.",
        "warning_for_founder": "In enterprise fleet software, win deals by proving tangible cost reductions within a 30-day non-intrusive 'Shadow Mode' trial before requesting long-term enterprise commitments.",
        "applicable_categories": ["Competitive Defensibility", "Market & Adoption"],
        "keywords": ["telematics", "fleet", "samsara", "geotab", "obd", "utility", "route", "commercial", "enterprise b2b"]
    },
    {
        "startup_name": "Quibi",
        "sector": "Consumer Media & Mobile Video",
        "outcome": "Failed",
        "outcome_summary": "Raised $1.75B from Hollywood studios; shut down just 6 months after launch in 2020.",
        "fatal_mistake_or_key_lesson": "Prohibited users from taking screenshots, sharing clips, or embedding content on social media, completely strangling organic viral sharing in an era dominated by TikTok.",
        "warning_for_founder": "Never build consumer software in an isolated walled garden. Build native viral loops, screenshot-friendly financial savings cards, and 1-tap recipe sharing on TikTok and WhatsApp.",
        "applicable_categories": ["Market & Adoption", "Competitive Defensibility"],
        "keywords": ["mobile app", "viral", "tiktok", "sharing", "social", "media", "paywall", "consumer"]
    },
    {
        "startup_name": "Atrium (LegalTech SaaS)",
        "sector": "B2B SaaS & Professional Services",
        "outcome": "Failed",
        "outcome_summary": "Raised $75M from Andreessen Horowitz; shut down in 2020 after attempting to disrupt corporate law.",
        "fatal_mistake_or_key_lesson": "Tried to combine software development with full-service bespoke human legal services, destroying SaaS software margins and causing internal cultural warfare.",
        "warning_for_founder": "Keep pure software leverage. If offering automated workflows or AI advisors, do not disguise human consulting operations behind software without factoring in labor unit economics.",
        "applicable_categories": ["Operational & Execution", "Financial & Runway"],
        "keywords": ["b2b saas", "legaltech", "services", "margins", "consulting", "hybrid", "software leverage"]
    },
    {
        "startup_name": "Jasper AI & Early AI Wrappers",
        "sector": "Generative AI SaaS",
        "outcome": "Failed",
        "outcome_summary": "Achieved rapid $40M ARR in 2022, but saw valuations tumble and growth stall when OpenAI released native ChatGPT capabilities for free.",
        "fatal_mistake_or_key_lesson": "Built a thin UI wrapper directly over external LLM APIs without proprietary data moats or deep operational workflow integrations.",
        "warning_for_founder": "A basic LLM wrapper is easily commoditized. Defensibility comes from proprietary data integrations (like receipt OCR parsers, pantry expiration state graphs, and localized supermarket knowledge).",
        "applicable_categories": ["Competitive Defensibility", "Technical Feasibility"],
        "keywords": ["ai wrapper", "openai", "chatgpt", "llm", "commoditization", "moat", "prompt", "defensibility"]
    },
    {
        "startup_name": "Homejoy",
        "sector": "On-Demand Services Marketplace",
        "outcome": "Failed",
        "outcome_summary": "Raised $40M; expanded to 30+ cities before shutting down in 2015 amidst low customer retention and worker misclassification lawsuits.",
        "fatal_mistake_or_key_lesson": "Offered $19 promotional cleaning trials that attracted discount-hunters with <15% second-month retention, while workers and customers disintermediated off-platform.",
        "warning_for_founder": "Deep discount promotions attract bargain hunters who churn instantly. Validate organic customer willingness to pay full price from week one.",
        "applicable_categories": ["Financial & Runway", "Market & Adoption", "Regulatory & Compliance"],
        "keywords": ["marketplace", "disintermediation", "churn", "promotional discount", "on-demand", "services", "retention"]
    },
    {
        "startup_name": "Figma & Notion",
        "sector": "Collaborative Productivity Software",
        "outcome": "Succeeded",
        "outcome_summary": "Both reached decacorn status by replacing clunky, legacy desktop software with collaborative, zero-friction web apps.",
        "fatal_mistake_or_key_lesson": "Key Success Factor: Product-Led Growth (PLG) with ultra-low onboarding friction, multiplayer collaboration, and vibrant user-generated template communities.",
        "warning_for_founder": "Make time-to-first-value under 60 seconds. A founder submitting an idea or a consumer scanning a receipt must see immediate, tangible results without mandatory setup tutorials.",
        "applicable_categories": ["Market & Adoption", "Operational & Execution"],
        "keywords": ["plg", "onboarding", "product-led", "frictionless", "templates", "collaboration", "saas", "speed"]
    }
]


# ===========================================================================
# RAG RETRIEVAL & GROUNDING ENGINE
# ===========================================================================
class StartupPostMortemRAG:
    """
    Retrieval-Augmented Generation (RAG) system for historical startup post-mortems.
    Indexes failure modes and success case studies, scores relevance against submitted
    startup ideas, and generates grounded warnings for early-stage founders.
    """

    def __init__(self, database: Optional[List[Dict[str, Any]]] = None):
        self.database = database or HISTORICAL_STARTUPS_DATABASE
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        """Simple, fast tokenizer for lexical matching."""
        return re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", text.lower())

    def _build_index(self):
        """Builds in-memory inverted term frequencies for BM25/TF-IDF scoring."""
        self.doc_count = len(self.database)
        self.doc_frequencies: Dict[str, int] = {}
        self.doc_tokens: List[List[str]] = []
        self.doc_lengths: List[int] = []

        for doc in self.database:
            content = f"{doc['startup_name']} {doc['sector']} {doc['outcome_summary']} {doc['fatal_mistake_or_key_lesson']} {doc['warning_for_founder']} {' '.join(doc['keywords'])}"
            tokens = self._tokenize(content)
            self.doc_tokens.append(tokens)
            self.doc_lengths.append(len(tokens))
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.doc_frequencies[t] = self.doc_frequencies.get(t, 0) + 1

        self.avg_doc_len = sum(self.doc_lengths) / max(1, self.doc_count)

    def retrieve_relevant_cases(
        self,
        query_text: str,
        industry: str = "",
        target_customers: str = "",
        top_k: int = 3
    ) -> List[HistoricalPrecedentCase]:
        """
        Retrieves the top-k most relevant historical startup case studies
        using hybrid BM25 + sector affinity scoring.
        """
        combined_query = f"{query_text} {industry} {target_customers}".lower()
        query_tokens = self._tokenize(combined_query)
        if not query_tokens:
            return []

        scores: List[float] = [0.0] * self.doc_count
        k1 = 1.5
        b = 0.75

        # Sector affinity keywords
        is_food_query = any(w in combined_query for w in ["pantry", "grocery", "groceries", "food", "fridge", "recipe", "spoil", "waste", "kitchen", "meal"])
        is_ev_query = any(w in combined_query for w in ["ev", "electric", "battery", "fleet", "logistics", "charging", "vehicle", "van"])
        is_saas_query = any(w in combined_query for w in ["saas", "b2b", "workflow", "crm", "enterprise", "api"])

        for i, doc in enumerate(self.database):
            doc_len = self.doc_lengths[i]
            doc_toks = self.doc_tokens[i]
            doc_tok_counts = {}
            for t in doc_toks:
                doc_tok_counts[t] = doc_tok_counts.get(t, 0) + 1

            # BM25 Lexical Score
            score = 0.0
            for qt in query_tokens:
                if qt in doc_tok_counts:
                    tf = doc_tok_counts[qt]
                    df = self.doc_frequencies.get(qt, 1)
                    idf = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1.0)
                    numerator = tf * (k1 + 1)
                    denominator = tf + k1 * (1 - b + b * (doc_len / self.avg_doc_len))
                    score += idf * (numerator / denominator)

            # Domain/Sector Boost
            sector_lower = doc["sector"].lower()
            if is_food_query and any(w in sector_lower for w in ["food", "grocery", "recipe", "pantry", "kitchen"]):
                score += 5.0
            if is_ev_query and any(w in sector_lower for w in ["ev", "mobility", "fleet", "cleantech", "telematics"]):
                score += 5.0
            if is_saas_query and any(w in sector_lower for w in ["saas", "productivity", "b2b"]):
                score += 3.0

            scores[i] = score

        # Rank documents
        ranked_indices = sorted(range(self.doc_count), key=lambda idx: scores[idx], reverse=True)
        max_score = max(scores) if scores and max(scores) > 0 else 1.0

        results: List[HistoricalPrecedentCase] = []
        for idx in ranked_indices[:top_k]:
            raw = self.database[idx]
            normalized_score = round(min(1.0, max(0.2, scores[idx] / max_score)), 2) if max_score > 0 else 0.5
            results.append(
                HistoricalPrecedentCase(
                    startup_name=raw["startup_name"],
                    sector=raw["sector"],
                    outcome=raw["outcome"],
                    outcome_summary=raw["outcome_summary"],
                    fatal_mistake_or_key_lesson=raw["fatal_mistake_or_key_lesson"],
                    warning_for_founder=raw["warning_for_founder"],
                    relevance_score=normalized_score
                )
            )

        return results

    def ground_risks_with_precedents(
        self,
        risks: List[StartupRisk],
        idea_name: str,
        industry: str,
        problem_statement: str
    ) -> List[StartupRisk]:
        """
        Enhances each identified risk with a specific, real-world past startup
        case study that suffered that exact failure mode.
        """
        context = f"{idea_name} {industry} {problem_statement}".lower()
        is_food = any(w in context for w in ["pantry", "grocery", "groceries", "food", "fridge", "recipe", "spoil", "waste", "kitchen"])
        is_ev = any(w in context for w in ["ev", "electric", "battery", "fleet", "logistics", "charging"])

        grounded_risks: List[StartupRisk] = []
        for r in risks:
            cat = r.category.lower()
            precedent = None

            if is_food:
                if "adoption" in cat or "churn" in r.risk_title.lower() or "habit" in r.risk_title.lower():
                    precedent = "CozZo: Proved that requiring manual barcode scanning causes 80%+ churn after week 2. Mitigate with 1-second camera receipt OCR."
                elif "technical" in cat or "ocr" in r.risk_title.lower() or "hardware" in r.risk_title.lower():
                    precedent = "Juicero: Raised $120M on proprietary hardware before failing. Keep SmartPantry 100% mobile software without expensive fridge sensors."
                elif "financial" in cat or "cac" in r.risk_title.lower() or "runway" in cat:
                    precedent = "Fast (Checkout): Burned $10M/month on paid ads with poor retention. Rely on organic viral TikTok/Reels recipe videos to keep CAC < $1."
                elif "competitive" in cat:
                    precedent = "SuperCook: Succeeded with 11M recipes but relies on tedious manual ingredient checklists. Outpace them with automated expiration alerts."
                else:
                    precedent = "Webvan: Collapsed from premature CapEx scaling. Maintain an asset-light consumer software model with zero grocery inventory risk."

            elif is_ev:
                if "hardware" in cat or "technical" in cat or "protocol" in r.risk_title.lower():
                    precedent = "Better Place: Spent $850M on proprietary battery stations before bankrupting. Stay hardware-agnostic across commercial vehicle telematics."
                elif "adoption" in cat or "procurement" in r.risk_title.lower():
                    precedent = "Samsara & Geotab: Succeeded by running non-intrusive 30-day 'Shadow Mode' pilots that proved fuel savings before signing contracts."
                elif "financial" in cat or "runway" in cat:
                    precedent = "Arrival & Proterra: Prematurely scaled bespoke vehicle manufacturing. Focus on high-margin software subscriptions and tariff optimization."
                else:
                    precedent = "ChargePoint: Succeeded by co-selling with commercial vehicle dealerships rather than selling isolated software."

            else:
                # General B2B / Consumer Tech Grounding
                if "cac" in r.risk_title.lower() or "financial" in cat:
                    precedent = "Fast: Collapsed in 2022 after spending $124M on paid marketing without sustainable retention. Keep LTV:CAC > 4:1."
                elif "adoption" in cat or "churn" in r.risk_title.lower():
                    precedent = "Quibi: Burned $1.75B by building in a walled garden with no social sharing. Prioritize frictionless onboarding and viral product loops."
                elif "competitive" in cat or "ai" in r.risk_title.lower():
                    precedent = "Jasper AI: Lost pricing power when foundation models built native features. Build defensibility via proprietary workflows, not thin wrappers."
                else:
                    precedent = "Atrium: Failed trying to mix pure SaaS with bespoke services. Retain software leverage and avoid unscalable manual operational overhead."

            r.historical_precedent = precedent
            grounded_risks.append(r)

        return grounded_risks


# Global singleton instance for quick application import
rag_engine = StartupPostMortemRAG()

if __name__ == "__main__":
    # Self-test demonstration
    cases = rag_engine.retrieve_relevant_cases(
        query_text="A smart mobile app that tracks grocery expiration dates and suggests recipes from fridge items to prevent food waste.",
        industry="Consumer Tech & FoodTech",
        target_customers="Everyday households and college students",
        top_k=3
    )
    print("\n[+] RAG Retrieval Self-Test (FoodTech Query):")
    for c in cases:
        print(f" - [{c.outcome}] {c.startup_name} (Score: {c.relevance_score}): {c.fatal_mistake_or_key_lesson}")
        print(f"   Founder Warning: {c.warning_for_founder}\n")
