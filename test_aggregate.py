import json
import time
from pathlib import Path

from schemas import Plan, Source, ValidatedEvidence
from agents.aggregate import aggregate

d = Path("data")
validated = [ValidatedEvidence(**v) for v in json.loads((d / "sample_validated.json").read_text(encoding="utf-8"))]
sources = [Source(**s) for s in json.loads((d / "sample_sources.json").read_text(encoding="utf-8"))]
plan = Plan.model_validate_json((d / "sample_plan.json").read_text(encoding="utf-8"))

start = time.time()
ins = aggregate(validated, plan, sources,
                question="Analyze the Indian electric vehicle market and identify key business opportunities for a charging company.",
                job_id="job_real")
print(f"Took {time.time() - start:.1f}s")

print("\nThemes:", [(t["theme"], len(t["evidence_ids"])) for t in ins["themes"]])

print("\nMarket size series (compare 3 rows with their claims):")
for r in ins["market_size_series"]:
    print(f"  {r['year']}  {r['value']:>8} {r['unit']}  {r['kind']:9s} {r['source']}  {r['evidence_ids']}")
print("Other estimates:", ins.get("other_estimates"))

print("\nCompetitor table:")
for c in ins["competitor_table"][:10]:
    print(f"  {c['company']}: {c['figure']} ({c['measure']})")

print("\nCharts:", [(c["title"], c["png_path"]) for c in ins["charts"]])

for key in ("key_findings", "opportunities", "risks"):
    print(f"\n{key}:")
    for it in ins[key]:
        flag = " [NEEDS REVIEW]" if it.get("needs_review") else ""
        print(f"  - {it['text']}{flag}  {it['evidence_ids']}")

print("\nQuality:", json.dumps(ins["quality"]))

accepted = {v.evidence_id for v in validated if v.status == "accepted"}
used = {i for k in ("key_findings", "opportunities", "risks") for it in ins[k] for i in it["evidence_ids"]}
print("\nAll cited ids are accepted records:", used <= accepted)

from agents.aggregate import status_context
print("\nStatus-change evidence the writer saw:")
for r in status_context(validated):
    print(f"  [{r.status}] {r.claim[:110]}")
    
Path("data/sample_insights.json").write_text(json.dumps(ins, indent=2), encoding="utf-8")