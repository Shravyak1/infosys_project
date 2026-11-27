# Task 3: System Architecture & Data Flow Design

**Project Title:** AI Startup Idea Validator  
**Milestone:** 1 (Week 1–2)  
**Date:** October 2026  

---

## 1. System Architecture Overview

The **AI Startup Idea Validator** uses a modern, modular, service-oriented multi-agent architecture. It decouples the user-facing web interface, backend workflow orchestration, autonomous agent reasoning, and external API integrations into clearly delineated tiers.

```mermaid
graph TD
    %% TIER 1: CLIENT PRESENTATION
    subgraph TIER_1 ["Tier 1: Client Presentation Layer"]
        UI_Web["Web Application (React / Next.js / Tailwind CSS)"]
        UI_Form["Startup Idea Submission Form"]
        UI_Tracker["Live Agent Progress Stepper / WebSocket"]
        UI_Report["Interactive Report & PDF Downloader"]
        UI_Web --> UI_Form
        UI_Web --> UI_Tracker
        UI_Web --> UI_Report
    end

    %% TIER 2: BACKEND & ORCHESTRATION
    subgraph TIER_2 ["Tier 2: API & Orchestration Layer"]
        API_Gateway["API Gateway (FastAPI / REST & WebSockets)"]
        Idea_Parser["Idea Ingestion & LLM Structured Parser"]
        Orchestrator["Agent Workflow Engine (StateGraph / Asyncio Pipeline)"]
        State_Manager["Session State & Shared Memory Store"]
        
        API_Gateway --> Idea_Parser
        Idea_Parser --> Orchestrator
        Orchestrator <--> State_Manager
    end

    %% TIER 3: MULTI-AGENT EXECUTION LAYER
    subgraph TIER_3 ["Tier 3: Autonomous Agent Execution Layer"]
        Agent_Search["1. Web Search Agent"]
        Agent_Market["2. Market Analysis Agent"]
        Agent_Comp["3. Competitor Analysis Agent"]
        Agent_SWOT["4. SWOT & Risk Agent"]
        Agent_MVP["5. MVP Recommendation Agent"]
        Agent_Report["6. Report Generation Agent"]

        Orchestrator --> Agent_Search
        Agent_Search --> Agent_Market
        Agent_Search --> Agent_Comp
        Agent_Market --> Agent_SWOT
        Agent_Comp --> Agent_SWOT
        Agent_SWOT --> Agent_MVP
        Agent_MVP --> Agent_Report
    end

    %% TIER 4: EXTERNAL SERVICES & FOUNDATION MODELS
    subgraph TIER_4 ["Tier 4: External Services & Foundation Models"]
        Tavily_API["Tavily Search API / Live Web Engine"]
        LLM_Engine["Foundation LLMs (Gemini 1.5 Pro / GPT-4o / Claude)"]
    end

    %% CONNECTIONS
    UI_Form -->|HTTP POST /api/submit| API_Gateway
    API_Gateway -->|WebSocket Events| UI_Tracker
    Agent_Report -->|Final Report JSON| API_Gateway
    API_Gateway -->|Render Data| UI_Report

    Agent_Search <-->|REST API Queries| Tavily_API
    Agent_Search <-->|Prompt / Reasoning| LLM_Engine
    Agent_Market <-->|Prompt / Reasoning| LLM_Engine
    Agent_Comp <-->|Prompt / Reasoning| LLM_Engine
    Agent_SWOT <-->|Prompt / Reasoning| LLM_Engine
    Agent_MVP <-->|Prompt / Reasoning| LLM_Engine
    Agent_Report <-->|Prompt / Reasoning| LLM_Engine
```

---

## 2. Component Roles and Responsibilities

| System Component | Technology Stack | Core Role & Responsibilities |
| :--- | :--- | :--- |
| **User Interface (UI)** | React / Tailwind CSS / HTML5 | • Provides an intuitive, responsive submission portal for founders.<br>• Streams real-time visual progress as each agent activates and completes.<br>• Renders the final interactive report with charts, SWOT matrices, and PDF export. |
| **Backend API Layer** | FastAPI / Python 3.11 / Pydantic | • Exposes asynchronous REST endpoints for submission, status polling, and report retrieval.<br>• Maintains persistent WebSocket connections for real-time status streaming.<br>• Enforces request validation and rate limiting. |
| **LLM Reasoning Engine** | Google Gemini / OpenAI API | • Performs contextual reasoning, entity extraction, competitive synthesis, and report drafting.<br>• Governed by strict system prompts and structured output schemas (JSON/Pydantic). |
| **Web Search API** | Tavily Search API | • Delivers clean, low-latency, real-time web intelligence specifically parsed for LLMs.<br>• Eliminates training cutoff limitations and verifies live market facts, competitors, and pricing. |
| **Workflow Orchestrator** | Custom Async Pipeline / LangGraph | • Coordinates the sequence and parallel execution of agents.<br>• Manages the shared state dictionary (context passing between agents).<br>• Implements error handling, retries, and fallback logic if an agent fails. |

---

## 3. End-to-End Information Flow

Here is the step-by-step trace of how a submitted startup idea flows through the system to become an executive validation report:

```mermaid
sequenceDiagram
    autonumber
    actor Founder as Founder (User)
    participant UI as User Interface
    participant Backend as FastAPI Backend
    participant Parser as LLM Idea Parser
    participant Orchestrator as Agent Orchestrator
    participant SearchAgent as Web Search Agent
    participant Tavily as Tavily Web Search API
    participant AnalysisAgents as Market & Competitor Agents
    participant StrategicAgents as SWOT & MVP Agents
    participant ReportAgent as Report Generation Agent

    Founder->>UI: Submits startup idea (2-3 lines + metadata)
    UI->>Backend: POST /api/validate-idea
    Backend->>Parser: Ingest raw freeform text
    Parser-->>Backend: Return Structured Idea Schema (JSON)
    Backend->>Orchestrator: Initialize pipeline with Idea State
    Backend-->>UI: Return Session ID + Start WebSocket Stream

    Note over Orchestrator, SearchAgent: Phase 1: Real-Time Intelligence Gathering
    Orchestrator->>SearchAgent: Formulate search queries for Market & Competitors
    SearchAgent->>Tavily: Execute targeted web queries
    Tavily-->>SearchAgent: Raw search results & sanitized snippets
    SearchAgent-->>Orchestrator: Categorized Market & Competitor Intelligence

    Note over Orchestrator, AnalysisAgents: Phase 2: Parallel Domain Analysis
    par Parallel Execution
        Orchestrator->>AnalysisAgents: Run Market Analysis Agent (TAM/SAM/SOM, Personas)
    and
        Orchestrator->>AnalysisAgents: Run Competitor Analysis Agent (Direct/Indirect, Matrix)
    end
    AnalysisAgents-->>Orchestrator: Return Market Opportunity & Competitor Benchmarks

    Note over Orchestrator, StrategicAgents: Phase 3: Strategic Synthesis & Scoping
    Orchestrator->>StrategicAgents: Run SWOT & Risk Analysis Agent
    StrategicAgents-->>Orchestrator: Return SWOT Grid + Risk Mitigation Matrix
    Orchestrator->>StrategicAgents: Run MVP Recommendation Agent (MoSCoW features)
    StrategicAgents-->>Orchestrator: Return Prioritized MVP Scope & 30-Day Plan

    Note over Orchestrator, ReportAgent: Phase 4: Executive Compilation & Scoring
    Orchestrator->>ReportAgent: Aggregate full session state
    ReportAgent-->>Orchestrator: Final Validation Report + Feasibility Score (0-100)
    Orchestrator-->>Backend: Pipeline execution completed
    Backend-->>UI: Push "COMPLETE" event via WebSocket
    UI->>Backend: GET /api/report/{session_id}
    Backend-->>UI: Return Complete Report JSON
    UI-->>Founder: Renders Interactive Validation Dossier & PDF Export
```

### Detailed Execution Stages:
1. **Intake & Normalization:** Founder fills out the submission form. The backend uses an extraction prompt to transform unstructured founder notes into a validated Pydantic model containing canonical industry categories, key search terms, and pain points.
2. **Search Orchestration:** The Web Search Agent generates queries such as `"[Industry] market size 2025 2026 report"`, `"[Idea keywords] top competitors pricing"`, and `"[Problem] customer challenges"`. It queries Tavily and aggregates verified sources.
3. **Parallel Analysis:** The Market Analysis Agent and Competitor Analysis Agent run simultaneously, utilizing the fresh search context to calculate TAM/SAM/SOM and map existing player gaps.
4. **Synthesis & Risk Mapping:** Armed with market numbers and competitor strengths, the SWOT & Risk Agent maps out vulnerability profiles and execution roadblocks.
5. **Product Scoping:** The MVP Recommendation Agent takes those risks and competitive gaps, determining the leanest feature set required to validate the core value proposition.
6. **Report Compilation & Scoring:** The Report Generation Agent computes a weighted viability score (0–100), summarizes go-to-market next steps, and formats the final artifact for immediate founder review.

---
*Authored for Infosys AI Startup Idea Validator Project — Milestone 1 Deliverable.*
