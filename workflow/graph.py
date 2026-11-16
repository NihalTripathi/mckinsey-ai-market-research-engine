"""LangGraph version of the research pipeline.

Each node wraps ONE existing agent/service call, using the same arguments
as orchestrator.py. Nothing about the research logic is rewritten.

Graph:
    START -> planner -> search -> extract -> validate -> support_check
          -> aggregate -> report -> pdf -> persist -> END

Reused from orchestrator.py (so logs, error messages and JSON format match):
    run_stage, save_json, model_to_dict, get_evidence_counts
"""

import uuid
from datetime import datetime
from pathlib import Path

from langgraph.graph import END, START, StateGraph

from agents.planner import plan as create_plan
from agents.search import find_sources
from agents.extract import extract_many
from agents.validate import validate, check_support
from agents.aggregate import aggregate
from agents.report import write_report
from services.pdf import make_pdf

from orchestrator import (
    run_stage,
    save_json,
    model_to_dict,
    get_evidence_counts,
)

from workflow.state import ResearchState


# ---------------------------------------------------------
# Nodes (one per pipeline step)
# ---------------------------------------------------------

def planner_node(state: ResearchState) -> dict:
    research_plan = run_stage(
        "1. Research Planning",
        create_plan,
        query=state["question"],
        geography=state.get("geography"),
        timeframe=state.get("timeframe"),
        industry=state.get("industry"),
    )

    if not research_plan.tasks:
        raise RuntimeError("Planner returned a research plan without tasks.")

    print(f"Research tasks: {len(research_plan.tasks)}")
    return {"plan": research_plan, "stages": ["planner"]}


def search_node(state: ResearchState) -> dict:
    sources = run_stage("2. Source Discovery", find_sources, state["plan"])

    if not sources:
        raise RuntimeError(
            "Search returned no usable sources. The pipeline cannot continue."
        )

    print(f"Sources discovered: {len(sources)}")
    return {"sources": sources, "stages": ["search"]}


def extract_node(state: ResearchState) -> dict:
    evidence = run_stage(
        "3. Evidence Extraction",
        extract_many,
        state["sources"],
        per_task=state["per_task"],
        workers=state["extraction_workers"],
    )

    if not evidence:
        raise RuntimeError(
            "Extraction returned no evidence. "
            "The pipeline cannot produce a reliable report."
        )

    print(f"Evidence extracted: {len(evidence)}")
    return {"evidence": evidence, "stages": ["extract"]}


def validate_node(state: ResearchState) -> dict:
    validated = run_stage(
        "4. Evidence Validation",
        validate,
        state["evidence"],
        sources=state["sources"],
        plan=state["plan"],
        llm_check=False,          # IMPORTANT: semantic check happens once, next node
    )

    print(f"Initially validated: {len(validated)}")
    return {"validated": validated, "stages": ["validate"]}


def support_check_node(state: ResearchState) -> dict:
    # validate() above ran with llm_check=False, so this is the one and
    # only semantic support check.
    validated = run_stage(
        "5. Semantic Support Verification",
        check_support,
        state["validated"],
        workers=state["support_workers"],
    )

    counts = get_evidence_counts(validated)

    print("\nFinal evidence status:")
    print(f"Accepted:     {counts['accepted']}")
    print(f"Needs review: {counts['needs_review']}")
    print(f"Rejected:     {counts['rejected']}")

    return {"validated": validated, "counts": counts, "stages": ["support_check"]}


def aggregate_node(state: ResearchState) -> dict:
    insights = run_stage(
        "6. Research Analysis and Aggregation",
        aggregate,
        state["validated"],
        plan=state["plan"],
        sources=state["sources"],
        question=state["question"],
        job_id=state["job_id"],
    )
    return {"insights": insights, "stages": ["aggregate"]}


def report_node(state: ResearchState) -> dict:
    report = run_stage(
        "7. Research Report Generation",
        write_report,
        state["validated"],
        plan=state["plan"],
        sources=state["sources"],
        question=state["question"],
        job_id=state["job_id"],
        insights=state["insights"],
    )

    if not report.sections:
        raise RuntimeError("Report generation returned no report sections.")

    return {"report": report, "stages": ["report"]}


def pdf_node(state: ResearchState) -> dict:
    report = state["report"]

    pdf_path = run_stage(
        "8. PDF Generation",
        make_pdf,
        report,
        question=state["question"],
        out_dir="storage/reports",
    )

    if pdf_path:
        report = report.model_copy(update={"pdf_path": str(pdf_path)})
        print(f"PDF created: {pdf_path}")
    else:
        # A missing PDF does not invalidate the JSON report.
        report = report.model_copy(
            update={
                "warnings": list(report.warnings) + [
                    "PDF generation did not return a file path. "
                    "The report data is available as JSON."
                ]
            }
        )
        print("[workflow] WARNING: PDF was not generated.")

    return {"report": report, "pdf_path": pdf_path, "stages": ["pdf"]}


def persist_node(state: ResearchState) -> dict:
    """Same files and run_summary.json layout as orchestrator.py step 9."""

    job_id = state["job_id"]
    report = state["report"]
    pdf_path = state.get("pdf_path")
    counts = state["counts"]

    job_dir = Path("storage") / "jobs" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    report_json_path = job_dir / "report.json"
    evidence_json_path = job_dir / "validated_evidence.json"
    plan_json_path = job_dir / "plan.json"
    summary_path = job_dir / "run_summary.json"

    save_json(plan_json_path, model_to_dict(state["plan"]))
    save_json(
        evidence_json_path,
        [model_to_dict(item) for item in state["validated"]],
    )
    save_json(report_json_path, model_to_dict(report))

    summary = {
        "job_id": job_id,
        "question": state["question"],
        "created_at": datetime.now().isoformat(),
        "status": "completed",
        "statistics": {
            "tasks": len(state["plan"].tasks),
            "sources": len(state["sources"]),
            "extracted_evidence": len(state["evidence"]),
            "validated_evidence": len(state["validated"]),
            **counts,
        },
        "outputs": {
            "report_json": str(report_json_path),
            "validated_evidence": str(evidence_json_path),
            "plan_json": str(plan_json_path),
            "pdf": str(pdf_path) if pdf_path else None,
        },
        "warnings": list(report.warnings),
    }

    save_json(summary_path, summary)

    return {"summary_path": str(summary_path), "stages": ["persist"]}


# ---------------------------------------------------------
# Graph
# ---------------------------------------------------------

def build_graph():
    """Build and compile the research graph (no checkpointer / database yet)."""

    builder = StateGraph(ResearchState)

    builder.add_node("planner", planner_node)
    builder.add_node("search", search_node)
    builder.add_node("extract", extract_node)
    builder.add_node("validate", validate_node)
    builder.add_node("support_check", support_check_node)
    builder.add_node("aggregate", aggregate_node)
    builder.add_node("report", report_node)
    builder.add_node("pdf", pdf_node)
    builder.add_node("persist", persist_node)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "search")
    builder.add_edge("search", "extract")
    builder.add_edge("extract", "validate")
    builder.add_edge("validate", "support_check")
    builder.add_edge("support_check", "aggregate")
    builder.add_edge("aggregate", "report")
    builder.add_edge("report", "pdf")
    builder.add_edge("pdf", "persist")
    builder.add_edge("persist", END)

    return builder.compile()


# ---------------------------------------------------------
# Public entry point (same inputs/outputs as orchestrator.run_research)
# ---------------------------------------------------------

def run_research_graph(
    question: str,
    geography: str = None,
    timeframe: str = None,
    industry: str = None,
    per_task: int = 3,
    extraction_workers: int = 4,
    support_workers: int = 3,
) -> dict:

    if not question or not question.strip():
        raise ValueError("Research question cannot be empty.")

    if per_task < 1:
        raise ValueError("per_task must be at least 1.")

    if extraction_workers < 1 or support_workers < 1:
        raise ValueError("Worker counts must be at least 1.")

    job_id = (
        "job_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + "_"
        + uuid.uuid4().hex[:8]
    )

    print("\n" + "#" * 60)
    print("AI MARKET RESEARCH PIPELINE (LangGraph)")
    print("#" * 60)
    print(f"Job ID: {job_id}")
    print(f"Question: {question}")

    graph = build_graph()

    final = graph.invoke(
        {
            "question": question,
            "geography": geography,
            "timeframe": timeframe,
            "industry": industry,
            "per_task": per_task,
            "extraction_workers": extraction_workers,
            "support_workers": support_workers,
            "job_id": job_id,
            "stages": [],
        }
    )

    counts = final["counts"]
    report = final["report"]

    print("\n" + "#" * 60)
    print("RESEARCH PIPELINE COMPLETED")
    print("#" * 60)
    print(f"Job ID: {job_id}")
    print(f"Sources: {len(final['sources'])}")
    print(f"Evidence: {len(final['evidence'])}")
    print(f"Accepted: {counts['accepted']}")
    print(f"Needs review: {counts['needs_review']}")
    print(f"Rejected: {counts['rejected']}")
    print(f"PDF: {final.get('pdf_path') or 'Not generated'}")
    print(f"Run summary: {final['summary_path']}")

    if report.warnings:
        print("\nWarnings:")
        for warning in report.warnings:
            print(f"- {warning}")

    return {
        "job_id": job_id,
        "plan": final["plan"],
        "sources": final["sources"],
        "evidence": final["evidence"],
        "validated": final["validated"],
        "insights": final["insights"],
        "report": report,
        "pdf_path": final.get("pdf_path"),
        "summary_path": final["summary_path"],
        "stages": final["stages"],
    }
