import json
import re
import time
from pathlib import Path

from schemas import Plan, Source, ValidatedEvidence
from agents.report import CITE, write_report
from services.llm import check_gemini

REUSE_INSIGHTS = False        # True: reuse data/sample_insights.json and skip the slow analysis step

ok, message = check_gemini()          # stop early if the AI service cannot be reached
print(message)
if not ok:
    raise SystemExit(1)

d = Path("data")
validated = [ValidatedEvidence(**v) for v in json.loads((d / "sample_validated.json").read_text(encoding="utf-8"))]
sources = [Source(**s) for s in json.loads((d / "sample_sources.json").read_text(encoding="utf-8"))]
plan = Plan.model_validate_json((d / "sample_plan.json").read_text(encoding="utf-8"))
question = "Analyze the Indian electric vehicle market and identify key business opportunities for a charging company."

insights = None
if REUSE_INSIGHTS and (d / "sample_insights.json").exists():
    insights = json.loads((d / "sample_insights.json").read_text(encoding="utf-8"))

start = time.time()
report = write_report(validated, plan, sources, question, job_id="job_real", insights=insights)
print(f"Took {time.time() - start:.1f}s\n")

for sec in report.sections:
    flag = "  [NEEDS REVIEW]" if sec.needs_review else ""
    print(f"## {sec.title}{flag}")
    print(sec.content)
    print()

print("Warnings:", report.warnings or "none")
print("Charts:", [c.title for c in report.charts])
print("PDF:", report.pdf_path)
print("Appendix rows:", len(report.evidence_appendix))

# Rule checks
appendix_ids = {a.id for a in report.evidence_appendix}
cited = {c for s in report.sections for c in s.citations}
print("\nEvery citation is in the appendix:", cited <= appendix_ids)

uncited = []
for sec in report.sections:
    if sec.title in ("Method and Limitations", "Evidence Requiring Review", "Glossary"):
        continue
    for line in sec.content.split("\n"):
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            if re.search(r"\d", CITE.sub("", sentence)) and not CITE.search(sentence):
                uncited.append(sentence)
print("Sentences with a number but no citation:", len(uncited))
for s in uncited[:5]:
    print("  -", s)

if not cited <= appendix_ids:
    raise AssertionError("A report citation is missing from the evidence appendix.")

if uncited:
    raise AssertionError(
        f"Report contains {len(uncited)} numbered sentence(s) without citations."
    )

Path("data/sample_report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")