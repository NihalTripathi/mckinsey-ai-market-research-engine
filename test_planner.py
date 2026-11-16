import time
from pathlib import Path
from agents.planner import plan

question = "Analyze the Indian electric vehicle market and identify key business opportunities for launching a new EV charging infrastructure company."

start = time.time()
result = plan(question, geography="India", timeframe="2026-2031")
print(f"Took {time.time() - start:.1f}s")

print(result.model_dump_json(indent=2))

Path("data").mkdir(exist_ok=True)
Path("data/sample_plan.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")