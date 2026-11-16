"""Offline regression tests for report snapshot consistency and policy findings."""

from unittest.mock import patch

from schemas import Plan, Source, ValidatedEvidence
from agents.report import write_report


def test_report_recalculates_quality_and_keeps_verified_policy_findings():
    evidence = ValidatedEvidence(
        evidence_id="policy1",
        claim="India has AI-specific obligations effective from 20 February 2026.",
        entity="India",
        topic="policy",
        excerpt="India has AI-specific obligations effective from 20 February 2026.",
        source_id="source1",
        date="2026-07-21",
        data_year=2026,
        excerpt_found=True,
        claim_supported=True,
        status="accepted",
        reason="Passes all checks; excerpt supports the claim",
        confidence=0.78,
        task_id="t1",
        task_ids=["t1"],
    )
    plan = Plan(
        research_objectives=["Test policy coverage"],
        tasks=[{
            "task_id": "t1",
            "task_name": "Policy",
            "search_queries": ["AI policy"],
            "priority": "high",
        }],
        industry="Artificial Intelligence / Enterprise Software",
        geography="India",
        timeframe="2025-2030",
    )
    source = Source(
        source_id="source1",
        url="https://cms.law/example",
        title="CMS",
    )
    stale_insights = {
        "quality": {
            "counts": {"accepted": 0, "needs_review": 1, "rejected": 0},
            "accepted_by_source_tier": {"report_seller": 1},
        },
        "warnings": [],
        "key_findings": [],
        "market_size_series": [],
        "competitor_table": [],
        "opportunities": [{
            "text": "India has AI-specific obligations effective from 20 February 2026.",
            "evidence_ids": ["policy1"],
            "verify_status": True,
        }],
        "risks": [],
        "findings_unavailable": False,
        "market_size_comparable": True,
    }

    with (
        patch("agents.report._llm_sections", return_value=None),
        patch("agents.report._glossary_section", return_value=None),
        patch("agents.report.make_pdf", return_value=None),
    ):
        report = write_report(
            [evidence],
            plan,
            [source],
            "Test policy",
            job_id="test_snapshot",
            insights=stale_insights,
        )

    method = next(s.content for s in report.sections if s.title == "Method and Limitations")
    competitors = next(s.content for s in report.sections if s.title == "Competitor Analysis")
    opportunities = next(s.content for s in report.sections if s.title == "Opportunities and Risks")

    assert "1 accepted, 0 need review and 0 rejected" in method
    assert any("different evidence snapshot" in w for w in report.warnings)
    assert "verify the current status" in opportunities.lower()
    assert "[E1]" in opportunities
    assert "AI solution providers" not in competitors
    assert "Artificial Intelligence / Enterprise Software market" in competitors
    assert {c for s in report.sections for c in s.citations} <= {
        a.id for a in report.evidence_appendix
    }


if __name__ == "__main__":
    test_report_recalculates_quality_and_keeps_verified_policy_findings()
    print("Report snapshot regression test passed.")
