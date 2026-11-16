
import hashlib
import os
import re
import time

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from dotenv import load_dotenv
from tavily import TavilyClient

from schemas import Plan, Source


load_dotenv(override=True)

api_key = os.getenv("TAVILY_API_KEY")

if not api_key:
    raise RuntimeError("TAVILY_API_KEY is missing from environment.")

client = TavilyClient(api_key=api_key)


MAX_RESULTS_PER_QUERY = 5
SEARCH_DEPTH = "advanced"
MAX_WORKERS = 4
RETRIES = 2


# ---------- Date Handling ----------

_MONTHS = {
    m: i for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun",
         "jul", "aug", "sep", "oct", "nov", "dec"],
        start=1
    )
}

_MONTH = (
    r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)

_LABEL = r"(?:last\s+updated|updated|published|posted|date)"

_TEXT_DATE = re.compile(
    rf"{_LABEL}\s*[:\-]?\s*{_MONTH}\.?\s+(\d{{1,2}}),?\s+(\d{{4}})",
    re.I
)

_ISO_DATE = re.compile(
    rf"{_LABEL}\s*[:\-]?\s*(\d{{4}})-(\d{{2}})-(\d{{2}})",
    re.I
)


def _valid(y: int, m: int, d: int):
    try:
        dt = date(y, m, d)
    except ValueError:
        return None

    if dt.year < 2000 or dt > date.today():
        return None

    return dt.strftime("%Y-%m-%d")


def _to_ymd(raw):
    if not raw:
        return None

    try:
        return datetime.fromisoformat(
            raw.replace("Z", "+00:00")
        ).date().strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        pass

    try:
        return parsedate_to_datetime(raw).date().strftime("%Y-%m-%d")
    except (TypeError, ValueError, AttributeError):
        return None


def _find_date(text):
    if not text:
        return None

    m = _TEXT_DATE.search(text)

    if m:
        return _valid(
            int(m.group(3)),
            _MONTHS[m.group(1)[:3].lower()],
            int(m.group(2))
        )

    m = _ISO_DATE.search(text)

    if m:
        return _valid(
            int(m.group(1)),
            int(m.group(2)),
            int(m.group(3))
        )

    return None


# ---------- URL Handling ----------

def _normalize_url(url: str) -> str:
    """
    Normalize URLs for duplicate detection.
    Preserve the original URL separately for citations.
    """

    parsed = urlparse(url.strip())

    if parsed.scheme.lower() not in ("http", "https"):
        return url.strip()

    query = [
        (k, v)
        for k, v in parse_qsl(parsed.query)
        if not (
            k.lower().startswith("utm_")
            or k.lower() in {
                "fbclid",
                "gclid",
                "ref",
                "source"
            }
        )
    ]

    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        path=parsed.path.rstrip("/") or "/",
        query=urlencode(query),
        fragment=""
    )

    return urlunparse(normalized)


def _source_id(url: str) -> str:
    normalized = _normalize_url(url)

    return "s_" + hashlib.sha1(
        normalized.encode("utf-8")
    ).hexdigest()[:8]


def _domain(url: str) -> str:
    host = urlparse(url).netloc.lower()

    return host[4:] if host.startswith("www.") else host


# ---------- Search Execution ----------

def _search_one(task_id: str, query: str):
    last_error = None

    for attempt in range(RETRIES):
        try:
            resp = client.search(
                query=query,
                max_results=MAX_RESULTS_PER_QUERY,
                search_depth=SEARCH_DEPTH
            )

            return task_id, query, resp.get("results", []), None

        except Exception as e:
            last_error = str(e)

            print(
                f"[search] attempt {attempt + 1} failed "
                f"for {query!r}: {e}"
            )

            if attempt < RETRIES - 1:
                time.sleep(2 * (attempt + 1))

    return task_id, query, [], last_error


# ---------- Main Search Agent ----------

def find_sources(plan: Plan) -> list[Source]:

    jobs = [
        (task.task_id, query)
        for task in plan.tasks
        for query in task.search_queries
    ]

    if not jobs:
        raise ValueError("Research plan contains no search queries.")

    by_url: dict[str, Source] = {}
    failed_queries = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        outcomes = list(
            pool.map(
                lambda job: _search_one(*job),
                jobs
            )
        )

    for task_id, query, results, error in outcomes:

        if error is not None:
            failed_queries.append({
                "task_id": task_id,
                "query": query,
                "error": error
            })

            continue

        for result in results:

            url = result.get("url")

            if not url:
                continue

            normalized_url = _normalize_url(url)

            if not normalized_url:
                continue

            score = result.get("score")
            content = result.get("content")

            if normalized_url in by_url:

                existing = by_url[normalized_url]

                if task_id not in existing.task_ids:
                    existing.task_ids.append(task_id)

                if existing.task_id is None:
                    existing.task_id = task_id

                if (
                    score is not None
                    and (
                        existing.score is None
                        or score > existing.score
                    )
                ):
                    existing.score = score

                # Keep the longer available search content.
                if content and (
                    not existing.content
                    or len(content) > len(existing.content)
                ):
                    existing.content = content

                continue

            source = Source(
                source_id=_source_id(normalized_url),
                url=url,
                title=result.get("title") or url,
                pub_date=(
                    _to_ymd(result.get("published_date"))
                    or _find_date(content)
                ),
                task_id=task_id,
                task_ids=[task_id],
                content=content,
                domain=_domain(url),
                score=score
            )

            by_url[normalized_url] = source

    sources = list(by_url.values())

    print(
        f"[search] {len(jobs)} queries, "
        f"{len(failed_queries)} failed, "
        f"{len(sources)} unique sources"
    )

    if failed_queries:
        print(
            f"[search] failed queries: {len(failed_queries)}"
        )

    if not sources:
        raise RuntimeError(
            "Search returned no sources. "
            "Check TAVILY_API_KEY, network connection "
            "and search query quality."
        )

    return sources
