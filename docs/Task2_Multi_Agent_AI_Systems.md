# Task 2: Study Multi-Agent AI Systems & Agent Specifications

**Project Title:** AI Startup Idea Validator  
**Milestone:** 1 (Week 1–2)  
**Date:** October 2026  

---

## 1. What are LLMs and AI Agents?

### Large Language Models (LLMs)
A **Large Language Model (LLM)** is a statistical deep neural network (typically a Transformer architecture) trained on vast corpuses of text to predict subsequent tokens and generate human-like language.
* **Capabilities:** Highly proficient at summarization, translation, code generation, reasoning over provided context, and semantic understanding.
* **Inherent Limitations:**
  * **Static Knowledge Cutoff:** Cannot inherently access information beyond its training cut-off date.
  * **Hallucinations:** Capable of generating plausible-sounding but factually inaccurate assertions when uncertain.
  * **No Direct Agency:** By default, an LLM cannot interact with external systems, execute database lookups, or perform API calls without external orchestration.

### AI Agents
An **AI Agent** is an autonomous entity that leverages an LLM as its central reasoning "brain", augmented with four architectural components:
1. **Perception / Goal Formulation:** Accepts a high-level goal and breaks it down into intermediate milestones.
2. **Tools & Actuators:** Has the capability to execute code, call external APIs (web search, databases, calculators), and read local files.
3. **Memory Systems:** 
   * *Short-term memory:* In-context conversational history and scratchpad reasoning.
   * *Long-term memory:* Vector stores or persistent session state.
4. **Planning & Reflection:** Uses paradigms like ReAct (Reason + Act), Chain-of-Thought (CoT), or self-consistency to critique its outputs and correct course when an action fails.

```
┌─────────────────────────────────────────────────────────────┐
│                       AI AGENT ANATOMY                      │
│                                                             │
│             ┌────────────────────────────────┐              │
│             │   Goal / Instruction Ingestion  │              │
│             └───────────────┬────────────────┘              │
│                             ▼                               │
│  ┌──────────────┐     ┌───────────┐     ┌────────────────┐  │
│  │ Short/Long   │◄───►│  LLM Core │◄───►│ Tools & APIs   │  │
│  │ Memory       │     │ Reasoning │     │ (Search/Exec)  │  │
│  └──────────────┘     └─────┬─────┘     └────────────────┘  │
│                             │                               │
│                             ▼                               │
│             ┌────────────────────────────────┐              │
│             │ Structured Output / Next Step  │              │
│             └────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Multi-Agent Systems (MAS) & Collaboration Patterns

In complex enterprise and business research tasks, a single agent attempting to do everything suffers from context contamination, degraded prompt focus, and shallow reasoning. 

A **Multi-Agent System** solves this by decomposing the macro-problem into modular, specialized agents that interact according to structured patterns:

### Primary Collaboration Patterns
1. **Sequential Chain (Pipeline Pattern):**
   * Output of Agent $A$ becomes the input context of Agent $B$.
   * *Best suited for:* Workflows with strict dependency requirements (e.g., cannot analyze competitors until search data is collected).
2. **Hierarchical / Supervisor Pattern (Manager-Worker):**
   * A lead orchestrator agent dispatches subtasks to specialist workers, reviews their outputs, and triggers retries if quality standards are not met.
3. **Parallel Scatter-Gather Pattern:**
   * An orchestrator triggers independent agents simultaneously (e.g., Market Analysis and Competitor Analysis running concurrently on the same search payload) and merges their results into a unified downstream agent (SWOT Analysis).

```
                      ┌────────────────────────┐
                      │ Raw Startup Submission │
                      └───────────┬────────────┘
                                  ▼
                      ┌────────────────────────┐
                      │ Idea Structuring Agent │
                      └───────────┬────────────┘
                                  ▼
                      ┌────────────────────────┐
                      │    Web Search Agent    │
                      └───────────┬────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
       ┌──────────────────────┐       ┌──────────────────────┐
       │   Market Analysis    │       │ Competitor Analysis  │
       │        Agent         │       │        Agent         │
       └──────────┬───────────┘       └──────────┬───────────┘
                  └───────────────┬───────────────┘
                                  ▼
                      ┌────────────────────────┐
                      │ SWOT & Risk Analysis   │
                      │         Agent          │
                      └───────────┬────────────┘
                                  ▼
                      ┌────────────────────────┐
                      │   MVP Recommendation   │
                      │         Agent          │
                      └───────────┬────────────┘
                                  ▼
                      ┌────────────────────────┐
                      │   Report Generation    │
                      │         Agent          │
                      └───────────┬────────────┘
                                  ▼
                      ┌────────────────────────┐
                      │ Final Validation Report│
                      └────────────────────────┘
```

---

## 3. Specifications for the 6 Project Agents

Below are the detailed definitions, responsibilities, input dependencies, and output schemas for each agent in the **AI Startup Idea Validator** pipeline.

---

### Agent 1: Web Search Agent
* **Role Title:** Real-Time Market & Competitive Intelligence Researcher
* **Core Responsibilities:**
  1. Receive the structured startup idea (target industry, keywords, value proposition).
  2. Formulate high-precision web queries optimized for retrieval (e.g., industry market size reports, competitor pricing pages, regulatory mandates).
  3. Execute multi-query searches via Tavily API / Google Serper.
  4. Filter, sanitize, and de-duplicate search snippets to remove SEO spam, forum noise, and redundant pages.
  5. Structure the raw data into categorized intelligence packets (Market Data, Competitor Data, Customer Sentiment).
* **Inputs:** Structured Idea Profile (`idea_name`, `industry`, `target_audience`, `core_problem`, `keywords`).
* **Tools / APIs:** Tavily Search API (`search_depth="advanced"`, `include_raw_content=False`, `max_results=7`).
* **Output Contract:**
  ```json
  {
    "market_search_results": [
      {"title": "Commercial EV Market Report 2025", "url": "...", "snippet": "..."}
    ],
    "competitor_search_results": [
      {"title": "Geotab Fleet Telematics", "url": "...", "snippet": "..."}
    ],
    "regulatory_results": [
      {"title": "Clean Fleets Directive Overview", "url": "...", "snippet": "..."}
    ]
  }
  ```

---

### Agent 2: Market Analysis Agent
* **Role Title:** Industry Opportunity & Demographic Analyst
* **Core Responsibilities:**
  1. Estimate addressable market potential (TAM, SAM, SOM) using verified industry data from the Web Search Agent.
  2. Identify primary market growth drivers, headwinds, and Compound Annual Growth Rate (CAGR).
  3. Formulate detailed Customer Personas (pain points, behavioral triggers, willingness to pay, budget gatekeepers).
  4. Assess market timing ("Why now?"): technological inflection points, consumer shifts, or regulatory changes.
* **Inputs:** Structured Idea Profile + `market_search_results` from Web Search Agent.
* **Tools / APIs:** LLM Reasoning Engine (Structured Output Prompting).
* **Output Contract:**
  * Market Size Breakdown (TAM, SAM, SOM with qualitative justifications).
  * 3–5 Year Market Growth Projection.
  * Primary Customer Personas (Role, Goals, Daily Friction, Budget Authority).
  * Market Readiness Score (1–10) with rationale.

---

### Agent 3: Competitor Analysis Agent
* **Role Title:** Competitive Intelligence & Market Differentiation Strategist
* **Core Responsibilities:**
  1. Identify direct, indirect, and substitute competitors based on search retrieval.
  2. Analyze competitor pricing structures, core capabilities, and known limitations (via reviews, user feedback).
  3. Construct a feature-by-feature Competitive Differentiation Matrix.
  4. Identify defensible market gaps and recommend the startup's "Unique Value Proposition" (UVP).
* **Inputs:** Structured Idea Profile + `competitor_search_results`.
* **Tools / APIs:** LLM Reasoning Engine with Tabular Comparison Templates.
* **Output Contract:**
  * Direct Competitors List (Profiles, Strengths, Weaknesses, Pricing).
  * Indirect & Substitute Solutions List.
  * Competitive Matrix (Feature comparison table across 5 key dimensions).
  * White Space / Uncontested Market Gap definition.

---

### Agent 4: SWOT and Risk Analysis Agent
* **Role Title:** Enterprise Risk Assessor & Strategic Evaluator
* **Core Responsibilities:**
  1. Synthesize internal factors (**Strengths** derived from proposed innovation, **Weaknesses** stemming from early-stage resource constraints).
  2. Synthesize external factors (**Opportunities** uncovered by Market Agent, **Threats** identified by Competitor Agent).
  3. Conduct categorical Risk Evaluation:
     * *Technical Feasibility Risk:* API availability, AI hallucinations, hardware dependencies.
     * *Market & Adoption Risk:* Customer inertia, high switching costs, extended sales cycles.
     * *Regulatory & Compliance Risk:* Data governance, privacy laws, governmental policy shifts.
  4. Propose actionable mitigation strategies for every high-severity risk.
* **Inputs:** Market Analysis Output + Competitor Analysis Output + Structured Idea Profile.
* **Tools / APIs:** LLM Reasoning Engine (SWOT Framework Prompting).
* **Output Contract:**
  * 2x2 SWOT Matrix.
  * Risk Scorecard (Risk Item, Category, Likelihood [High/Med/Low], Impact [High/Med/Low], Mitigation Plan).

---

### Agent 5: MVP Recommendation Agent
* **Role Title:** Product Management & Agile Scoping Advisor
* **Core Responsibilities:**
  1. Prevent "feature bloat" by stripping the concept down to the absolute minimal feature set required to test the core value hypothesis.
  2. Apply the **MoSCoW Prioritization Framework**:
     * **Must-Have:** Non-negotiable features needed for basic utility.
     * **Should-Have:** Important features deferred to v1.1.
     * **Could-Have:** Desirable enhancements.
     * **Won't-Have:** Features explicitly out of scope for the MVP.
  3. Define actionable Key Performance Indicators (KPIs) and validation experiments (e.g., Smoke Test, Concierge MVP, Pre-sale commitments).
* **Inputs:** Structured Idea + SWOT & Risk Output + Competitive Gaps.
* **Tools / APIs:** LLM Reasoning Engine (Agile Product Frameworks).
* **Output Contract:**
  * Core Value Hypothesis to Validate.
  * Prioritized Feature Backlog (MoSCoW categories).
  * Recommended Tech Stack & Integration APIs.
  * 30-Day Validation Experiment Plan with quantitative success benchmarks.

---

### Agent 6: Report Generation Agent
* **Role Title:** Executive Synthesis & Documentation Publisher
* **Core Responsibilities:**
  1. Collate, harmonize, and format outputs from all preceding agents into a coherent, professional validation dossier.
  2. Calculate an aggregate **Startup Feasibility Index (0–100)** across four weighted pillars: Market Demand (30%), Competitive Advantage (25%), Business Feasibility (25%), and Execution Risk (20%).
  3. Provide an unambiguous executive recommendation: **Proceed (Green Light)**, **Pivot (Orange Light)**, or **Abandon (Red Light)**.
  4. Generate both Markdown and structured JSON report representations ready for UI rendering and PDF export.
* **Inputs:** Complete aggregate state from Agents 1 through 5.
* **Tools / APIs:** Markdown / Document Formatting Engine, Scoring Heuristic Algorithms.
* **Output Contract:** Comprehensive Final Startup Validation Report.

---
*Authored for Infosys AI Startup Idea Validator Project — Milestone 1 Deliverable.*
