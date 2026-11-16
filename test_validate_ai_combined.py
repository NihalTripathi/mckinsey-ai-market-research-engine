
import json
import re
import time
from collections import Counter
from pathlib import Path

from schemas import Evidence, Plan, Source
from agents.validate import validate, summarize, coverage

d = Path("data")

original = json.loads(
    (d / "ai_evidence.json").read_text(encoding="utf-8")
)

additional = json.loads(
    (d / "ai_t4_evidence.json").read_text(encoding="utf-8")
)

evidence = [
    Evidence.model_validate(e)
    for e in original + additional
]

sources = [
    Source.model_validate(s)
    for s in json.loads(
        (d / "ai_sources.json").read_text(encoding="utf-8")
    )
]

plan = Plan.model_validate_json(
    (d / "ai_plan.json").read_text(encoding="utf-8")
)

print("Original evidence:", len(original))
print("Additional t4 evidence:", len(additional))
print("Combined evidence:", len(evidence))
print("Sources:", len(sources))

start = time.time()
validated = validate(evidence, sources, plan)

print(f"\nValidation took {time.time() - start:.1f}s")

print("\nSTATUS SUMMARY:")
print(summarize(validated))

print("\nTASK COVERAGE:")
print(coverage(validated, plan))

for status in ("needs_review", "rejected"):
    print(f"\nReasons for {status}:")
    reasons = Counter()

    for v in validated:
        if v.status == status:
            for part in v.reason.split("; "):
                reasons[re.sub(r"\d+", "N", part)[:90]] += 1

    for reason, count in reasons.most_common(10):
        print(f"  {count:3d}  {reason}")

checked = [
    v for v in validated
    if "(checked)" in v.reason
]

not_run = [
    v for v in validated
    if "semantic support check not run" in v.reason
]

flagged = [
    v for v in validated
    if v.reason.startswith(
        ("Excerpt only partly", "Excerpt does not support")
    )
]

print(
    f"\nSemantic check: confirmed {len(checked)}, "
    f"flagged {len(flagged)}, not run {len(not_run)}"
)

for v in flagged[:10]:
    print(f"\n- [{v.status}] {v.claim[:120]}")
    print(f"  Excerpt: {v.excerpt[:180]}")
    print(f"  Reason: {v.reason[:180]}")

output = d / "ai_validated_combined.json"

output.write_text(
    json.dumps(
        [v.model_dump() for v in validated],
        indent=2,
        ensure_ascii=False
    ),
    encoding="utf-8"
)

print("\nCombined validated evidence saved to:", output)
