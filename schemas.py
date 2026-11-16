
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ---------- Agent 1: Planner ----------
class Task(BaseModel):
    task_id: str = Field(description="Short unique id, e.g. 't1', 't2'")
    task_name: str
    search_queries: list[str]
    research_questions: list[str] = Field(default_factory=list)
    expected_evidence: Optional[str] = None
    priority: Literal["high", "medium", "low"] = "medium"


class Plan(BaseModel):
    research_objectives: list[str]
    tasks: list[Task]
    industry: Optional[str] = None
    geography: Optional[str] = None
    timeframe: Optional[str] = None
    assumptions: list[str] = Field(default_factory=list)


# ---------- Agent 2: Search ----------
class Source(BaseModel):
    source_id: str
    url: str
    title: str
    pub_date: Optional[str] = None
    task_id: Optional[str] = None
    content: Optional[str] = None

    # All research tasks associated with this source
    task_ids: list[str] = Field(default_factory=list)

    domain: Optional[str] = None
    score: Optional[float] = None


# ---------- Agent 3: Extraction ----------
class Evidence(BaseModel):
    claim: str
    entity: str
    topic: str
    excerpt: str
    source_id: str

    date: Optional[str] = None
    excerpt_found: bool
    evidence_id: Optional[str] = None

    # Original primary task association (backward compatibility)
    task_id: Optional[str] = None

    # NEW: All research tasks associated with this evidence
    task_ids: list[str] = Field(default_factory=list)

    claim_supported: Optional[bool] = None
    date_source: Optional[str] = None
    data_year: Optional[int] = None


# ---------- Agent 4: Validation ----------
class ValidatedEvidence(Evidence):
    status: Literal["accepted", "rejected", "needs_review"]
    reason: str
    confidence: Optional[float] = None
    scores: Optional[dict[str, float]] = None
    duplicate_of: Optional[str] = None
    conflict_with: list[str] = Field(default_factory=list)


# ---------- Agent 5: Report ----------
class ReportSection(BaseModel):
    title: str
    content: str
    citations: list[str] = Field(default_factory=list)
    needs_review: bool = False


class ReportChart(BaseModel):
    title: str
    plotly_json: str
    png_path: Optional[str] = None
    name: str = ""
    section: str = ""
    description: str = ""


class AppendixRow(BaseModel):
    id: str
    evidence_id: Optional[str] = None
    claim: str
    source: str
    source_url: str = ""
    date: str = ""
    confidence: float = 0.0
    status: str


class Report(BaseModel):
    job_id: str
    sections: list[ReportSection]
    charts: list[ReportChart] = Field(default_factory=list)
    evidence_appendix: list[AppendixRow] = Field(default_factory=list)
    pdf_path: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
