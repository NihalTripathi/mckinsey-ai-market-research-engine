
import json
import time
from pathlib import Path

from agents.extract import extract
from schemas import Source

sources = json.loads(
    Path("data/ai_sources.json").read_text(encoding="utf-8")
)

target_domains = {
    "ideas.repec.org",
    "expresscomputer.in",
    "cio.economictimes.indiatimes.com",
    "orfonline.org",
    "cms.law",
}

selected = []

for item in sources:
    task_ids = list(item.get("task_ids") or [])

    if item.get("task_id"):
        task_ids.append(item["task_id"])

    if "t4" in task_ids and item.get("domain") in target_domains:
        selected.append(Source.model_validate(item))

print("Additional t4 sources selected:", len(selected))

all_evidence = []
start = time.time()

for source in selected:
    print("\nExtracting:", source.domain)
    print("Title:", source.title)

    try:
        records = extract(source)
        all_evidence.extend(records)
        print("Evidence generated:", len(records))
    except Exception as exc:
        print("Extraction failed:", type(exc).__name__, str(exc))

Path("data/ai_t4_evidence.json").write_text(
    json.dumps(
        [e.model_dump() for e in all_evidence],
        indent=2,
        ensure_ascii=False
    ),
    encoding="utf-8"
)

print("\n--------------------------------")
print("Total additional evidence:", len(all_evidence))
print(f"Time taken: {time.time() - start:.1f}s")
print("Saved to data/ai_t4_evidence.json")

print("\nEvidence date coverage:")
print("With date:", sum(bool(e.date) for e in all_evidence))
print("With data year:", sum(bool(e.data_year) for e in all_evidence))
