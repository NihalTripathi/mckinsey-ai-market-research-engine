import json
import time
from pathlib import Path

from schemas import Source
from agents.extract import extract_many

sources = [
    Source(**s)
    for s in json.loads(Path("data/sample_sources.json").read_text(encoding="utf-8"))
]

start = time.time()
evidence = extract_many(sources, per_task=3)

print(f"Took {time.time() - start:.1f}s, {len(evidence)} records")
print("excerpt_found True :", sum(e.excerpt_found for e in evidence))
print("claim_supported True:", sum(bool(e.claim_supported) for e in evidence))
print("with a date        :", sum(bool(e.date) for e in evidence))
print("with data_year     :", sum(bool(e.data_year) for e in evidence))

print("\nFirst 5 records:")
for e in evidence[:5]:
    print(f"- [{e.topic}] {e.claim}")
    print(f"  found={e.excerpt_found} supported={e.claim_supported} date={e.date} year={e.data_year}")

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
         
Path("data/sample_evidence.json").write_text(
    json.dumps([e.model_dump() for e in evidence], indent=2), encoding="utf-8"
)