# AI Startup Idea Validator — Autonomous Multi-Agent Platform

Autonomous multi-agent platform for real-time startup feasibility assessment, market sizing (TAM/SAM/SOM), competitor intelligence, SWOT risk evaluation, lean MVP roadmapping, and conversational venture advisory.

---

## 🎯 Project Overview & Objective

Entrepreneurs and innovators frequently generate startup ideas but struggle to evaluate feasibility, market demand, competitive landscape, business viability, and execution challenges. Traditional startup validation requires extensive manual market research, competitor benchmarking, and business planning — time-consuming and difficult for early-stage founders with limited resources.

The **AI Startup Idea Validator** solves this by providing a unified multi-agent platform:
- The founder submits an idea in **2-3 lines**.
- The system automatically triggers an autonomous 8-phase agentic pipeline combining real-time web retrieval, LLM reasoning (Google Gemini / OpenAI), and quantitative venture scoring.
- Outputs an interactive **Startup Validation Dossier** with a **Feasibility Index (0–100)**, strategic verdict (**PROCEED / PIVOT / ABANDON**), and initializes a **Conversational Startup Advisor** grounded directly in the validation dossier.

---

## 🏛️ System Architecture & 9 Core Modules

```
                               ┌─────────────────────────────────┐
                               │   Module 1: Idea Intake Form    │
                               │   (2-3 lines raw text + domain) │
                               └────────────────┬────────────────┘
                                                ▼
                               ┌─────────────────────────────────┐
                               │     Idea Structuring Engine     │
                               │  (Pydantic normalization & taxonomy)
                               └────────────────┬────────────────┘
                                                ▼
                               ┌─────────────────────────────────┐
                               │ Module 2: Web Search Agent      │
                               │ (Tavily real-time intelligence) │
                               └────────┬───────────────┬────────┘
                                        │               │
                     ┌──────────────────┴──┐         ┌──┴──────────────────┐
                     ▼                     │         │                     ▼
     ┌───────────────────────────────┐     │         │     ┌───────────────────────────────┐
     │ Module 3: Market Opportunity  │     │         │     │ Module 4: Competitor Analysis │
     │ & Customer Segmentation Agent │     │         │     │ & Whitespace Benchmark Agent  │
     │ (TAM/SAM/SOM, CAGR, Personas) │     │         │     │ (5-Dim Matrix, Pricing, UVP)  │
     └───────────────┬───────────────┘     │         │     └───────────────┬───────────────┘
                     └──────────────────┐  │         │  ┌──────────────────┘
                                        ▼  ▼         ▼  ▼
                               ┌─────────────────────────────────┐
                               │ Module 5: SWOT & Risk Agent     │
                               │ (2x2 Matrix & Mitigation Plans) │
                               └────────────────┬────────────────┘
                                                ▼
                               ┌─────────────────────────────────┐
                               │ Module 6: MVP Recommendation    │
                               │ (MoSCoW Backlog & Tech Stack)   │
                               └────────────────┬────────────────┘
                                                ▼
                               ┌─────────────────────────────────┐
                               │ Module 7: Go-To-Market Module   │
                               │ (Channels, Tiers, 3 Launch Ph.) │
                               └────────────────┬────────────────┘
                                                ▼
                               ┌─────────────────────────────────┐
                               │ Module 8: Report Generator      │
                               │ (Feasibility Index 0-100 Dossier│
                               └────────────────┬────────────────┘
                                                ▼
                               ┌─────────────────────────────────┐
                               │ Module 9: Conversational        │
                               │ Startup Advisor (Interactive)   │
                               └─────────────────────────────────┘
```

---

## 📦 Implemented Modules Specification

| # | Module / Agent | File Path | Core Capabilities |
|---|---|---|---|
| **1** | **Startup Idea Submission & Workspace Module** | [`src/idea_extractor.py`](file:///c:/Users/Shravya%20K/OneDrive/Desktop/infosys/src/idea_extractor.py)<br>[`src/workspace_manager.py`](file:///c:/Users/Shravya%20K/OneDrive/Desktop/infosys/src/workspace_manager.py) | Ingests 2-3 line freeform ideas or rich form data; extracts taxonomy, problem, solution, target audience, keywords, and generates search queries. Manages saved workspace dossiers. |
| **2** | **Web Search and Data Retrieval Agent** | [`src/web_search_agent.py`](file:///c:/Users/Shravya%20K/OneDrive/Desktop/infosys/src/web_search_agent.py) | Connects to Tavily Search API (`advanced` search depth) to gather real-time market reports, competitor pricing, and regulations. Features high-fidelity domain fallback for offline execution. |
| **3** | **Market Opportunity & Customer Segmentation Agent** | [`src/market_analysis_agent.py`](file:///c:/Users/Shravya%20K/OneDrive/Desktop/infosys/src/market_analysis_agent.py) | Calculates TAM, SAM, and SOM figures with bottom-up rationales; evaluates CAGR growth rate, market tailwinds/headwinds, detailed customer personas, and assigns a Market Readiness Score (1-10). |
| **4** | **Competitor Discovery & Comparison Agent** | [`src/competitor_analysis_agent.py`](file:///c:/Users/Shravya%20K/OneDrive/Desktop/infosys/src/competitor_analysis_agent.py) | Discovers direct, indirect, and legacy rivals; profiles competitor pricing and customer-reported weaknesses; constructs a 5-dimension comparison matrix; maps uncontested whitespace and defines the UVP. |
| **5** | **SWOT & Risk Analysis Agent (RAG-Augmented)** | [`src/swot_risk_agent.py`](file:///c:/Users/Shravya%20K/OneDrive/Desktop/infosys/src/swot_risk_agent.py)<br>[`src/rag_startup_knowledge.py`](file:///c:/Users/Shravya%20K/OneDrive/Desktop/infosys/src/rag_startup_knowledge.py) | Synthesizes a 2x2 SWOT grid and categorized risk scorecard. **Augmented via RAG (Retrieval-Augmented Generation)** over 25+ real-world startup post-mortems (Juicero, Webvan, Fast, Quibi, CozZo, Too Good To Go) to warn founders of fatal mistakes others already made. |
| **6** | **MVP Feature Recommendation Agent** | [`src/mvp_agent.py`](file:///c:/Users/Shravya%20K/OneDrive/Desktop/infosys/src/mvp_agent.py) | Applies the MoSCoW Prioritization Framework (Must-Have, Should-Have, Could-Have, Won't-Have); prescribes modern tech stack with architectural justification; outlines an 8-week sprint roadmap and validation experiments. |
| **7** | **Go-To-Market (GTM) Strategy Generation Module** | [`src/gtm_agent.py`](file:///c:/Users/Shravya%20K/OneDrive/Desktop/infosys/src/gtm_agent.py) | Formulates multi-channel acquisition playbooks; generates **realistic, domain-adaptive pricing** (Freemium for Consumer B2C, commissions for Marketplaces, $29-$79/mo for SMB, and enterprise contracts for B2B); structures 3 launch phases with CAC:LTV unit economics. |
| **8** | **Startup Validation Report Generation Agent** | [`src/report_generator_agent.py`](file:///c:/Users/Shravya%20K/OneDrive/Desktop/infosys/src/report_generator_agent.py) | Calculates the weighted **Startup Feasibility Index (0-100)** across 4 strategic pillars (Market, Defensibility, Feasibility, Business Model); assigns clear verdict (**PROCEED / PIVOT / ABANDON**); exports to Markdown, Print/PDF, and JSON. |
| **9** | **Conversational Startup Advisor** | [`src/conversational_advisor.py`](file:///c:/Users/Shravya%20K/OneDrive/Desktop/infosys/src/conversational_advisor.py) | An interactive, persistent conversational advisor grounded directly in the generated dossier; advises on pilot pricing, investor decks, objection handling, and competitor defense with contextual suggested follow-up chips. |

---

## 🚀 Quick Start & How to Run

### 1. Run the End-to-End Terminal Pipeline
Executes all 9 modules sequentially and prints the executive dossier with a live advisor turn:
```powershell
python src/view_sample_pipeline.py
```

### 2. Launch the Full-Stack Web Application & API Server
Starts the FastAPI backend and serves the interactive web dashboard:
```powershell
python src/server.py
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in any browser.

The web dashboard features:
- **Idea Submission Form** with the single official layman-friendly starter preset: **SmartPantry AI** (an easy-to-understand app that tracks supermarket receipt expiry dates and suggests 15-minute recipes to prevent household food waste).
- **Live Pipeline Tracker** visualizing agent execution step-by-step.
- **Multi-Tab Validation Workspace** covering Executive Scorecard, Market Opportunity, Competitor Matrix, SWOT & Risk Matrix (with RAG Past Startup Post-Mortems), MVP Backlog, and Go-To-Market Playbook with realistic pricing.
- **Interactive Conversational Advisor** with chat history and contextual suggested follow-up chips.
- **Export Options**: Download Markdown report, Print/Save PDF report, or Copy full JSON.

### 3. Run the Unit & Integration Test Suite
```powershell
python -m unittest discover tests
```
*Runs 24 automated unit and integration tests across all agents, orchestrator, and API endpoints.*

---

## 📂 Project Directory Structure

```
infosys/
├── README.md                                  # Complete Project Overview & Guide
├── requirements.txt                           # Core dependencies (pydantic, fastapi, uvicorn, requests, etc.)
├── .env.example                               # Template for API keys (Tavily, Gemini, OpenAI)
├── src/
│   ├── __init__.py
│   ├── models.py                              # Pydantic schemas for all 9 modules & dossier
│   ├── idea_extractor.py                      # Module 1: Idea Ingestion & Structured Extractor
│   ├── workspace_manager.py                   # Module 1: Workspace Storage, Presets & Persistence
│   ├── web_search_agent.py                    # Module 2: Web Search & Intelligence Agent (Tavily)
│   ├── market_analysis_agent.py               # Module 3: Market Sizing (TAM/SAM/SOM) & Personas Agent
│   ├── competitor_analysis_agent.py           # Module 4: Competitor Discovery & Whitespace Agent
│   ├── swot_risk_agent.py                     # Module 5: SWOT & Risk Analysis Agent
│   ├── rag_startup_knowledge.py               # RAG: Historical Startup Post-Mortems & Precedents
│   ├── mvp_agent.py                           # Module 6: MoSCoW MVP Feature Recommendation Agent
│   ├── gtm_agent.py                           # Module 7: Go-To-Market & Tiered Pricing Module
│   ├── report_generator_agent.py              # Module 8: Validation Dossier & Feasibility Scoring Agent
│   ├── conversational_advisor.py              # Module 9: Grounded Conversational Startup Advisor
│   ├── orchestrator.py                        # Multi-Agent Workflow Orchestrator
│   ├── server.py                              # FastAPI Backend REST & Export Server
│   └── view_sample_pipeline.py                # Full 9-Module Pipeline CLI Demonstration
├── web/
│   ├── index.html                             # Full interactive modern web dashboard application
│   ├── submission_wireframe.html              # Standalone submission wireframe
│   └── swot_dashboard.html                    # Standalone SWOT & risk dashboard
├── tests/
│   ├── test_all_agents.py                     # Comprehensive tests for all 9 individual modules
│   ├── test_orchestrator.py                   # End-to-end pipeline integration tests
│   ├── test_api_server.py                     # FastAPI REST API endpoint tests
│   └── test_swot_risk_agent.py                # SWOT & Risk agent unit tests
└── data/
    └── workspaces/                            # Persistent JSON dossiers for validation workspaces
```

---

## 🔑 Environment Configuration (Optional)

The platform is architected with a **hybrid resilience engine**:
1. **Live Cloud API Mode**: If keys are provided in `.env`, the agents invoke live Google Gemini (`gemini-1.5-flash`), OpenAI (`gpt-4o-mini`), and Tavily Search API.
2. **Deterministic Fallback Engine**: If no API keys are present or during offline testing, verified domain knowledge synthesizers run automatically with zero runtime errors.

To configure live keys, create a `.env` file:
```env
# Tavily Real-Time Search API
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxx

# LLM Providers (Optional for live LLM extraction)
GEMINI_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxx
```

---
*Developed for the AI Startup Idea Validator Multi-Agent System Project.*
