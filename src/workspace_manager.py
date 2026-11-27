"""
Workspace Manager: Manages persistent storage, retrieval, export,
and the single default layman-friendly startup idea example.
"""

import os
import sys
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.models import (
    WorkspaceSession,
    RawStartupSubmission,
    ValidationDossierReport
)

logger = logging.getLogger("WorkspaceManager")
WORKSPACES_DIR = root_dir / "data" / "workspaces"


def ensure_workspaces_dir() -> Path:
    """Ensures the workspaces directory exists."""
    WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)
    return WORKSPACES_DIR


def save_workspace(session: WorkspaceSession) -> Path:
    """Persists a workspace session to disk as formatted JSON."""
    ensure_workspaces_dir()
    filepath = WORKSPACES_DIR / f"{session.session_id}.json"
    session.updated_at = datetime.utcnow().isoformat() + "Z"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(session.model_dump(), f, indent=2)
    logger.info(f"Saved workspace session: {session.session_id} to {filepath}")
    return filepath


def load_workspace(session_id: str) -> Optional[WorkspaceSession]:
    """Loads a workspace session from disk."""
    filepath = WORKSPACES_DIR / f"{session_id}.json"
    if not filepath.exists():
        logger.warning(f"Workspace session not found: {session_id}")
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return WorkspaceSession.model_validate(data)
    except Exception as e:
        logger.error(f"Error loading workspace {session_id}: {e}")
        return None


def list_workspaces() -> List[Dict[str, Any]]:
    """Returns a list of all saved workspaces with summary metadata."""
    ensure_workspaces_dir()
    summaries = []
    for f in sorted(WORKSPACES_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            with open(f, "r", encoding="utf-8") as file:
                data = json.load(file)
            summaries.append({
                "session_id": data.get("session_id"),
                "created_at": data.get("created_at"),
                "startup_name": data.get("raw_input", {}).get("startup_name") or data.get("report", {}).get("idea_name", "Untitled"),
                "industry": data.get("raw_input", {}).get("industry") or "Technology",
                "feasibility_score": data.get("report", {}).get("feasibility_score") if data.get("report") else None,
                "verdict": data.get("report", {}).get("verdict") if data.get("report") else None,
                "status": data.get("status", "completed")
            })
        except Exception as e:
            logger.warning(f"Failed to read workspace file {f.name}: {e}")
    return summaries


def get_default_presets(include_all: bool = False) -> List[Dict[str, Any]]:
    """
    Provides curated startup idea presets for one-click validation.
    If include_all is False, returns the single default layman-friendly startup idea
    (SmartPantry AI) for backward compatibility and unit tests.
    If include_all is True, returns all diverse industry presets.
    """
    base_preset = {
        "id": "smartpantry",
        "startup_name": "SmartPantry AI",
        "industry": "Consumer Tech & FoodTech",
        "geography": "Global",
        "icon": "fa-carrot",
        "description": "A smart mobile app that tracks grocery expiration dates by snapping a photo of grocery store receipts, alerts users before food spoils, and automatically suggests easy recipes using ingredients already in the fridge to stop food waste and save household money.",
        "target_customers": "Busy working professionals, college students, and budget-conscious families who buy groceries.",
        "monetization_hypothesis": "Freemium mobile subscription ($4.99/month for unlimited receipt scanning, smart meal planner, and automatic grocery list sync).",
        "known_competitors": "SuperCook, CozZo, MyFridgeFood, Paprika"
    }

    if not include_all:
        return [base_preset]

    return [
        base_preset,
        {
            "id": "fleetpulse",
            "startup_name": "FleetPulse EV",
            "industry": "Logistics & CleanTech",
            "geography": "North America & Europe",
            "icon": "fa-truck-bolt",
            "description": "AI-powered dynamic routing, battery state-of-health management, and smart charging scheduling platform designed for commercial delivery fleets transitioning from diesel to electric vehicles. Solves unpredictable battery drain and high peak-electricity charging tariffs.",
            "target_customers": "Fleet operations managers at mid-sized delivery companies (15-250 vans).",
            "monetization_hypothesis": "B2B SaaS subscription ($50/vehicle/month) yielding 25% fleet energy savings.",
            "known_competitors": "Samsara, Geotab, OptimoRoute, Ampcontrol"
        },
        {
            "id": "medscribe",
            "startup_name": "MedScribe AI",
            "industry": "Healthcare & HealthTech",
            "geography": "Global",
            "icon": "fa-heart-pulse",
            "description": "Ambient AI clinical scribe that listens to physician-patient consultations with patient consent, autonomously generates structured SOAP notes, and syncs directly into electronic health record (EHR) systems to eliminate 2+ hours of daily clerical physician burnout.",
            "target_customers": "Outpatient clinics, primary care physicians, and specialty health networks.",
            "monetization_hypothesis": "Tiered clinician seat license ($149/clinician/month) with hospital enterprise volume pricing.",
            "known_competitors": "Abridge, Nuance DAX, Nabla, ScribeLink"
        },
        {
            "id": "edumentor",
            "startup_name": "EduMentor AI",
            "industry": "EdTech & Learning",
            "geography": "Global",
            "icon": "fa-graduation-cap",
            "description": "Personalized multimodal AI tutor for secondary and college STEM students that adapts dynamically to student conceptual misconceptions in real-time, providing step-by-step Socratic guidance rather than just giving away final test answers.",
            "target_customers": "High school & university STEM students, tutoring centers, and parents.",
            "monetization_hypothesis": "Student freemium subscription ($9.99/month for unlimited 24/7 personalized problem breakdowns).",
            "known_competitors": "Photomath, Khanmigo, Chegg, Symbolab"
        },
        {
            "id": "cybersentinel",
            "startup_name": "CyberSentinel",
            "industry": "Cybersecurity & DevOps",
            "geography": "Global",
            "icon": "fa-shield-halved",
            "description": "Autonomous cloud infrastructure security copilot that continuously scans multi-cloud Kubernetes & Terraform environments for zero-day privilege drift and misconfigurations, automatically drafting verified pull requests to patch vulnerabilities before exploitation.",
            "target_customers": "DevSecOps leads, CISOs, and fast-growing mid-market software enterprises.",
            "monetization_hypothesis": "Usage-based cloud seat & node pricing ($300/month base + $15/cloud account).",
            "known_competitors": "Wiz, Orca Security, Snyk, Prisma Cloud"
        }
    ]
