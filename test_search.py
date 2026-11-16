import json
import time
from pathlib import Path

from schemas import Plan
from agents.search import find_sources

plan = Plan.model_validate_json(
    Path("data/sample_plan.json").read_text(encoding="utf-8")
)

start = time.time()
sources = find_sources(plan)
print(f"Took {time.time() - start:.1f}s, {len(sources)} sources")
print("With a date:", sum(1 for s in sources if s.pub_date))
print("Found by 2+ tasks:", sum(1 for s in sources if len(s.task_ids) > 1))

for s in sources[:6]:
    print(s.task_ids, s.domain, s.pub_date, s.title[:60])

Path("data/sample_sources.json").write_text(
    json.dumps([s.model_dump() for s in sources], indent=2), encoding="utf-8"
)