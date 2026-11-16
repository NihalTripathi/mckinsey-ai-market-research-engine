
"""Automatic offline checks for Agent 5 (Aggregate).
Run with: python test_aggregate_rules.py
No Gemini API or network required.
"""

from agents.aggregate import (
    select_evidence,
    _cluster_rows,
    status_context,
    _is_competitor_category,
    _clean_figure,
    _Fig,
)
from schemas import ValidatedEvidence


def ev(
    eid,
    claim,
    task_id="t1",
    task_ids=None,
    status="accepted",
    confidence=0.8,
    data_year=None,
):
    return ValidatedEvidence(
        evidence_id=eid,
        claim=claim,
        entity="Test entity",
        topic="market size",
        excerpt=claim,
        source_id="test_source",
        excerpt_found=True,
        task_id=task_id,
        task_ids=task_ids or [],
        status=status,
        reason="Test record",
        confidence=confidence,
        data_year=data_year,
    )


FAILED = []


def check(name, condition):
    result = bool(condition)
    print(("PASS  " if result else "FAIL  ") + name)

    if not result:
        FAILED.append(name)


# ---------------------------------------------------------
# 1. Multi-task evidence selection
# ---------------------------------------------------------

a = ev(
    "a",
    "Evidence about market growth.",
    task_id="t1",
    task_ids=["t2"],
    confidence=0.9,
)

b = ev(
    "b",
    "Evidence about charging infrastructure.",
    task_id="t1",
    confidence=0.8,
)

c = ev(
    "c",
    "Evidence about government policy.",
    task_id="t2",
    confidence=0.7,
)

selected = select_evidence([a, b, c], limit=3)
selected_ids = [r.evidence_id for r in selected]

check(
    "multi-task evidence is associated with both task queues",
    selected_ids == ["a", "c", "b"],
)


# ---------------------------------------------------------
# 2. Same evidence is not selected twice
# ---------------------------------------------------------

selected = select_evidence([a], limit=10)

check(
    "multi-task evidence is selected only once",
    len(selected) == 1 and selected[0].evidence_id == "a",
)


# ---------------------------------------------------------
# 3. Only accepted evidence is selected
# ---------------------------------------------------------

accepted = ev("accepted", "Accepted evidence.")
review = ev(
    "review",
    "Evidence needing review.",
    status="needs_review",
)
rejected = ev(
    "rejected",
    "Rejected evidence.",
    status="rejected",
)

selected = select_evidence([accepted, review, rejected])

check(
    "only accepted evidence is selected",
    [r.evidence_id for r in selected] == ["accepted"],
)


# ---------------------------------------------------------
# 4. Duplicate claims are removed
# ---------------------------------------------------------

first = ev("first", "India EV market reached 5 billion dollars.")
duplicate = ev(
    "second",
    "INDIA EV market reached 5 billion dollars!",
    confidence=0.7,
)

selected = select_evidence([first, duplicate])

check(
    "duplicate normalized claims are removed",
    len(selected) == 1 and selected[0].evidence_id == "first",
)


# ---------------------------------------------------------
# 5. Zero and negative limits return no records
# ---------------------------------------------------------

check(
    "zero limit returns an empty list",
    select_evidence([a, b], limit=0) == [],
)

check(
    "negative limit returns an empty list",
    select_evidence([a, b], limit=-1) == [],
)


# ---------------------------------------------------------
# 6. Evidence selection respects the maximum limit
# ---------------------------------------------------------

records = [
    ev("one", "First independent claim."),
    ev("two", "Second independent claim."),
    ev("three", "Third independent claim."),
]

selected = select_evidence(records, limit=2)

check(
    "selection never exceeds the requested limit",
    len(selected) == 2,
)


# ---------------------------------------------------------
# 7. Same source and year: keep highest confidence
# ---------------------------------------------------------

figures = {
    "figs": [
        {
            "label": "Source A",
            "year": 2025,
            "confidence": 0.7,
            "value": 5.0,
        },
        {
            "label": "Source A",
            "year": 2025,
            "confidence": 0.9,
            "value": 5.2,
        },
    ]
}

rows = _cluster_rows(figures)

check(
    "highest-confidence estimate is kept for source and year",
    len(rows) == 1
    and rows[0]["confidence"] == 0.9
    and rows[0]["value"] == 5.2,
)


# ---------------------------------------------------------
# 8. Different sources with identical figures are preserved
# ---------------------------------------------------------

figures = {
    "figs": [
        {
            "label": "Source A",
            "year": 2025,
            "confidence": 0.9,
            "value": 5.0,
        },
        {
            "label": "Source B",
            "year": 2025,
            "confidence": 0.8,
            "value": 5.0,
        },
    ]
}

rows = _cluster_rows(figures)

check(
    "identical estimates from different sources are preserved",
    len(rows) == 2
    and {r["label"] for r in rows} == {"Source A", "Source B"},
)


# ---------------------------------------------------------
# 9. Different years from the same source are preserved
# ---------------------------------------------------------

figures = {
    "figs": [
        {
            "label": "Source A",
            "year": 2025,
            "confidence": 0.9,
            "value": 5.0,
        },
        {
            "label": "Source A",
            "year": 2026,
            "confidence": 0.8,
            "value": 6.0,
        },
    ]
}

rows = _cluster_rows(figures)

check(
    "different years from the same source are preserved",
    len(rows) == 2
    and {r["year"] for r in rows} == {2025, 2026},
)


# ---------------------------------------------------------
# 10. Status context identifies status-change evidence
# ---------------------------------------------------------

ended = ev(
    "ended",
    "The government scheme was discontinued in 2025.",
    confidence=0.9,
)

ordinary = ev(
    "ordinary",
    "The government announced a new charging policy.",
    confidence=0.95,
)

context = status_context([ordinary, ended])

check(
    "status context identifies discontinued schemes",
    len(context) == 1 and context[0].evidence_id == "ended",
)


# ---------------------------------------------------------
# 11. Accepted status evidence ranks before review evidence
# ---------------------------------------------------------

accepted_status = ev(
    "accepted_status",
    "The previous scheme expired in 2025.",
    status="accepted",
    confidence=0.7,
)

review_status = ev(
    "review_status",
    "The older program was replaced in 2024.",
    status="needs_review",
    confidence=0.99,
)

context = status_context([review_status, accepted_status])

check(
    "accepted status evidence ranks before review evidence",
    len(context) == 2
    and context[0].evidence_id == "accepted_status",
)


# ---------------------------------------------------------
# 12. Status context respects its limit
# ---------------------------------------------------------

records = [
    ev("s1", "The first scheme expired."),
    ev("s2", "The second scheme was discontinued."),
    ev("s3", "The third policy was revoked."),
]

context = status_context(records, limit=2)

check(
    "status context respects its maximum limit",
    len(context) == 2,
)


# ---------------------------------------------------------
# 13. Competitor classification excludes non-competitors
# ---------------------------------------------------------

check(
    "actual competitor category is accepted",
    _is_competitor_category("competitor"),
)

check(
    "competitor category is case-insensitive",
    _is_competitor_category("Competitor"),
)

check(
    "investors are excluded from competitor classification",
    not _is_competitor_category("investor"),
)

check(
    "geographies are excluded from competitor classification",
    not _is_competitor_category("geography"),
)

check(
    "government bodies are excluded from competitor classification",
    not _is_competitor_category("government"),
)

check(
    "survey populations are excluded from competitor classification",
    not _is_competitor_category("survey_population"),
)

check(
    "unknown or missing classifications are excluded",
    not _is_competitor_category("")
    and not _is_competitor_category("unknown"),
)


# ---------------------------------------------------------
# 14. Year-specific monetary figure selection
# ---------------------------------------------------------

record = ev(
    "year_test",
    "The India Artificial Intelligence Market expanded from USD 2,860 million in 2020 to USD 10,200 million in 2025.",
    data_year=2025,
)

figure = _Fig(
    id="year_test",
    measure="India AI market size",
    measure_type="market_size",
    value=2860,
    unit="million",
    currency="USD",
    year=2020,
    kind="actual",
)

cleaned = _clean_figure(record, figure)

check(
    "2025 amount is selected instead of 2020 amount",
    cleaned is not None
    and cleaned["value"] == 10200
    and cleaned["unit"] == "million"
    and cleaned["year"] == 2025,
)

check(
    "2025 market size converts to USD 10.2 billion",
    cleaned is not None
    and abs(cleaned["billions"] - 10.2) < 1e-9,
)


# ---------------------------------------------------------
# Final result
# ---------------------------------------------------------

print("\n" + "=" * 45)

if FAILED:
    print(f"FAILED: {len(FAILED)} check(s)")
    for name in FAILED:
        print(" -", name)
else:
    print("ALL CHECKS PASSED")

print("=" * 45)
