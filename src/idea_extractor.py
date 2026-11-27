"""
Idea Extractor Module: Converts raw startup submissions (2-3 lines or detailed)
into a validated StructuredIdeaOutput schema.
"""

import os
import sys
import json
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

load_dotenv(root_dir / ".env")

from src.models import RawStartupSubmission, StructuredIdeaOutput

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IdeaExtractor")

SYSTEM_EXTRACTION_PROMPT = """You are an expert Startup Architect and Venture Analyst.
Your task is to analyze a raw startup idea submission (often just 2-3 lines) and convert it into a standardized, structured JSON format.

You MUST extract and output the following fields in valid JSON:
{
  "idea_name": "Short, catchy, professional name for the startup",
  "tagline": "Crisp one-sentence elevator pitch",
  "problem_statement": "A clear, specific explanation of the core pain point or friction being solved",
  "proposed_solution": "The product, platform, or service proposed to solve this problem",
  "target_customers": "Specific target customer profile or user archetype (e.g., job titles, business size)",
  "industry": "Primary industry vertical (e.g., Logistics & CleanTech, HealthTech, FinTech, EdTech, B2B SaaS)",
  "key_features": [
    "Feature 1 - descriptive title and what it does",
    "Feature 2 - descriptive title and what it does",
    "Feature 3 - descriptive title and what it does",
    "Feature 4 - descriptive title and what it does"
  ],
  "monetization_model": "Proposed revenue model (e.g., B2B SaaS Subscription, Usage-Based, Marketplace Take-Rate)",
  "search_keywords": ["keyword 1", "keyword 2", "keyword 3", "keyword 4"],
  "search_queries": [
    "query to find market size and CAGR",
    "query to find top competitors and alternatives",
    "query to find customer pain points and willingness to pay"
  ]
}

STRICT INSTRUCTIONS:
1. Return ONLY the raw JSON object. Do NOT add markdown code fences or conversational text.
2. If any field is not explicitly stated in the input, intelligently infer it based on business domain context.
3. Provide at least 3-5 concrete key features for an MVP.
"""


def _call_gemini_api(prompt: str, user_content: str, api_key: str) -> str:
    """Connects to Google Gemini API."""
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.2,
        },
        system_instruction=prompt
    )
    response = model.generate_content(user_content)
    return response.text


def _call_openai_api(prompt: str, user_content: str, api_key: str) -> str:
    """Connects to OpenAI API."""
    import requests
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_content}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def clean_and_parse_json(raw_text: str) -> Dict[str, Any]:
    """Sanitizes LLM output to guarantee valid JSON parsing."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise ValueError(f"Could not parse valid JSON from response: {raw_text[:120]}...")


def _rule_based_fallback(raw: RawStartupSubmission, error_reason: str) -> StructuredIdeaOutput:
    """Domain-tailored deterministic extractor when LLM API keys are absent or failed."""
    logger.warning(f"Using rule-based fallback extractor. Reason: {error_reason}")
    text = (raw.description + " " + (raw.startup_name or "") + " " + (raw.industry or "")).lower()
    
    name = raw.startup_name or "Innovative Startup"
    desc = raw.description.strip()
    customers = raw.target_customers or ""
    industry = raw.industry or ""

    # Infer domain (SmartPantry AI / FoodTech as primary layman-friendly default)
    if any(k in text for k in ["pantry", "grocery", "groceries", "food", "fridge", "recipe", "spoil", "waste", "kitchen"]):
        name = raw.startup_name or "SmartPantry AI"
        tagline = "Smart mobile app that tracks grocery expiration dates and suggests recipes from ingredients in your fridge."
        industry = industry or "Consumer Tech & FoodTech"
        customers = customers or "Busy working professionals, college students, and budget-conscious households"
        key_features = [
            "Instant grocery receipt photo scanner with automated expiration date logging",
            "Smart push notifications alerting users 48 hours before perishable food spoils",
            "'What's in my fridge?' recipe generator matching meals to expiring ingredients",
            "Automated grocery shopping list that tracks pantry depletion and household savings"
        ]
        monetization = raw.monetization_hypothesis or "Freemium ($4.99/month for Pro unlimited receipt scanning and custom meal plans)"
        keywords = ["grocery tracking app", "food waste reduction", "recipe generator from fridge", "smart kitchen assistant"]
        queries = [
            "household grocery food waste reduction app market size 2025 2030",
            "top smart pantry grocery expiration competitors SuperCook CozZo MyFridgeFood",
            "consumer grocery food waste annual financial cost savings"
        ]
    elif any(k in text for k in ["ev", "electric", "battery", "fleet", "logistics", "charging", "van"]):
        name = raw.startup_name or "FleetPulse EV"
        tagline = "Intelligent battery health and dynamic route optimization for commercial electric fleets."
        industry = industry or "Logistics & CleanTech"
        customers = customers or "Fleet operations managers at mid-sized delivery companies (15-250 commercial vans)"
        key_features = [
            "Dynamic routing engine balancing battery state-of-health and terrain",
            "Automated off-peak depot charging scheduler with utility tariff arbitrage",
            "Battery degradation telemetry and predictive thermal health alerts",
            "Fleet manager operations dashboard with CO2 and TCO savings metrics"
        ]
        monetization = raw.monetization_hypothesis or "B2B SaaS ($45-$65/vehicle/month) yielding 25% energy savings"
        keywords = ["commercial EV fleet", "depot charging management", "battery health telematics", "route optimization"]
        queries = [
            "commercial EV fleet management market size CAGR 2025 2030",
            "top EV fleet charging and telematics competitors Samsara Geotab Ampcontrol",
            "commercial fleet electrification challenges utility demand charges"
        ]
    elif any(k in text for k in ["health", "med", "pharmacy", "hospital", "patient", "drug", "clinic"]):
        name = raw.startup_name or "MedTrack AI"
        tagline = "Automated computer vision and RFID inventory tracking for hospital pharmacy medication stocks."
        industry = industry or "Healthcare & Enterprise SaaS"
        customers = customers or "Hospital pharmacy directors and clinical supply chain executives in 200-800 bed hospitals"
        key_features = [
            "Continuous RFID and optical smart bin medication inventory tracking",
            "Predictive medication stockout and expiration date forecaster",
            "Automated supplier purchase order replenishment triggers",
            "Bi-directional EHR and hospital ERP integration (Epic, Cerner)"
        ]
        monetization = raw.monetization_hypothesis or "Enterprise SaaS ($3,500/hospital/month) + hardware sensor lease"
        keywords = ["hospital pharmacy inventory", "drug expiration tracking", "RFID medication management", "healthtech SaaS"]
        queries = [
            "hospital pharmacy automation market size forecast",
            "medication inventory management software competitors Omnicell Pyxis KitCheck",
            "hospital drug stockouts and medication waste financial losses"
        ]
    elif any(k in text for k in ["farm", "agri", "crop", "drone", "soil", "irrigation", "yield"]):
        name = raw.startup_name or "AgriSense Autonomous"
        tagline = "Autonomous drone scouting and multispectral soil telemetry for high-yield precision agriculture."
        industry = industry or "AgriTech & Robotics"
        customers = customers or "Commercial crop farmers and agronomy advisors managing 500+ acre farms"
        key_features = [
            "Automated waypoint drone aerial crop scouting and vegetation index mapping",
            "Sub-surface soil moisture and nitrogen deficit sensor network",
            "AI pest infestation and crop disease early detection vision models",
            "Variable-rate irrigation and fertilization prescription exports"
        ]
        monetization = raw.monetization_hypothesis or "Annual Subscription ($12/acre/year) + drone flight services"
        keywords = ["precision agriculture drones", "crop yield monitoring AI", "multispectral farm scouting", "smart irrigation"]
        queries = [
            "precision agriculture drone market size growth rate",
            "commercial farm crop health monitoring competitors John Deere Climate FieldView",
            "drone multispectral crop disease detection farmer adoption"
        ]
    elif any(k in text for k in ["edu", "tutor", "learn", "student", "teacher", "school", "course"]):
        name = raw.startup_name or "EduSpark Adaptive"
        tagline = "Hyper-personalized AI 1-on-1 tutor that adapts curriculum to individual student cognitive pacing."
        industry = industry or "EdTech & Generative AI"
        customers = customers or "K-12 school districts, private academies, and remote learning parents"
        key_features = [
            "Real-time diagnostic knowledge graph tracking concept mastery",
            "Socratic dialogue AI tutor with multi-modal problem solving",
            "Teacher dashboard with automated intervention alerts and student analytics",
            "Gamified progression milestones and curriculum alignment"
        ]
        monetization = raw.monetization_hypothesis or "B2B school licensing ($6/student/year) and B2C Pro tier ($19/mo)"
        keywords = ["adaptive AI tutoring", "K-12 personalized learning", "edtech Socratic tutor", "learning analytics"]
        queries = [
            "AI personalized learning edtech market size 2025 2030",
            "AI tutoring platform competitors Khanmigo synthesize edtech",
            "school district personalized learning adoption student outcomes"
        ]
    else:
        name = raw.startup_name or "NextGen Platform"
        tagline = f"An intelligent automated system solving {desc[:50]}..."
        industry = industry or "Enterprise SaaS & AI"
        customers = customers or "Mid-market businesses and operational leaders"
        key_features = [
            "Automated core workflow orchestration and intelligent processing engine",
            "Real-time analytics and situational intelligence dashboard",
            "Seamless API connectors for legacy enterprise databases",
            "Role-based collaboration and compliance audit logging"
        ]
        monetization = raw.monetization_hypothesis or "Tiered B2B SaaS ($99 to $499/month)"
        keywords = ["workflow automation", "enterprise AI software", f"{industry.lower()} software", "business intelligence"]
        queries = [
            f"{industry} market size forecast CAGR",
            f"top competitors and software platforms in {industry}",
            f"{industry} software customer pain points and pricing"
        ]

    return StructuredIdeaOutput(
        idea_name=name,
        tagline=tagline,
        problem_statement=desc,
        proposed_solution=f"A specialized {industry} platform that directly resolves this friction through intelligent automation and real-time operational optimization.",
        target_customers=customers,
        industry=industry,
        key_features=key_features,
        monetization_model=monetization,
        search_keywords=keywords,
        search_queries=queries,
        extraction_source="FALLBACK_RULE_BASED",
        status=f"partial (Fallback triggered: {error_reason})"
    )


def extract_idea_structure(raw: RawStartupSubmission) -> StructuredIdeaOutput:
    """
    Connects to LLM and returns structured StructuredIdeaOutput.
    Falls back gracefully if no API key is configured or on failure.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    user_input_prompt = (
        f"Startup Name: {raw.startup_name or 'N/A'}\n"
        f"Idea / Problem Description: {raw.description}\n"
        f"Target Customers: {raw.target_customers or 'N/A'}\n"
        f"Industry: {raw.industry or 'N/A'}\n"
        f"Geography: {raw.geography or 'Global'}\n"
        f"Monetization: {raw.monetization_hypothesis or 'N/A'}\n"
        f"Known Competitors: {raw.known_competitors or 'N/A'}"
    )

    structured_output: Optional[StructuredIdeaOutput] = None

    if gemini_key and not gemini_key.startswith("your_"):
        logger.info("Connecting to Google Gemini LLM for structured idea extraction...")
        try:
            raw_response = _call_gemini_api(SYSTEM_EXTRACTION_PROMPT, user_input_prompt, gemini_key)
            parsed_json = clean_and_parse_json(raw_response)
            parsed_json["extraction_source"] = "LLM_GEMINI"
            parsed_json["status"] = "success"
            structured_output = StructuredIdeaOutput.model_validate(parsed_json)
        except Exception as e:
            logger.warning(f"Gemini LLM extraction failed: {e}. Trying fallback...")
            structured_output = None

    if structured_output is None and openai_key and not openai_key.startswith("your_"):
        logger.info("Connecting to OpenAI LLM for structured idea extraction...")
        try:
            raw_response = _call_openai_api(SYSTEM_EXTRACTION_PROMPT, user_input_prompt, openai_key)
            parsed_json = clean_and_parse_json(raw_response)
            parsed_json["extraction_source"] = "LLM_OPENAI"
            parsed_json["status"] = "success"
            structured_output = StructuredIdeaOutput.model_validate(parsed_json)
        except Exception as e:
            logger.warning(f"OpenAI LLM extraction failed: {e}. Trying fallback...")
            structured_output = None

    if structured_output is None:
        reason = "No valid GEMINI_API_KEY or OPENAI_API_KEY in .env" if (not gemini_key and not openai_key) else "LLM API connection error"
        structured_output = _rule_based_fallback(raw, reason)

    return structured_output


def extract_idea_with_llm(raw: RawStartupSubmission) -> str:
    """Legacy helper returning JSON string for backward compatibility."""
    output = extract_idea_structure(raw)
    return json.dumps(output.model_dump(), indent=2)


if __name__ == "__main__":
    test_sub = RawStartupSubmission(
        startup_name="SmartPantry AI",
        description="Smart app that tracks grocery expiration dates from receipt photos, alerts users before food spoils, and suggests recipes using items already in the fridge.",
        industry="Consumer Tech & FoodTech"
    )
    result = extract_idea_structure(test_sub)
    print(f"Extracted Idea: {result.idea_name}")
    print(f"Tagline: {result.tagline}")
    print(f"Key Features: {len(result.key_features)}")
    print(f"Search Queries: {result.search_queries}")
