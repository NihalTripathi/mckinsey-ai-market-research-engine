
from agents.report import build_pool, clean_text, _review_section, _bullets, _repair_report_spacing
from schemas import ValidatedEvidence


FAILED = []


def check(name, condition):
    if condition:
        print(f"PASS  {name}")
    else:
        print(f"FAIL  {name}")
        FAILED.append(name)


def make_evidence(
    evidence_id,
    status="accepted",
    topic="market size",
    confidence=0.9,
    claim=None,
    task_id="t1"
):
    return ValidatedEvidence(
        evidence_id=evidence_id,
        claim=claim or f"Market estimate for company {evidence_id}",
        entity="Test company",
        topic=topic,
        excerpt="Supporting evidence excerpt",
        source_id="source1",
        excerpt_found=True,
        status=status,
        reason="Test reason",
        confidence=confidence,
        task_id=task_id
    )


# --------------------------------------------------
# 1. Evidence pool tests
# --------------------------------------------------

records = [
    make_evidence("e1"),
    make_evidence("e2"),
    make_evidence("e3", status="needs_review"),
    make_evidence("e4", status="rejected"),
]

insights = {
    "key_findings": [
        {"evidence_ids": ["e1", "e3", "e4"]}
    ],
    "opportunities": [],
    "risks": [],
    "market_size_series": [],
    "competitor_table": []
}

pool = build_pool(records, insights)

check(
    "only accepted evidence enters the writing pool",
    all(r.status == "accepted" for r in pool)
)

check(
    "accepted insight evidence is included",
    "e1" in [r.evidence_id for r in pool]
)

check(
    "needs-review evidence is excluded",
    "e3" not in [r.evidence_id for r in pool]
)

check(
    "rejected evidence is excluded",
    "e4" not in [r.evidence_id for r in pool]
)


# --------------------------------------------------
# 2. Evidence pool limit tests
# --------------------------------------------------

many_records = [
    make_evidence(f"many_{i}", confidence=0.9)
    for i in range(60)
]

many_insights = {
    "key_findings": [
        {"evidence_ids": [f"many_{i}" for i in range(60)]}
    ],
    "opportunities": [],
    "risks": [],
    "market_size_series": [],
    "competitor_table": []
}

limited_pool = build_pool(many_records, many_insights, limit=10)

check(
    "pool never exceeds requested limit",
    len(limited_pool) <= 10
)

check(
    "pool fills available limit",
    len(limited_pool) == 10
)

check(
    "zero limit returns empty pool",
    build_pool(records, insights, limit=0) == []
)

check(
    "negative limit returns empty pool",
    build_pool(records, insights, limit=-5) == []
)


# --------------------------------------------------
# 3. Duplicate evidence tests
# --------------------------------------------------

duplicate_insights = {
    "key_findings": [
        {"evidence_ids": ["e1", "e1", "e2"]}
    ],
    "opportunities": [],
    "risks": [],
    "market_size_series": [],
    "competitor_table": []
}

duplicate_pool = build_pool(records, duplicate_insights)

duplicate_ids = [r.evidence_id for r in duplicate_pool]

check(
    "duplicate evidence IDs are included only once",
    len(duplicate_ids) == len(set(duplicate_ids))
)


# --------------------------------------------------
# 4. Sentence citation tests
# --------------------------------------------------

accepted = make_evidence(
    "e10",
    claim="The market was valued at $100 million in 2025."
)

review = make_evidence(
    "e11",
    status="needs_review",
    claim="The market was valued at $200 million in 2025."
)

alias = {
    "E1": accepted,
    "E2": review
}

valid_sentence = clean_text(
    "The market was valued at $100 million in 2025 [E1].",
    alias
)

check(
    "supported numbered sentence is retained",
    bool(valid_sentence)
)

unsupported_sentence = clean_text(
    "The market was valued at $500 million in 2025 [E1].",
    alias
)

check(
    "unsupported number is rejected",
    not unsupported_sentence
)

missing_citation = clean_text(
    "The market was valued at $100 million in 2025.",
    alias
)

check(
    "numbered sentence without citation is rejected",
    not missing_citation
)


# --------------------------------------------------
# 5. Review section tests
# --------------------------------------------------

review_records = [
    make_evidence(
        "review1",
        status="needs_review",
        claim="A proposed policy may support the market."
    )
]

review_alias = {}
review_by_id = {}

review_text, review_ids = _review_section(
    review_records,
    None,
    review_alias,
    review_by_id,
    {}
)

check(
    "review section includes unconfirmed evidence",
    review_text is not None and "review1" in review_ids
)

check(
    "review evidence receives a citation alias",
    "review1" in review_alias
)




# --------------------------------------------------
# 6. Opportunity and risk evidence checks
# --------------------------------------------------

policy = make_evidence(
    "policy1",
    topic="policy",
    claim="India has AI-specific obligations effective from 20 February 2026."
)
policy_alias = {"E1": policy}

policy_bullet = _bullets(
    [{
        "text": "India has AI-specific obligations effective from 20 February 2026.",
        "evidence_ids": ["policy1"],
        "verify_status": True,
    }],
    policy_alias,
)

check(
    "policy findings are retained with a verification reminder",
    "verify the current status" in policy_bullet.lower()
    and "[E1]" in policy_bullet
)

stale_bullet = _bullets(
    [{
        "text": "A market was valued at $500 million in 2025.",
        "evidence_ids": ["missing_evidence"],
    }],
    policy_alias,
)

check(
    "findings with stale evidence IDs are excluded",
    stale_bullet == ""
)

unsupported_bullet = _bullets(
    [{
        "text": "A market was valued at $500 million in 2025.",
        "evidence_ids": ["policy1"],
    }],
    policy_alias,
)

check(
    "unsupported numbers in findings are excluded",
    unsupported_bullet == ""
)


# --------------------------------------------------
# 7. Report spacing repair
# --------------------------------------------------

spacing = _repair_report_spacing(
    "Startup activity,investment figures increased in2025and 2026."
)

check(
    "missing spaces after commas and years are repaired",
    "activity, investment" in spacing
    and "in 2025 and 2026" in spacing
)

# --------------------------------------------------
# Final result
# --------------------------------------------------

print("\n=============================================")

if FAILED:
    print(f"{len(FAILED)} CHECK(S) FAILED:")
    for item in FAILED:
        print(" -", item)
else:
    print("ALL CHECKS PASSED")

print("=============================================")

if FAILED:
    raise SystemExit(1)
