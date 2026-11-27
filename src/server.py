"""
FastAPI Backend Server
Project: AI Startup Idea Validator

Exposes REST and SSE endpoints for:
- Startup Idea Submission and Validation Pipeline
- Workspace Management & Saved Dossiers
- Conversational Startup Advisor Chat Grounded in Dossiers
- Markdown, JSON, and Printable HTML Exports
- Static UI Hosting
"""

import os
import sys
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.models import (
    RawStartupSubmission,
    ValidationDossierReport,
    AdvisorChatRequest,
    AdvisorChatResponse,
    ChatMessage,
    WorkspaceSession
)
from src.orchestrator import StartupValidationOrchestrator
from src.workspace_manager import (
    list_workspaces,
    load_workspace,
    save_workspace,
    get_default_presets
)
from src.report_generator_agent import export_to_markdown
from src.conversational_advisor import ConversationalAdvisorAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ValidationServer")

app = FastAPI(
    title="AI Startup Idea Validator API",
    description="Multi-Agent Platform for Autonomous Startup Validation and Advisory",
    version="2.0.0"
)

# Enable CORS for flexible local development and web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = StartupValidationOrchestrator()
advisor_agent = ConversationalAdvisorAgent()


# Auth and System Models
class LoginRequest(BaseModel):
    email: str
    password: Optional[str] = "demo123"
    role: Optional[str] = "Venture Capital Partner"
    remember_me: Optional[bool] = True

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "Founder & CEO"
    organization: Optional[str] = "Stealth Startup"

class AuthResponse(BaseModel):
    success: bool
    token: str
    user: Dict[str, Any]
    message: str


# ===========================================================================
# API Endpoints
# ===========================================================================

@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    """Returns system status, active LLMs, and search API configuration."""
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()

    return {
        "status": "online",
        "timestamp": os.path.basename(str(root_dir)),
        "llm_gemini_active": bool(gemini_key and not gemini_key.startswith("your_")),
        "llm_openai_active": bool(openai_key and not openai_key.startswith("your_")),
        "tavily_search_active": bool(tavily_key and not tavily_key.startswith("your_")),
        "mode": "HYBRID (Live APIs with Intelligent Domain Fallbacks)"
    }


@app.get("/api/presets")
def get_presets(all: bool = False) -> List[Dict[str, Any]]:
    """Returns curated starter ideas for one-click validation.
    Set all=true to return all industry starter presets."""
    return get_default_presets(include_all=all)


@app.post("/api/auth/login", response_model=AuthResponse)
def login_endpoint(req: LoginRequest) -> AuthResponse:
    """Authenticates a user or demo analyst profile."""
    email = req.email.strip().lower()
    # Demo presets or custom credentials
    role_map = {
        "partner@horizonvc.com": ("Alex Morgan", "Venture Capital Partner", "Horizon Ventures"),
        "founder@smartpantry.ai": ("Elena Rostova", "Founder & CEO", "SmartPantry AI"),
        "analyst@innovation.io": ("Marcus Chen", "Senior Venture Analyst", "Infosys Innovation Lab"),
        "lead@enterprise.com": ("Sarah Vance", "Enterprise Innovation Lead", "Infosys Consulting")
    }
    
    if email in role_map:
        name, role, org = role_map[email]
    else:
        # Generic login
        name = email.split("@")[0].replace(".", " ").title() if "@" in email else "Demo Executive"
        role = req.role or "Venture Capital Partner"
        org = "Venture Strategy Group"

    token = f"jwt-session-{uuid.uuid4().hex[:16]}"
    return AuthResponse(
        success=True,
        token=token,
        user={
            "id": f"usr-{uuid.uuid4().hex[:8]}",
            "name": name,
            "email": email,
            "role": role,
            "organization": org,
            "avatar": f"https://api.dicebear.com/7.x/initials/svg?seed={name.replace(' ', '+')}&backgroundColor=2563eb,1d4ed8,0284c7"
        },
        message="Authentication successful"
    )


@app.post("/api/auth/register", response_model=AuthResponse)
def register_endpoint(req: RegisterRequest) -> AuthResponse:
    """Registers a new founder or analyst account."""
    name = req.name.strip()
    email = req.email.strip().lower()
    role = req.role or "Founder & CEO"
    org = req.organization or "Stealth Venture"

    token = f"jwt-session-{uuid.uuid4().hex[:16]}"
    return AuthResponse(
        success=True,
        token=token,
        user={
            "id": f"usr-{uuid.uuid4().hex[:8]}",
            "name": name,
            "email": email,
            "role": role,
            "organization": org,
            "avatar": f"https://api.dicebear.com/7.x/initials/svg?seed={name.replace(' ', '+')}&backgroundColor=2563eb,1d4ed8,0284c7"
        },
        message="Account created successfully"
    )


@app.get("/api/auth/me")
def get_current_user_profile():
    """Returns currently authenticated session metadata."""
    return {
        "authenticated": True,
        "default_role": "Venture Capital Partner",
        "demo_accounts": [
            {"email": "partner@horizonvc.com", "name": "Alex Morgan", "role": "Venture Capital Partner", "org": "Horizon Ventures"},
            {"email": "founder@smartpantry.ai", "name": "Elena Rostova", "role": "Founder & CEO", "org": "SmartPantry AI"},
            {"email": "analyst@innovation.io", "name": "Marcus Chen", "role": "Senior Venture Analyst", "org": "Infosys Innovation Lab"}
        ]
    }


def validate_description_depth(description: Optional[str]) -> str:
    """
    Validates that the startup idea description is at least 2-3 lines.
    A standard line contains ~30-50 characters or ~7-10 words.
    Therefore, 2-3 lines requires either:
    - Multiple lines (2+ non-empty lines) with substantive content (>= 45 chars, >= 8 words), or
    - A single continuous paragraph with at least 60 characters and >= 10 words.
    """
    if not description:
        raise HTTPException(
            status_code=400, 
            detail="Idea description is required and must be at least 2-3 lines."
        )

    desc = description.strip()
    words = desc.split()
    lines = [l.strip() for l in desc.splitlines() if l.strip()]

    is_valid_multiline = (len(lines) >= 2 and len(desc) >= 45 and len(words) >= 8)
    is_valid_prose = (len(desc) >= 60 and len(words) >= 10)

    if not (is_valid_multiline or is_valid_prose):
        raise HTTPException(
            status_code=400,
            detail="Idea description is too short (below 2-3 lines). Please provide at least 2-3 lines (minimum 60 characters and 10+ words) detailing the core problem and your proposed solution."
        )

    return desc


@app.post("/api/validate", response_model=ValidationDossierReport)
def validate_startup_idea(submission: RawStartupSubmission) -> ValidationDossierReport:
    """
    Submits a startup idea (2-3 lines or detailed) and triggers
    the complete 8-agent validation pipeline.
    Rejects submissions with descriptions below 2-3 lines.
    """
    validate_description_depth(submission.description)

    try:
        logger.info(f"Triggering validation pipeline for idea: '{submission.startup_name}'")
        dossier = orchestrator.run_pipeline(submission)
        return dossier
    except Exception as e:
        logger.error(f"Validation pipeline failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.get("/api/workspaces")
def get_workspaces_list() -> List[Dict[str, Any]]:
    """Lists all saved validation workspace sessions."""
    return list_workspaces()


@app.get("/api/workspace/{session_id}")
def get_workspace_session(session_id: str) -> Dict[str, Any]:
    """Retrieves full saved workspace dossier and chat history."""
    workspace = load_workspace(session_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace session not found.")
    return workspace.model_dump()


@app.post("/api/advisor/chat", response_model=AdvisorChatResponse)
def chat_with_advisor(req: AdvisorChatRequest) -> AdvisorChatResponse:
    """
    Interacts with the Conversational Startup Advisor grounded in
    the validation dossier for the given session.
    """
    workspace = load_workspace(req.session_id)
    dossier = workspace.report if workspace else None

    # Execute advisor chat
    response = advisor_agent.chat(req, dossier)

    # Persist conversation turn to workspace
    if workspace:
        workspace.chat_history.append(ChatMessage(role="user", content=req.message))
        workspace.chat_history.append(ChatMessage(role="assistant", content=response.response))
        save_workspace(workspace)

    return response


@app.get("/api/export/{session_id}/markdown")
def export_markdown_report(session_id: str):
    """Exports the validation dossier as a downloadable Markdown document."""
    workspace = load_workspace(session_id)
    if not workspace or not workspace.report:
        raise HTTPException(status_code=404, detail="Report not found for this session.")
    
    md_content = export_to_markdown(workspace.report)
    filename = f"{workspace.report.idea_name.replace(' ', '_').lower()}_validation_dossier.md"
    return PlainTextResponse(
        content=md_content,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/export/{session_id}/html")
def export_printable_html(session_id: str):
    """Generates an executive print-ready HTML dossier for PDF export."""
    workspace = load_workspace(session_id)
    if not workspace or not workspace.report:
        raise HTTPException(status_code=404, detail="Report not found for this session.")
    
    r = workspace.report
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{r.idea_name} - Startup Validation Dossier</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @media print {{
      body {{ font-size: 12pt; background: #fff !important; color: #000 !important; }}
      .no-print {{ display: none !important; }}
      .page-break {{ page-break-before: always; }}
    }}
  </style>
</head>
<body class="bg-slate-50 text-slate-800 p-8 max-w-5xl mx-auto">
  <div class="no-print mb-6 flex justify-between items-center bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
    <span class="text-sm font-semibold text-slate-600">Executive Print Preview</span>
    <button onclick="window.print()" class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700">
      🖨️ Print / Save as PDF
    </button>
  </div>

  <div class="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
    <div class="border-b border-slate-200 pb-6 mb-6">
      <div class="flex justify-between items-start">
        <div>
          <h1 class="text-3xl font-extrabold text-slate-900">{r.idea_name}</h1>
          <p class="text-slate-500 font-medium mt-1">{r.tagline}</p>
          <span class="inline-block mt-2 px-3 py-1 bg-slate-100 text-slate-700 text-xs font-semibold rounded-md">
            Industry: {r.structured_idea.industry}
          </span>
        </div>
        <div class="text-right">
          <div class="text-3xl font-black text-blue-600">{r.feasibility_score} / 100</div>
          <div class="text-xs font-bold uppercase tracking-wider text-slate-500 mt-1">Feasibility Index</div>
          <span class="inline-block mt-2 px-3 py-1 bg-emerald-100 text-emerald-800 text-xs font-bold rounded-full">
            {r.verdict}
          </span>
        </div>
      </div>
    </div>

    <section class="mb-8">
      <h2 class="text-xl font-bold text-slate-900 mb-3">Executive Summary</h2>
      <p class="text-slate-700 leading-relaxed whitespace-pre-line">{r.executive_summary}</p>
    </section>

    <section class="mb-8">
      <h2 class="text-xl font-bold text-slate-900 mb-3">Feasibility Pillar Breakdown</h2>
      <div class="grid grid-cols-2 gap-4">
        {"".join([f'''
        <div class="p-4 bg-slate-50 rounded-xl border border-slate-200">
          <div class="flex justify-between items-center mb-1">
            <span class="font-bold text-slate-800">{p.pillar_name}</span>
            <span class="font-black text-blue-600">{p.score}/100</span>
          </div>
          <p class="text-xs text-slate-600">{p.rationale}</p>
        </div>''' for p in r.pillar_scores])}
      </div>
    </section>

    <section class="mb-8">
      <h2 class="text-xl font-bold text-slate-900 mb-3">Market Opportunity & Customer Personas</h2>
      <div class="grid grid-cols-3 gap-4 mb-4">
        <div class="p-3 bg-blue-50 border border-blue-100 rounded-lg">
          <span class="text-xs font-bold text-blue-700">TAM (Total Market)</span>
          <p class="font-extrabold text-blue-900 text-sm">{r.market_analysis.market_size.tam_value}</p>
        </div>
        <div class="p-3 bg-blue-50 border border-blue-100 rounded-lg">
          <span class="text-xs font-bold text-blue-700">SAM (Serviceable)</span>
          <p class="font-extrabold text-blue-900 text-sm">{r.market_analysis.market_size.sam_value}</p>
        </div>
        <div class="p-3 bg-blue-50 border border-blue-100 rounded-lg">
          <span class="text-xs font-bold text-blue-700">CAGR Growth</span>
          <p class="font-extrabold text-blue-900 text-sm">{r.market_analysis.cagr_growth_rate}</p>
        </div>
      </div>
      <p class="text-sm text-slate-700"><strong>Why Now:</strong> {r.market_analysis.why_now_rationale}</p>
    </section>

    <section class="mb-8">
      <h2 class="text-xl font-bold text-slate-900 mb-3">Competitive Whitespace & UVP</h2>
      <p class="text-sm text-slate-700 mb-2"><strong>Uncontested Whitespace:</strong> {r.competitor_analysis.uncontested_white_space}</p>
      <div class="p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-sm font-semibold">
        Unique Value Proposition: "{r.competitor_analysis.unique_value_proposition}"
      </div>
    </section>

    <section class="mb-8">
      <h2 class="text-xl font-bold text-slate-900 mb-3">Immediate 14-Day Next Steps</h2>
      <ul class="space-y-2">
        {"".join([f'<li class="text-sm text-slate-700 flex items-start"><span class="mr-2">👉</span>{step}</li>' for step in r.immediate_next_steps])}
      </ul>
    </section>

    <footer class="mt-12 pt-6 border-t border-slate-200 text-center text-xs text-slate-400">
      Autonomously generated by Infosys AI Startup Idea Validator Multi-Agent System. Session: {r.session_id}
    </footer>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html)


# ===========================================================================
# Static Web UI Mount
# ===========================================================================
web_dir = root_dir / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

    @app.get("/", response_class=FileResponse)
    @app.get("/index.html", response_class=FileResponse)
    def serve_index():
        index_file = web_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return FileResponse(web_dir / "submission_wireframe.html")

    @app.get("/swot_dashboard.html", response_class=FileResponse)
    def serve_swot_dashboard():
        return FileResponse(web_dir / "swot_dashboard.html")

    @app.get("/submission_wireframe.html", response_class=FileResponse)
    def serve_submission_wireframe():
        return FileResponse(web_dir / "submission_wireframe.html")


if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 80)
    print("  AI STARTUP IDEA VALIDATOR — FASTAPI SERVER")
    print("  Serving at: http://127.0.0.1:8000")
    print("=" * 80 + "\n")
    uvicorn.run("src.server:app", host="127.0.0.1", port=8000, reload=True)
