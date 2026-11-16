import os
import time
from datetime import date
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

from schemas import Plan

load_dotenv(override=True)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELS = [
    os.getenv("GEMINI_MODEL"),
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
]
MODELS = [m for i, m in enumerate(MODELS) if m and m not in MODELS[:i]]


def _check_plan(p: Plan) -> None:
    if not p.research_objectives or not p.tasks:
        raise ValueError("plan has no objectives or tasks")
    ids = [t.task_id for t in p.tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate task_id values")
    for t in p.tasks:
        if not t.search_queries:
            raise ValueError(f"task {t.task_id} has no search queries")


def plan(
    query: str,
    geography: Optional[str] = None,
    timeframe: Optional[str] = None,
    industry: Optional[str] = None,
) -> Plan:
    context = []
    if industry:
        context.append(f"- Industry: {industry}")
    if geography:
        context.append(f"- Geography: {geography}")
    if timeframe:
        context.append(f"- Timeframe: {timeframe}")
    context_text = "\n".join(context) if context else "- none given"

    prompt = f"""
You are the Planner Agent of an AI Market Research and Strategy Engine.
Today's date is {date.today().isoformat()}. Prefer the most recent data
and do not use outdated years in search queries.

Analyze the research question and create:
1. Research objectives (2-5)
2. Research tasks (4-6), each with a unique task_id like "t1", "t2".
   Cover the main angles that fit the question, such as market size,
   regulation, competition, business model and unit economics,
   technology or infrastructure, and risks.
3. For each task:
   - 3-4 specific web search queries
   - 3 research questions the task must answer
   - expected_evidence: name the kind of source that would answer it
     (e.g. industry reports, regulatory documents, company filings)
   - priority: high, medium or low
4. industry, geography and timeframe. Use the given context if present,
   otherwise take them from the question. If no timeframe is given, use
   a forward-looking window of about 5 years from today's date.
5. assumptions: list anything the question did not specify and you had to assume.

Make sure every research objective is covered by at least one task.

Important: your knowledge may be out of date. In search queries, do not name
specific government schemes, laws, companies, products or statistics unless
they appear in the research question or the context below. Describe them
generically instead (for example "central government EV charging subsidy
scheme" or "leading charge point operators"), so the search finds the
current names.

Do not perform any searches or answer the question yourself.

Given context:
{context_text}

Research Question:
{query}
"""

    last_error = None
    for model in MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=Plan,
                    ),
                )
                result = Plan.model_validate_json(response.text)
                _check_plan(result)
                print(f"[planner] used model: {model}")
                return result
            except errors.ServerError as e:
                last_error = e
                time.sleep(2 * (attempt + 1))
            except errors.ClientError as e:
                last_error = e
                break
            except (ValueError, TypeError) as e:
                last_error = e

    raise last_error