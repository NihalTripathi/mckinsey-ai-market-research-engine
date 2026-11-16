"""Shared state passed between LangGraph nodes.

Each node reads what it needs from this dictionary and returns only the
keys it wants to add or change. LangGraph merges those updates for us.

Values such as plan, sources, evidence and report are the existing
Pydantic objects from schemas.py. They are stored as-is (type Any) so the
existing schemas stay untouched.
"""

import operator
from typing import Annotated, Any, Optional, TypedDict


class ResearchState(TypedDict, total=False):
    # ---- inputs (set once, before the graph starts) ----
    question: str
    geography: Optional[str]
    timeframe: Optional[str]
    industry: Optional[str]
    per_task: int
    extraction_workers: int
    support_workers: int
    job_id: str

    # ---- produced by the nodes ----
    plan: Any                  # schemas.Plan
    sources: list              # list[schemas.Source]
    evidence: list             # list[schemas.Evidence]
    validated: list            # list[schemas.ValidatedEvidence]
    counts: dict               # {"accepted": n, "needs_review": n, "rejected": n}
    insights: dict
    report: Any                # schemas.Report
    pdf_path: Optional[str]
    summary_path: str

    # Names of the nodes that have finished, in order. The operator.add
    # reducer makes each node's list get appended instead of replaced.
    stages: Annotated[list[str], operator.add]
