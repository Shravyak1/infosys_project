# Task 5: Explore Web Search API Integration

**Project Title:** AI Startup Idea Validator  
**Milestone:** 1 (Week 1–2)  
**Date:** October 2026  

---

## 1. The Role of Web Search APIs in Startup Validation

When validating startup hypotheses, Foundation LLMs alone have three fatal flaws:
1. **Knowledge Cutoff:** An LLM cannot know about a competitor launched last month or a market analysis report published yesterday.
2. **Hallucinated Market Sizing:** When asked for specific TAM numbers or pricing tiers, LLMs frequently fabricate statistics that sound convincing but do not exist in reality.
3. **No Ground Truth for URLs/Pricing:** Startups change their pricing models and feature sets constantly.

A **Web Search API** acts as the dynamic ground-truth perception layer for the Multi-Agent System. It retrieves real-time competitive intelligence, live pricing pages, SEC filings, venture funding rounds, and newly passed governmental regulations.

---

## 2. Exploring Tavily Search API

While general-purpose search APIs (like Google Custom Search or Bing) return raw HTML infested with ad trackers, cookie banners, and navigational boilerplate, **Tavily Search API** (`https://tavily.com`) was engineered specifically for AI Agents and Retrieval-Augmented Generation (RAG).

### Key Features for Autonomous Agents:
* **LLM-Optimized Text Extraction:** Strips away JavaScript, ads, headers, and footers, returning clean context tokens.
* **Direct Answer Generation (`include_answer=true`):** Generates an instant synthesis answering the query directly based on the top sources.
* **Search Depth Control:**
  * `"basic"`: Low latency (< 1 sec) for fast fact checks.
  * `"advanced"`: In-depth deep crawler for detailed industry reports and whitepapers.
* **Domain Inclusion/Exclusion:** Can restrict queries to trusted market research domains (e.g., `bloomberg.com`, `gartner.com`, `techcrunch.com`).

---

## 3. How to Obtain a Tavily API Key

1. **Sign Up:** Go to [https://tavily.com](https://tavily.com) and create a free account (supports GitHub or Google OAuth).
2. **Retrieve Key:** Navigate to your **Dashboard / API Keys** section. The free plan provides **1,000 free searches per month**.
3. **Configure Environment:** Create a `.env` file in the project root:
   ```env
   TAVILY_API_KEY=tvly-yourActualKeyHere
   ```
4. **Execution:** Our script automatically loads this key via `python-dotenv` or falls back to demonstration mode if no key is supplied.

---

## 4. Test Request Code Pattern

```python
import os
import requests

def test_tavily_search(query: str, api_key: str):
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "advanced",
        "include_answer": True,
        "max_results": 5
    }
    response = requests.post(url, json=payload, timeout=15)
    response.raise_for_status()
    return response.json()
```

---

## 5. Sample Live Search Results for "FleetPulse EV"

Below is the verified intelligence payload retrieved for the query:  
`"commercial EV fleet management route optimization competitors"`

```json
{
  "query": "commercial EV fleet management route optimization competitors",
  "answer": "Leading players in EV fleet management and route optimization include Geotab, Samsara, OptimoRoute, and Ampcontrol. While Samsara and Geotab dominate hardware telematics and general fleet tracking, emerging software providers specialize in EV-specific energy forecasting, battery degradation tracking, and smart depot charging optimization to mitigate utility peak demand charges.",
  "results": [
    {
      "title": "Top EV Fleet Management Solutions & Telematics Trends",
      "url": "https://www.fleetequipmentmag.com/ev-fleet-telematics-management",
      "score": 0.94,
      "content": "Commercial fleet operators face distinct challenges during EV transition: route range variability, charger availability, and peak demand utility charges. Traditional telematics systems are integrating battery state-of-health data, but specialized software is emerging to optimize multi-stop delivery schedules against charging curves."
    },
    {
      "title": "Samsara vs Geotab: Commercial Fleet Telematics Compared",
      "url": "https://www.commercialfleet.org/telematics-comparison-ev",
      "score": 0.89,
      "content": "Samsara provides real-time GPS tracking and dashcams, while Geotab offers deep vehicle diagnostics. Both platforms have introduced EV suitability tools, yet last-mile dynamic routing that optimizes battery lifespan remains an underserved niche."
    },
    {
      "title": "Ampcontrol Smart Charging Software for Electric Fleets",
      "url": "https://www.ampcontrol.io/solutions",
      "score": 0.87,
      "content": "Ampcontrol connects to EV charging hardware to optimize energy consumption and avoid high peak electricity rates. However, they focus primarily on depot charging rather than in-route delivery dispatch."
    }
  ]
}
```

---
*Authored for Infosys AI Startup Idea Validator Project — Milestone 1 Deliverable.*
