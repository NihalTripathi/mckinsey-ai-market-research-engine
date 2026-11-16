
import json
import time
from pathlib import Path

from schemas import Plan, Source, ValidatedEvidence
from agents.aggregate import aggregate, status_context

d = Path("data")

validated = [
    ValidatedEvidence(**v)
    for v in json.loads(
        (d / "ai_validated_combined.json").read_text(encoding="utf-8")
    )
]

sources = [
    Source(**s)
    for s in json.loads(
        (d / "ai_sources.json").read_text(encoding="utf-8")
    )
]

plan = Plan.model_validate_json(
    (d / "ai_plan.json").read_text(encoding="utf-8")
)

question = (
    "Analyze AI adoption in Indian businesses and identify key "
    "business opportunities, industry applications, competition, "
    "and implementation challenges for AI solution providers."
)

print("Validated evidence:", len(validated))
print("Sources:", len(sources))

start = time.time()

ins = aggregate(
    validated,
    plan,
    sources,
    question=question,
    job_id="job_ai_combined"
)

print(f"\nTook {time.time() - start:.1f}s")

print("\nThemes:")
for t in ins["themes"]:
    print(f"  {t['theme']}: {len(t['evidence_ids'])} evidence records")

print("\nMarket size series:")
for r in ins["market_size_series"]:
    print(
        f"  {r['year']}  {r['value']} {r['unit']}  "
        f"{r['kind']}  {r['source']}  {r['evidence_ids']}"
    )

print("\nOther estimates:", ins.get("other_estimates"))

print("\nCompetitor table:")
for c in ins["competitor_table"][:10]:
    print(f"  {c['company']}: {c['figure']} ({c['measure']})")

print("\nCharts:")
for c in ins["charts"]:
    print(f"  {c['title']}: {c['png_path']}")

for key in ("key_findings", "opportunities", "risks"):
    print(f"\n{key}:")
    for item in ins[key]:
        flag = " [NEEDS REVIEW]" if item.get("needs_review") else ""
        print(
            f"  - {item['text']}{flag}  "
            f"{item['evidence_ids']}"
        )

print("\nQuality:", json.dumps(ins["quality"], indent=2))

accepted = {
    v.evidence_id
    for v in validated
    if v.status == "accepted"
}

used = {
    evidence_id
    for key in ("key_findings", "opportunities", "risks")
    for item in ins[key]
    for evidence_id in item["evidence_ids"]
}

print("\nAll cited IDs are accepted records:", used <= accepted)
print("Number of unique cited IDs:", len(used))

print("\nStatus-change evidence:")
for r in status_context(validated):
    print(f"  [{r.status}] {r.claim[:110]}")

output = d / "ai_insights_combined.json"

output.write_text(
    json.dumps(ins, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("\nAI aggregate results saved to:", output)
