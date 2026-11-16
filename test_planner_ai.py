
import time
from pathlib import Path
from agents.planner import plan

question = (
    "Analyze AI adoption in Indian businesses and identify key "
    "business opportunities, industry applications, competition, "
    "and implementation challenges for AI solution providers."
)

start = time.time()
result = plan(
    question,
    geography="India",
    timeframe="2025-2030"
)

print(f"Took {time.time() - start:.1f}s")
print(result.model_dump_json(indent=2))

Path("data").mkdir(exist_ok=True)

Path("data/ai_plan.json").write_text(
    result.model_dump_json(indent=2),
    encoding="utf-8"
)

print("\nAI research plan saved to data/ai_plan.json")
