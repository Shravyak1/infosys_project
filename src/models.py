"""
Pydantic Data Models for Multi-Agent AI Startup Idea Validator.
Covers all 9 modules and end-to-end pipeline orchestration.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field


# ===========================================================================
# MODULE 1: Startup Idea Submission and Workspace Models
# ===========================================================================

class RawStartupSubmission(BaseModel):
    """Raw input received from user interface submission form."""
    startup_name: Optional[str] = Field(default="My Startup", description="Startup or product name")
    description: str = Field(..., description="Raw description of the startup idea and core problem (2-3 lines or detailed)")
    target_customers: Optional[str] = Field(default="", description="Target audience or user segment")
    industry: Optional[str] = Field(default="", description="Industry or primary market sector")
    geography: Optional[str] = Field(default="Global", description="Geographic focus")
    monetization_hypothesis: Optional[str] = Field(default=None, description="Proposed business model")
    known_competitors: Optional[str] = Field(default=None, description="Competitors recognized by the founder")


class StructuredIdeaOutput(BaseModel):
    """Normalized structured idea profile extracted via LLM."""
    idea_name: Optional[str] = Field(default="Startup Idea", description="Name or title of the startup")
    tagline: Optional[str] = Field(default="", description="One-line elevator pitch")
    problem_statement: str = Field(..., description="Core problem or pain point identified")
    proposed_solution: str = Field(..., description="The proposed product or solution addressing the problem")
    target_customers: str = Field(..., description="Primary user archetype or customer segment")
    industry: str = Field(..., description="Primary industry or business sector")
    key_features: List[str] = Field(default_factory=list, description="List of key capabilities, features, or components")
    monetization_model: Optional[str] = Field(default="B2B SaaS Subscription", description="Revenue model archetype")
    search_keywords: List[str] = Field(default_factory=list, description="Keywords for web retrieval")
    search_queries: List[str] = Field(default_factory=list, description="Targeted queries for Tavily Search Agent")
    extraction_source: str = Field(default="LLM", description="Source: 'LLM_GEMINI', 'LLM_OPENAI', or 'FALLBACK_RULE_BASED'")
    status: str = Field(default="success", description="Status of extraction")


# ===========================================================================
# MODULE 2: Web Search and Data Retrieval Models
# ===========================================================================

class SearchResultItem(BaseModel):
    """Single search result entry from web search."""
    title: str = Field(..., description="Title of the retrieved web page")
    url: str = Field(..., description="URL of the source")
    snippet: str = Field(..., description="Key textual excerpt from the source")
    score: Optional[float] = Field(default=0.85, description="Relevance score (0.0 to 1.0)")
    category: Optional[str] = Field(default="general", description="Category: market, competitor, regulatory, technology")


class WebSearchIntelligence(BaseModel):
    """Synthesized real-time search data returned by Web Search Agent."""
    query: str = Field(..., description="Primary search query executed")
    mode: str = Field(default="LIVE_API", description="LIVE_API or DEMONSTRATION_FALLBACK")
    ai_synthesis: str = Field(..., description="Executive synthesis / direct answer answering the query")
    market_results: List[SearchResultItem] = Field(default_factory=list, description="Industry size and market trends sources")
    competitor_results: List[SearchResultItem] = Field(default_factory=list, description="Competitor intelligence and pricing sources")
    regulatory_results: List[SearchResultItem] = Field(default_factory=list, description="Regulatory and compliance insights")
    retrieved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


# ===========================================================================
# MODULE 3: Market Opportunity & Customer Segmentation Models
# ===========================================================================

class MarketSizeBreakdown(BaseModel):
    """TAM, SAM, SOM market sizing figures and rationales."""
    tam_value: str = Field(..., description="Total Addressable Market figure (e.g., '$14.2 Billion')")
    tam_rationale: str = Field(..., description="Methodology and assumptions behind TAM")
    sam_value: str = Field(..., description="Serviceable Addressable Market figure (e.g., '$3.8 Billion')")
    sam_rationale: str = Field(..., description="Methodology and assumptions behind SAM")
    som_value: str = Field(..., description="Serviceable Obtainable Market figure (e.g., '$180 Million')")
    som_rationale: str = Field(..., description="3-5 year realistic capture assumption")


class CustomerPersonaProfile(BaseModel):
    """Detailed target customer persona."""
    persona_name: str = Field(..., description="Role title (e.g., 'Director of Fleet Operations')")
    archetype: str = Field(..., description="Organization archetype (e.g., 'Mid-sized Regional Delivery')")
    firmographics: str = Field(..., description="Company size, revenue, headcount, or asset scale")
    acute_pain_points: List[str] = Field(..., description="Specific operational headaches and losses")
    budget_authority: str = Field(..., description="Level of discretionary budget authority")
    willingness_to_pay: str = Field(..., description="Estimated budget range or price tolerance")
    urgency_rating: str = Field(..., description="'High (Painkiller)', 'Medium (Efficiency)', or 'Low (Vitamin)'")


class MarketOpportunityReport(BaseModel):
    """Complete output schema for Market Opportunity and Customer Segmentation Agent."""
    industry_vertical: str = Field(..., description="Standardized industry taxonomy")
    market_size: MarketSizeBreakdown = Field(..., description="TAM, SAM, SOM analysis")
    cagr_growth_rate: str = Field(..., description="Annual growth rate with forecast window (e.g., '24.5% (2025-2032)')")
    market_tailwinds: List[str] = Field(..., description="Key macro tailwinds and growth catalysts")
    market_headwinds: List[str] = Field(..., description="Market barriers, friction, or deceleration factors")
    target_customer_segments: List[str] = Field(..., description="Ranked prioritized customer segments")
    personas: List[CustomerPersonaProfile] = Field(..., description="Detailed buyer and user personas")
    market_readiness_score: int = Field(..., ge=1, le=10, description="Readiness score from 1 to 10")
    why_now_rationale: str = Field(..., description="Technological, economic, or regulatory inflection driving timing")
    agent_metadata: Dict[str, Any] = Field(default_factory=dict)


# ===========================================================================
# MODULE 4: Competitor Discovery and Comparison Models
# ===========================================================================

class CompetitorProfile(BaseModel):
    """Detailed competitor profile."""
    name: str = Field(..., description="Competitor company or product name")
    competitor_type: str = Field(..., description="'Direct', 'Indirect', or 'Legacy Substitute'")
    core_offering: str = Field(..., description="Primary product capability")
    pricing_model: str = Field(..., description="Pricing structure (e.g., '$45/vehicle/mo', 'Custom Enterprise')")
    strengths: List[str] = Field(..., description="Key competitive advantages")
    weaknesses_and_gaps: List[str] = Field(..., description="Identified limitations, negative reviews, or blindspots")


class FeatureMatrixRow(BaseModel):
    """Row in feature comparison matrix."""
    dimension_name: str = Field(..., description="Evaluation criteria or capability dimension")
    startup_capability: str = Field(..., description="Startup's rating or capability description")
    competitor_a_capability: str = Field(..., description="Competitor 1 capability")
    competitor_b_capability: str = Field(..., description="Competitor 2 capability")
    competitor_c_capability: str = Field(..., description="Competitor 3 capability")


class CompetitorAnalysisReport(BaseModel):
    """Complete output schema for Competitor Discovery and Comparison Agent."""
    idea_name: str = Field(..., description="Name of startup being benchmarked")
    direct_competitors: List[CompetitorProfile] = Field(..., description="Direct active competitors")
    indirect_competitors: List[CompetitorProfile] = Field(..., description="Adjacent or substitute platforms")
    feature_comparison_matrix: List[FeatureMatrixRow] = Field(..., description="5-dimension comparison matrix")
    uncontested_white_space: str = Field(..., description="Defensible market gap or overlooked segment")
    unique_value_proposition: str = Field(..., description="The startup's primary positioning statement (UVP)")
    defensibility_rating: str = Field(..., description="'High', 'Medium', or 'Low'")
    agent_metadata: Dict[str, Any] = Field(default_factory=dict)


# ===========================================================================
# MODULE 5: SWOT and Risk Analysis Models
# ===========================================================================

class SWOTItem(BaseModel):
    """Discrete factor within a SWOT quadrant."""
    point: str = Field(..., description="Concise header of the SWOT item")
    explanation: str = Field(..., description="In-depth contextual explanation and business reasoning")
    strategic_implication: Optional[str] = Field(default=None, description="Impact on competitive posture or runway")


class SWOTAnalysis(BaseModel):
    """Standardized 2x2 SWOT grid."""
    strengths: List[SWOTItem] = Field(..., description="Internal capabilities and competitive advantages")
    weaknesses: List[SWOTItem] = Field(..., description="Internal liabilities and early-stage deficits")
    opportunities: List[SWOTItem] = Field(..., description="External market dynamics and tailwinds")
    threats: List[SWOTItem] = Field(..., description="External risks, incumbents, and macro headwinds")


class HistoricalPrecedentCase(BaseModel):
    """Real past startup case study retrieved via RAG for risk intelligence."""
    startup_name: str = Field(..., description="Name of the historical startup (e.g. Webvan, Juicero, Fast, Quibi)")
    sector: str = Field(..., description="Industry or market sector")
    outcome: str = Field(..., description="'Failed' or 'Succeeded'")
    outcome_summary: str = Field(..., description="Capital raised, years active, and ultimate fate")
    fatal_mistake_or_key_lesson: str = Field(..., description="The primary mistake that caused failure, or strategic breakthrough")
    warning_for_founder: str = Field(..., description="Actionable warning for the current founder to avoid repeating this history")
    relevance_score: float = Field(default=0.0, description="RAG semantic/similarity match score (0.0 to 1.0)")


class StartupRisk(BaseModel):
    """Granular startup risk profile."""
    risk_id: str = Field(..., description="Identifier (e.g., RISK-01)")
    category: str = Field(..., description="Category: Technical Feasibility, Market & Adoption, Regulatory & Compliance, Financial & Runway, Competitive Defensibility, Operational")
    risk_title: str = Field(..., description="Descriptive title of the risk")
    likelihood: str = Field(..., description="'High', 'Medium', or 'Low'")
    impact: str = Field(..., description="'High', 'Medium', or 'Low'")
    overall_severity: str = Field(default="Medium", description="'Critical', 'High', 'Medium', or 'Low'")
    explanation: str = Field(..., description="Root cause analysis and potential failure mode")
    mitigation_strategy: str = Field(..., description="Actionable, proactive counter-measures and contingency plan")
    historical_precedent: Optional[str] = Field(default=None, description="Real past startup that suffered this exact risk mode (RAG Grounding)")


class SWOTAndRiskReport(BaseModel):
    """Output schema for SWOT & Risk Analysis Agent."""
    idea_name: str = Field(..., description="Startup idea analyzed")
    industry: str = Field(..., description="Primary vertical")
    executive_summary: str = Field(..., description="Synthesis of SWOT posture and risk exposure")
    swot_analysis: SWOTAnalysis = Field(..., description="Structured 4-quadrant SWOT matrix")
    startup_risks: List[StartupRisk] = Field(..., description="Categorized startup risks and mitigations")
    overall_risk_level: str = Field(default="Moderate", description="'Low', 'Moderate', 'High', or 'Critical'")
    key_strategic_recommendation: str = Field(..., description="Primary strategic action the founders must execute first")
    historical_case_studies: List[HistoricalPrecedentCase] = Field(default_factory=list, description="Historical startup post-mortems retrieved via RAG")
    agent_metadata: Dict[str, Any] = Field(default_factory=dict)


# ===========================================================================
# MODULE 6: MVP Feature Recommendation Models
# ===========================================================================

class MVPFeatureItem(BaseModel):
    """Single feature item prioritized under MoSCoW framework."""
    feature_id: str = Field(..., description="Unique ID (e.g., 'FEAT-01')")
    title: str = Field(..., description="Descriptive feature name")
    description: str = Field(..., description="Specification of what this feature does")
    moscow_category: str = Field(..., description="'Must-Have', 'Should-Have', 'Could-Have', or 'Won't-Have (v1.0)'")
    complexity: str = Field(..., description="'Low', 'Medium', or 'High'")
    validation_goal: str = Field(..., description="Core hypothesis tested by this feature")


class TechStackComponent(BaseModel):
    """Component in the recommended tech stack."""
    layer: str = Field(..., description="Layer (e.g., Frontend, Backend, Database, AI/ML Services, Infrastructure)")
    recommended_tech: str = Field(..., description="Specific framework or tool (e.g., 'Next.js 14 / FastAPI')")
    rationale: str = Field(..., description="Why this technology is chosen for the MVP phase")


class SprintMilestone(BaseModel):
    """Sprint in the 8-week MVP roadmap."""
    sprint_name: str = Field(..., description="Sprint label (e.g., 'Weeks 1-2: Core Architecture & Data Ingestion')")
    deliverables: List[str] = Field(..., description="Concrete technical and functional deliverables")
    exit_criteria: str = Field(..., description="Definition of done for this phase")


class ValidationExperiment(BaseModel):
    """Concrete validation experiment to test before full build."""
    experiment_name: str = Field(..., description="Type (e.g., 'Concierge MVP', 'Smoke Test Landing Page', 'Paid Letter of Intent')")
    description: str = Field(..., description="Step-by-step experiment design")
    success_kpi: str = Field(..., description="Target threshold proving validation (e.g., '15% landing page conversion')")


class MVPRecommendationReport(BaseModel):
    """Output schema for MVP Feature Recommendation Agent."""
    idea_name: str = Field(..., description="Name of startup")
    core_value_hypothesis: str = Field(..., description="The primary testable leap-of-faith hypothesis")
    features: List[MVPFeatureItem] = Field(..., description="MoSCoW prioritized feature list")
    tech_stack: List[TechStackComponent] = Field(..., description="Recommended technology stack")
    roadmap_sprints: List[SprintMilestone] = Field(..., description="8-week development sprint schedule")
    validation_experiments: List[ValidationExperiment] = Field(..., description="Pre-build validation experiments")
    estimated_mvp_timeline: str = Field(default="6 to 8 weeks", description="Estimated build time")
    agent_metadata: Dict[str, Any] = Field(default_factory=dict)


# ===========================================================================
# MODULE 7: Go-To-Market (GTM) Strategy Models
# ===========================================================================

class AcquisitionChannel(BaseModel):
    """Customer acquisition channel."""
    channel_name: str = Field(..., description="Channel (e.g., 'Direct Outbound ABM', 'Strategic OEM Partnerships')")
    channel_type: str = Field(..., description="'Inbound', 'Outbound', 'Partnership', or 'Product-Led'")
    strategy_details: str = Field(..., description="Tactical execution playbook for this channel")
    expected_cac: str = Field(..., description="Estimated Customer Acquisition Cost range")
    scalability: str = Field(..., description="'High', 'Medium', or 'Low'")


class PricingTier(BaseModel):
    """Tier in monetization model."""
    tier_name: str = Field(..., description="Tier name (e.g., 'Starter', 'Professional', 'Enterprise')")
    price_point: str = Field(..., description="Price and billing interval (e.g., '$49 / vehicle / month')")
    target_customer_size: str = Field(..., description="Target account profile")
    included_features: List[str] = Field(..., description="Core capabilities included")


class LaunchPhase(BaseModel):
    """Phase in go-to-market rollout."""
    phase_name: str = Field(..., description="Phase label (e.g., 'Phase 1: Private Alpha (3-5 Design Partners)')")
    duration: str = Field(..., description="Timeline (e.g., 'Months 1-3')")
    objectives: List[str] = Field(..., description="Key milestones and objectives")
    target_metric: str = Field(..., description="Target KPI to unlock next phase")


class GTMStrategyReport(BaseModel):
    """Output schema for Go-To-Market Strategy Module."""
    idea_name: str = Field(..., description="Name of startup")
    positioning_headline: str = Field(..., description="Core market positioning hook")
    elevator_pitch: str = Field(..., description="30-second crisp elevator pitch")
    acquisition_channels: List[AcquisitionChannel] = Field(..., description="Ranked distribution channels")
    pricing_model_structure: str = Field(..., description="Monetization model overview")
    pricing_tiers: List[PricingTier] = Field(..., description="Recommended pricing tiers")
    launch_phases: List[LaunchPhase] = Field(..., description="3-phase rollout roadmap")
    sales_cycle_estimate: str = Field(..., description="Estimated sales cycle length (e.g., '30 to 60 days')")
    cac_to_ltv_target: str = Field(..., description="Target unit economic ratio (e.g., 'LTV:CAC > 4:1 with <8 mo payback')")
    agent_metadata: Dict[str, Any] = Field(default_factory=dict)


# ===========================================================================
# MODULE 8: Startup Validation Report Generation Models
# ===========================================================================

class FeasibilityPillarScore(BaseModel):
    """Individual pillar evaluation within Startup Feasibility Index."""
    pillar_name: str = Field(..., description="Pillar: Market Opportunity, Competitive Advantage, Technical Feasibility, Business Viability")
    score: int = Field(..., ge=0, le=100, description="Score 0 to 100")
    weight_percentage: int = Field(..., description="Weight in total score (e.g., 25)")
    rationale: str = Field(..., description="Justification for the assigned score")


class ValidationDossierReport(BaseModel):
    """Comprehensive, executive-ready startup validation report."""
    session_id: str = Field(..., description="Unique validation workspace session ID")
    idea_name: str = Field(..., description="Startup name")
    tagline: str = Field(..., description="One-line positioning tagline")
    verdict: str = Field(..., description="'PROCEED (Green Light)', 'PIVOT (Caution/Yellow)', or 'ABANDON (Red Light)'")
    feasibility_score: int = Field(..., ge=0, le=100, description="Overall Startup Feasibility Index (0-100)")
    pillar_scores: List[FeasibilityPillarScore] = Field(..., description="Detailed pillar breakdown")
    executive_summary: str = Field(..., description="3-paragraph executive synthesis")
    top_strengths: List[str] = Field(..., description="Top 3 internal strengths")
    critical_risks: List[str] = Field(..., description="Top 3 existential risks with immediate mitigation")
    immediate_next_steps: List[str] = Field(..., description="Top 5 concrete 14-day action items for founders")
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    # Nested full agent reports for complete dossier inspection
    structured_idea: StructuredIdeaOutput
    web_intelligence: WebSearchIntelligence
    market_analysis: MarketOpportunityReport
    competitor_analysis: CompetitorAnalysisReport
    swot_and_risk: SWOTAndRiskReport
    mvp_recommendation: MVPRecommendationReport
    gtm_strategy: GTMStrategyReport


# ===========================================================================
# MODULE 9: Conversational Startup Advisor Models
# ===========================================================================

class ChatMessage(BaseModel):
    """Single chat message between founder and Conversational Advisor."""
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message text content")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class AdvisorChatRequest(BaseModel):
    """Request payload for Conversational Advisor."""
    session_id: str = Field(..., description="Validation session to ground conversation on")
    message: str = Field(..., description="Founder's query or instruction")
    history: List[ChatMessage] = Field(default_factory=list, description="Recent conversation history")


class AdvisorChatResponse(BaseModel):
    """Response payload from Conversational Advisor."""
    session_id: str = Field(..., description="Validation session ID")
    response: str = Field(..., description="Advisor's structured, contextual advice")
    suggested_followups: List[str] = Field(default_factory=list, description="3 contextual follow-up prompt chips")
    grounded_in_modules: List[str] = Field(default_factory=list, description="Modules referenced in the answer")


# ===========================================================================
# Full Workspace Session Model
# ===========================================================================

class WorkspaceSession(BaseModel):
    """Persistent storage schema for a complete startup validation session."""
    session_id: str = Field(..., description="Unique UUID")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    raw_input: RawStartupSubmission
    status: str = Field(default="completed", description="'processing', 'completed', or 'failed'")
    report: Optional[ValidationDossierReport] = None
    chat_history: List[ChatMessage] = Field(default_factory=list)
