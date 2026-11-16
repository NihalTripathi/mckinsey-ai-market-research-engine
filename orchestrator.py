
"""
Main orchestration pipeline for AI Market Research.

Pipeline:
1. Planner
2. Search
3. Extraction
4. Validation
5. Semantic support check
6. Aggregation
7. Report generation
8. PDF generation

Run:
    python orchestrator.py "AI market opportunities in India"

Optional:
    python orchestrator.py "AI market opportunities" --geography India --timeframe "2025-2030" --industry AI
"""

import argparse
import json
import uuid
from datetime import datetime
from pathlib import Path

from agents.planner import plan as create_plan
from agents.search import find_sources
from agents.extract import extract_many
from agents.validate import validate, check_support
from agents.aggregate import aggregate
from agents.report import write_report
from services.pdf import make_pdf


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def log_stage(name: str) -> None:
    print("\n" + "=" * 60)
    print(f"STAGE: {name}")
    print("=" * 60)


def run_stage(name: str, function, *args, **kwargs):
    """Run one stage and report errors with the stage name."""

    log_stage(name)

    try:
        result = function(*args, **kwargs)
        print(f"[orchestrator] {name} completed")
        return result

    except Exception as exc:
        print(
            f"[orchestrator] ERROR in {name}: "
            f"{type(exc).__name__}: {exc}"
        )
        raise RuntimeError(
            f"Research pipeline stopped during: {name}"
        ) from exc


def save_json(path: Path, data) -> None:
    """Save JSON using UTF-8."""

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
            default=str
        )


def model_to_dict(value):
    """Convert a Pydantic model to a JSON-compatible dictionary."""

    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")

    return value


def get_evidence_counts(validated: list) -> dict:
    counts = {
        "accepted": 0,
        "needs_review": 0,
        "rejected": 0
    }

    for item in validated:
        if item.status in counts:
            counts[item.status] += 1

    return counts


# ---------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------

def run_research(
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
    print("AI MARKET RESEARCH PIPELINE")
    print("#" * 60)
    print(f"Job ID: {job_id}")
    print(f"Question: {question}")

    # -----------------------------------------------------
    # 1. Planning
    # -----------------------------------------------------

    research_plan = run_stage(
        "1. Research Planning",
        create_plan,
        query=question,
        geography=geography,
        timeframe=timeframe,
        industry=industry
    )

    if not research_plan.tasks:
        raise RuntimeError(
            "Planner returned a research plan without tasks."
        )

    print(f"Research tasks: {len(research_plan.tasks)}")

    # -----------------------------------------------------
    # 2. Search
    # -----------------------------------------------------

    sources = run_stage(
        "2. Source Discovery",
        find_sources,
        research_plan
    )

    if not sources:
        raise RuntimeError(
            "Search returned no usable sources. "
            "The pipeline cannot continue."
        )

    print(f"Sources discovered: {len(sources)}")

    # -----------------------------------------------------
    # 3. Extraction
    # -----------------------------------------------------

    evidence = run_stage(
        "3. Evidence Extraction",
        extract_many,
        sources,
        per_task=per_task,
        workers=extraction_workers
    )

    if not evidence:
        raise RuntimeError(
            "Extraction returned no evidence. "
            "The pipeline cannot produce a reliable report."
        )

    print(f"Evidence extracted: {len(evidence)}")

    # -----------------------------------------------------
    # 4. Initial validation
    # -----------------------------------------------------

    validated = run_stage(
        "4. Evidence Validation",
        validate,
        evidence,
        sources=sources,
        plan=research_plan,
        llm_check=False
    )

    print(f"Initially validated: {len(validated)}")

    # -----------------------------------------------------
    # 5. Semantic support check
    # -----------------------------------------------------
    # IMPORTANT:
    # validate() is called with llm_check=False above.
    # Therefore this is the one and only support-check call.

    validated = run_stage(
        "5. Semantic Support Verification",
        check_support,
        validated,
        workers=support_workers
    )

    counts = get_evidence_counts(validated)

    print("\nFinal evidence status:")
    print(f"Accepted:     {counts['accepted']}")
    print(f"Needs review: {counts['needs_review']}")
    print(f"Rejected:     {counts['rejected']}")

    # -----------------------------------------------------
    # 6. Aggregation
    # -----------------------------------------------------

    insights = run_stage(
        "6. Research Analysis and Aggregation",
        aggregate,
        validated,
        plan=research_plan,
        sources=sources,
        question=question,
        job_id=job_id
    )

    # -----------------------------------------------------
    # 7. Report generation
    # -----------------------------------------------------

    report = run_stage(
        "7. Research Report Generation",
        write_report,
        validated,
        plan=research_plan,
        sources=sources,
        question=question,
        job_id=job_id,
        insights=insights
    )

    if not report.sections:
        raise RuntimeError(
            "Report generation returned no report sections."
        )

    # -----------------------------------------------------
    # 8. PDF generation
    # -----------------------------------------------------

    pdf_path = run_stage(
        "8. PDF Generation",
        make_pdf,
        report,
        question=question,
        out_dir="storage/reports"
    )

    if pdf_path:
        report = report.model_copy(
            update={"pdf_path": str(pdf_path)}
        )
        print(f"PDF created: {pdf_path}")

    else:
        report = report.model_copy(
            update={
                "warnings": list(report.warnings) + [
                    "PDF generation did not return a file path. "
                    "The report data is available as JSON."
                ]
            }
        )
        print("[orchestrator] WARNING: PDF was not generated.")

    # -----------------------------------------------------
    # 9. Save job artifacts
    # -----------------------------------------------------

    job_dir = Path("storage") / "jobs" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    report_json_path = job_dir / "report.json"
    evidence_json_path = job_dir / "validated_evidence.json"
    plan_json_path = job_dir / "plan.json"
    summary_path = job_dir / "run_summary.json"

    save_json(
        plan_json_path,
        model_to_dict(research_plan)
    )

    save_json(
        evidence_json_path,
        [model_to_dict(item) for item in validated]
    )

    save_json(
        report_json_path,
        model_to_dict(report)
    )

    summary = {
        "job_id": job_id,
        "question": question,
        "created_at": datetime.now().isoformat(),
        "status": "completed",
        "statistics": {
            "tasks": len(research_plan.tasks),
            "sources": len(sources),
            "extracted_evidence": len(evidence),
            "validated_evidence": len(validated),
            **counts
        },
        "outputs": {
            "report_json": str(report_json_path),
            "validated_evidence": str(evidence_json_path),
            "plan_json": str(plan_json_path),
            "pdf": str(pdf_path) if pdf_path else None
        },
        "warnings": list(report.warnings)
    }

    save_json(summary_path, summary)

    # -----------------------------------------------------
    # Final result
    # -----------------------------------------------------

    print("\n" + "#" * 60)
    print("RESEARCH PIPELINE COMPLETED")
    print("#" * 60)

    print(f"Job ID: {job_id}")
    print(f"Sources: {len(sources)}")
    print(f"Evidence: {len(evidence)}")
    print(f"Accepted: {counts['accepted']}")
    print(f"Needs review: {counts['needs_review']}")
    print(f"Rejected: {counts['rejected']}")
    print(f"PDF: {pdf_path or 'Not generated'}")
    print(f"Report JSON: {report_json_path}")
    print(f"Run summary: {summary_path}")

    if report.warnings:
        print("\nWarnings:")
        for warning in report.warnings:
            print(f"- {warning}")

    return {
        "job_id": job_id,
        "plan": research_plan,
        "sources": sources,
        "evidence": evidence,
        "validated": validated,
        "insights": insights,
        "report": report,
        "pdf_path": pdf_path,
        "summary_path": str(summary_path)
    }


# ---------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description="Run the AI Market Research pipeline."
    )

    parser.add_argument(
        "question",
        help="Research question"
    )

    parser.add_argument(
        "--geography",
        default=None,
        help="Research geography, e.g. India"
    )

    parser.add_argument(
        "--timeframe",
        default=None,
        help="Research timeframe, e.g. 2025-2030"
    )

    parser.add_argument(
        "--industry",
        default=None,
        help="Industry, e.g. Artificial Intelligence"
    )

    parser.add_argument(
        "--per-task",
        type=int,
        default=3,
        help="Maximum selected sources per research task"
    )

    parser.add_argument(
        "--extraction-workers",
        type=int,
        default=4
    )

    parser.add_argument(
        "--support-workers",
        type=int,
        default=3
    )

    args = parser.parse_args()

    run_research(
        question=args.question,
        geography=args.geography,
        timeframe=args.timeframe,
        industry=args.industry,
        per_task=args.per_task,
        extraction_workers=args.extraction_workers,
        support_workers=args.support_workers
    )


if __name__ == "__main__":
    main()
