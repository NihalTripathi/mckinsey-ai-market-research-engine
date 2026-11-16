import json
from collections import Counter
from pathlib import Path

from services.credibility import assess

sources = json.loads(Path("data/sample_sources.json").read_text(encoding="utf-8"))

tiers = Counter()
unknown = Counter()
for s in sources:
    c = assess(s["url"])
    tiers[c.tier] += 1
    if c.tier == "unknown":
        unknown[c.domain] += 1

print(dict(tiers))
print("\nUnrecognised domains (add the good ones to the lists):")
for domain, n in unknown.most_common(15):
    print(f"  {n:2d}  {domain}")