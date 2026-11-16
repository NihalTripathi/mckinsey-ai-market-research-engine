import json
import re
import time
from collections import Counter
from pathlib import Path

from schemas import Evidence, Plan, Source
from agents.validate import validate, summarize, coverage

d = Path("data")
evidence = [Evidence(**e) for e in json.loads((d / "sample_evidence.json").read_text(encoding="utf-8"))]
sources = [Source(**s) for s in json.loads((d / "sample_sources.json").read_text(encoding="utf-8"))]
plan = Plan.model_validate_json((d / "sample_plan.json").read_text(encoding="utf-8"))

start = time.time()
validated = validate(evidence, sources, plan)
print(f"Took {time.time() - start:.1f}s")

print(len(validated), "records:", summarize(validated))
print("Coverage:", coverage(validated, plan))

for status in ("needs_review", "rejected"):
    print(f"\nWhy records were {status}:")
    reasons = Counter()
    for v in validated:
        if v.status == status:
            for part in v.reason.split("; "):
                reasons[re.sub(r"\d+", "N", part)[:90]] += 1
    for reason, n in reasons.most_common(8):
        print(f"  {n:3d}  {reason}")

checked = [v for v in validated if "(checked)" in v.reason]
not_run = [v for v in validated if "semantic support check not run" in v.reason]
flagged = [v for v in validated if v.reason.startswith(("Excerpt only partly", "Excerpt does not support"))]
print(f"\nSemantic check: confirmed {len(checked)}, flagged {len(flagged)}, not run {len(not_run)}")
for v in flagged[:10]:
    print(f"- [{v.status}] {v.claim[:100]}")
    print(f"    excerpt: {v.excerpt[:140]}")
    print(f"    {v.reason[:160]}")

print("\nThe 6.4% record:")
for v in validated:
    if "6.4%" in v.claim:
        print(f"- [{v.status}] {v.claim}")
        print(f"    {v.reason[:200]}")

(d / "sample_validated.json").write_text(
    json.dumps([v.model_dump() for v in validated], indent=2), encoding="utf-8"
)