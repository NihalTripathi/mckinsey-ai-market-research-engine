"""Regression tests for competitor classification and the two-source rule."""

from unittest.mock import patch

from agents.aggregate import build_competitors
from schemas import ValidatedEvidence


def _ev(evidence_id, entity, source_id):
    return ValidatedEvidence(
        evidence_id=evidence_id,
        claim=f"{entity} provides AI software.",
        entity=entity,
        topic="competitors",
        excerpt=f"{entity} provides AI software.",
        source_id=source_id,
        excerpt_found=True,
        status="accepted",
        reason="Test evidence",
        confidence=0.8,
        task_id="t1",
    )


def test_classifier_failure_is_reported_without_inventing_competitors():
    evidence = _ev("competitor1", "Example Corp", "source1")
    warnings = []

    with patch(
        "agents.aggregate._classify_competitor_entities",
        side_effect=RuntimeError("offline"),
    ):
        rows, chart = build_competitors(
            [evidence],
            {},
            "test_competitor",
            warnings=warnings,
        )

    assert rows == []
    assert chart is None
    assert any("competitor classification could not be completed" in w.lower() for w in warnings)


def test_company_needs_two_different_source_pages():
    records = [
        _ev("c1", "Alpha Ltd", "s1"),
        _ev("c2", "Alpha Ltd", "s2"),   # two different pages -> kept
        _ev("c3", "Beta Ltd", "s1"),
        _ev("c4", "Beta Ltd", "s1"),    # same page twice -> dropped
    ]

    with patch(
        "agents.aggregate._classify_competitor_entities",
        return_value={"Alpha Ltd": "competitor", "Beta Ltd": "competitor"},
    ):
        rows, chart = build_competitors(records, {}, "test_competitor", warnings=[])

    assert [r["company"] for r in rows] == ["Alpha Ltd"]


if __name__ == "__main__":
    test_classifier_failure_is_reported_without_inventing_competitors()
    test_company_needs_two_different_source_pages()
    print("Competitor classification and two-source tests passed.")