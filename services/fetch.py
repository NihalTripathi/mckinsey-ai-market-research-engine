import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

import requests
import trafilatura

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MarketResearchBot/1.0)"}
TIMEOUT = (5, 15)        # seconds to connect, seconds to read
MAX_BYTES = 3_000_000    # skip huge pages
MIN_CHARS = 200          # shorter than this is usually a block page or cookie wall


@dataclass
class FetchedPage:
    text: str
    pub_date: Optional[str] = None   # YYYY-MM-DD, None if the page doesn't say


def _clean_date(raw) -> Optional[str]:
    """Accept only a real date between 2000 and today, as YYYY-MM-DD."""
    if not raw:
        return None
    try:
        d = date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None
    if d.year < 2000 or d >= date.today():
        return None
    if d.month == 1 and d.day == 1:      # usually a placeholder, not a real publish date
        return None
    return d.isoformat()


def fetch_page(url: str) -> Optional[FetchedPage]:
    """Download a page and return its article text and publish date,
    or None if the page can't be read."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[fetch] failed {url}: {type(e).__name__}")
        return None

    if "html" not in resp.headers.get("Content-Type", "").lower():
        return None                      # PDFs and other non-HTML files
    if len(resp.content) > MAX_BYTES:
        return None

    html = resp.content                  # bytes, so trafilatura detects the encoding
    text = trafilatura.extract(html, include_comments=False, include_tables=True)
    if not text:
        return None
    text = re.sub(r"\[\d+\]", "", text).strip()   # drop citation marks like [1]
    if len(text) < MIN_CHARS:
        return None

    pub_date = None
    try:
        meta = trafilatura.extract_metadata(html)
        if meta is not None:
            pub_date = _clean_date(meta.date)
    except Exception:
        pass

    return FetchedPage(text=text, pub_date=pub_date)