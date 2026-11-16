import json
import time
from pathlib import Path

from services.fetch import fetch_page

sources = json.loads(Path("data/sample_sources.json").read_text(encoding="utf-8"))[:8]

ok = 0
for s in sources:
    start = time.time()
    page = fetch_page(s["url"])
    took = time.time() - start
    if page:
        ok += 1
        print(f"OK   {took:4.1f}s {len(page.text):6d} chars  date={page.pub_date}  {s['domain']}")
    else:
        print(f"FAIL {took:4.1f}s  {s['domain']}")

print(f"{ok}/{len(sources)} pages fetched")