
import json
import time
from pathlib import Path

from schemas import Source
from agents.extract import extract_many


sources = [
    Source(**s)
    for s in json.loads(
        Path("data/ai_sources.json").read_text(encoding="utf-8")
    )
]

print("AI sources loaded:", len(sources))

start = time.time()
evidence = extract_many(sources, per_task=3)

print(f"\nTook {time.time() - start:.1f}s, {len(evidence)} records")

print("excerpt_found True :", sum(e.excerpt_found for e in evidence))
print("claim_supported True:", sum(bool(e.claim_supported) for e in evidence))
print("with a date        :", sum(bool(e.date) for e in evidence))
print("with data_year     :", sum(bool(e.data_year) for e in evidence))

print("\nFirst 10 records:")
for e in evidence[:10]:
    print(f"- [{e.topic}] {e.claim}")
    print(
        f"  found={e.excerpt_found} "
        f"supported={e.claim_supported} "
        f"date={e.date} "
        f"date_source={e.date_source} "
        f"year={e.data_year}"
    )

print("\nRecords where the excerpt was NOT found:")
for e in evidence:
    if not e.excerpt_found:
        print("- claim  :", e.claim)
        print("  excerpt:", e.excerpt[:150])

print("\nRecords where claim_supported is False:")
for e in evidence:
    if not e.claim_supported:
        print("- claim  :", e.claim)
        print("  entity :", e.entity)
        print("  excerpt:", e.excerpt[:150])

Path("data/ai_evidence.json").write_text(
    json.dumps(
        [e.model_dump() for e in evidence],
        indent=2,
        ensure_ascii=False
    ),
    encoding="utf-8"
)

print("\nAI evidence saved to data/ai_evidence.json")
