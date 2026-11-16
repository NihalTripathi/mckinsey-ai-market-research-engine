"""Automatic checks for Agent 4. Runs offline: no Gemini, no network.
Run with:  python test_validate_rules.py
"""
from datetime import date

import agents.validate as V
from schemas import Evidence, Plan, Source, Task

TODAY = date(2026, 11, 6)
PLAN = Plan(
    research_objectives=["x"], geography="India",
    tasks=[Task(task_id="t1", task_name="Market size", search_queries=["india ev market size"]),
           Task(task_id="t2", task_name="Regulation", search_queries=["policy"])],
)


def src(sid, url, title="t"):
    return Source(source_id=sid, url=url, title=title)


SOURCES = [
    src("news", "https://www.evinfrastructurenews.com/a"),
    src("seller", "https://www.imarcgroup.com/india-ev"),
    src("iea", "https://www.iea.org/reports/x"),
    src("blog", "https://www.scribd.com/document/1"),
    src("old", "https://www.expertmarketresearch.com/r"),
    src("pub", "https://www.imarcengineering.com/insights/x", "IMARC Engineering Insight: charging"),
    src("unk1", "https://example-one.com/report"),      # unrecognised domains: equal credibility,
    src("unk2", "https://example-two.com/report"),      # so the test does not depend on the domain lists
]



def ev(eid, sid, claim, entity="IEA", topic="market size", excerpt=None, found=True, sup=True,
       year=2026, d="2026-09-25", tid="t1", tids=None):
    return Evidence(
        claim=claim,
        entity=entity,
        topic=topic,
        excerpt=excerpt or claim,
        source_id=sid,
        date=d,
        excerpt_found=found,
        claim_supported=sup,
        data_year=year,
        task_id=tid,
        task_ids=tids or [],
        evidence_id=eid
    )


def run(items, llm_check=False):
    return {v.evidence_id: v for v in V.validate(items, SOURCES, PLAN, today=TODAY, llm_check=llm_check)}


FAILED = []


def check(name, condition):
    print(("PASS  " if condition else "FAIL  ") + name)
    if not condition:
        FAILED.append(name)


# 1. a clean record from an official source is accepted
r = run([ev("a", "iea", "IEA reported 29000 public charging stations in 2026.")])
check("clean official record is accepted", r["a"].status == "accepted")

# 2. excerpt not found -> rejected
r = run([ev("a", "news", "IMARC said 5 units.", found=False)])
check("excerpt not found is rejected", r["a"].status == "rejected")

# 3. duplicates: the same figure from two sources, one is kept and corroborated
r = run([ev("a", "news", "IMARC estimated the India EV market size reached $1.45 billion in 2025.",
            entity="IMARC", year=2025),
         ev("b", "seller", "IMARC says the India EV market size reached $1.45 billion in 2025.",
            entity="IMARC", year=2025)])
dups = [v for v in r.values() if v.status == "rejected" and v.duplicate_of]
kept = [v for v in r.values() if v.status != "rejected"]
check("duplicate is rejected and points to the kept record", len(dups) == 1 and dups[0].duplicate_of == kept[0].evidence_id)
check("kept record is corroborated by 2 independent sources", "2 independent" in kept[0].reason or kept[0].scores["corroboration"] == 1.0)

# 4. two report sellers repeating one figure are NOT independent
r = run([ev("a", "seller", "IMARC said the India EV market size reached $2.10 billion in 2025.", entity="IMARC", year=2025),
         ev("b", "seller", "IMARC reports the India EV market size reached $2.10 billion in 2025.", entity="IMARC", year=2025)])
kept = [v for v in r.values() if not v.duplicate_of][0]
check("two sellers do not count as independent confirmation", kept.scores["corroboration"] == 0.5)

# 5. conflict: same measure, same year, figures differ by more than 15%, similar credibility
r = run([ev("a", "unk1", "Firm A reported the India EV market size stood at $5.76 billion in 2026.", entity="Firm A"),
         ev("b", "unk2", "Firm B reported the India EV market size stood at $7.38 billion in 2026.", entity="Firm B")])
check("conflicting figures are flagged for review", r["a"].status == "needs_review" and "conflicts with" in r["a"].reason.lower())

# 6. a conflict with a much weaker source does not downgrade the strong one
r = run([ev("a", "iea", "IEA reported the India EV market size stood at $5.10 billion in 2026.", entity="IEA"),
         ev("b", "blog", "A user said the India EV market size stood at $9.90 billion in 2026.", entity="User")])
check("official record is not downgraded by a user post", r["a"].status == "accepted")
check("user-generated record needs review", r["b"].status == "needs_review")

# 7. different years are not a conflict
r = run([ev("a", "iea", "IEA reported the India EV market size reached $1.45 billion in 2025.", entity="IEA", year=2025),
         ev("b", "iea", "IEA projects the India EV market size will reach $50.51 billion by 2034.", entity="IEA", year=2034)])
check("figures for different years do not conflict", not r["a"].conflict_with and not r["b"].conflict_with)

# 8. old figure with no page date is flagged
r = run([ev("a", "iea", "India had 300 community charging stations.", year=2021, d=None)])
check("old figure year is flagged as stale", r["a"].status == "needs_review" and "years old" in r["a"].reason)

# 9. no date and no year -> age unknown, needs review
r = run([ev("a", "iea", "India will add 5000 chargers soon.", year=None, d=None)])
check("unknown age needs review", r["a"].status == "needs_review" and "age unknown" in r["a"].reason.lower())

# 10. a stale page date (page dated 2023 reports 2025 facts) is not trusted
r = run([ev("a", "old", "India reached 1.56 million units in 2025.", year=2025, d="2023-03-27"),
         ev("b", "old", "India reached 29277 stations by April 2025.", year=2025, d="2023-03-27")])
check("stale page date does not make 2025 figures look old", r["a"].status == "accepted" and r["b"].status == "accepted")

# 11. global figure on a local question
r = run([ev("a", "iea", "The global EV charging market will reach $93.57 billion in 2026.")])
check("global figure for an India question needs review", r["a"].status == "needs_review" and "global" in r["a"].reason.lower())

# 12. entity gap: harmless for geography and publisher, real for a missing number
r = run([ev("a", "iea", "EV two-wheelers grew 65% in August 2026.", entity="India", excerpt="EV two-wheelers grew 65% in August 2026.", sup=False),
         ev("b", "pub", "Public DC fast charging costs INR 15 per kWh.", entity="IMARC Engineering Insight",
            excerpt="Public DC fast charging costs INR 15 per kWh.", sup=False),
         ev("c", "iea", "Break-even is 7 years at 25% utilisation.", entity="IEA",
            excerpt="| Break-Even | 7 years |", sup=False)])
check("geography entity gap is harmless", r["a"].status == "accepted")
check("publisher entity gap is harmless", r["b"].status == "accepted")
check("a missing number is a real problem", r["c"].status == "needs_review")

# 13. empty input, and missing sources and plan
check("empty input returns an empty list", V.validate([], llm_check=False) == [])
out = V.validate([ev("a", "iea", "IEA reported 5 sites in 2026.")], llm_check=False)
check("works without sources and plan", len(out) == 1 and out[0].status in ("accepted", "needs_review"))

# 14. coverage separates weak tasks from unverified tasks
validated = list(run([ev("a", "iea", "IEA reported 100 public charging stations in 2026.", tid="t1"),
                      ev("b", "iea", "IEA reported 200 battery swapping depots in 2026.", tid="t1")]).values())
cov = V.coverage(validated, PLAN)
check("task with no evidence is weak", "t2" in cov["weak_tasks"])
check("task with enough accepted evidence is fine", "t1" not in cov["weak_tasks"] and "t1" not in cov["unverified_tasks"])
more = list(run([ev("c", "blog", "A user said 300 fast chargers exist in 2026.", tid="t2"),
                 ev("d", "blog", "A user said 400 solar canopies exist in 2026.", tid="t2")]).values())
cov = V.coverage(validated + more, PLAN)
check("task with only needs_review evidence is unverified, not weak", "t2" in cov["unverified_tasks"] and "t2" not in cov["weak_tasks"])
# 14B. one evidence record can contribute to multiple tasks

multi_task_evidence = list(run([
    ev(
        "mt1", "iea",
        "IEA reported 100 public charging stations in 2026.",
        tid="t1",
        tids=["t1", "t2"]
    ),
    ev(
        "mt2", "iea",
        "IEA reported 200 battery swapping depots in 2026.",
        tid="t1",
        tids=["t1", "t2"]
    )
]).values())

cov = V.coverage(multi_task_evidence, PLAN)

check(
    "multi-task evidence contributes to both tasks",
    cov["by_task"]["t1"]["accepted"] == 2
    and cov["by_task"]["t2"]["accepted"] == 2
)

check(
    "multi-task evidence prevents false weak-task warnings",
    "t1" not in cov["weak_tasks"]
    and "t2" not in cov["weak_tasks"]
)

# 15. semantic check (Gemini replaced by a stand-in)
class J:
    def __init__(self, verdict, note=""):
        self.verdict, self.note = verdict, note


def fake_judge(batch):
    answers = {}
    for v in batch:
        if v.evidence_id == "p":
            answers[v.evidence_id] = J("partly", "scope differs")
        elif v.evidence_id == "n":
            answers[v.evidence_id] = J("not_supported", "says something else")
        elif v.evidence_id != "m":                       # "m" gets no answer
            answers[v.evidence_id] = J("supported")
    return answers


original = V._judge_batch
V._judge_batch = fake_judge
r = run([ev("s", "iea", "IEA reported 11 public charging stations in 2026."),
         ev("p", "iea", "IEA reported 12 battery swapping depots in 2026."),
         ev("n", "iea", "IEA reported 13 highway charging corridors in 2026."),
         ev("m", "iea", "IEA reported 14 solar charging canopies in 2026.")], llm_check=True)
check("supported stays accepted", r["s"].status == "accepted" and "checked" in r["s"].reason)
check("partly becomes needs_review with a lower confidence", r["p"].status == "needs_review" and r["p"].confidence < V.ACCEPT_MIN)
check("not supported becomes rejected with a lower confidence", r["n"].status == "rejected" and r["n"].confidence < V.REJECT_BELOW)
check("a missing answer stays accepted but says it was not checked", r["m"].status == "accepted" and "not run" in r["m"].reason)


def broken_judge(batch):
    raise RuntimeError("model down")


V._judge_batch = broken_judge
r = run([ev("s", "iea", "IEA reported 11 public charging stations in 2026.")], llm_check=True)
check("a failed support check is visible and does not crash", r["s"].status == "accepted" and "not run" in r["s"].reason)
V._judge_batch = original

print()
print("ALL CHECKS PASSED" if not FAILED else f"{len(FAILED)} CHECK(S) FAILED: {FAILED}")