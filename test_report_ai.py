
import json
import re
import time
from pathlib import Path

from schemas import Plan, Source, ValidatedEvidence
from agents.report import CITE, write_report
from services.llm import check_gemini


# Reuse the already generated AI insights.
# This avoids running the Aggregate Agent again.
REUSE_INSIGHTS = True

ok, message = check_gemini()
print(message)

if not ok:
    raise SystemExit(1)

d = Path("data")

# Load AI research data without touching EV fixtures.
validated = [
    ValidatedEvidence(**v)
    for v in json.loads(
        (d / "ai_validated_combined.json").read_text(encoding="utf-8")
    )
]

sources = [
    Source(**s)
    for s in json.loads(
        (d / "ai_sources.json").read_text(encoding="utf-8")
    )
]

plan = Plan.model_validate_json(
    (d / "ai_plan.json").read_text(encoding="utf-8")
)

question = (
    "Analyze AI adoption in Indian businesses and identify key business "
    "opportunities, industry applications, competition, and implementation "
    "challenges for AI solution providers."
)

# Load the completed AI aggregation output.
insights = None

if REUSE_INSIGHTS:
    insights_path = d / "ai_insights_combined.json"

    if not insights_path.exists():
        raise FileNotFoundError(
            "AI insights file not found: data/ai_insights_combined.json"
        )

    insights = json.loads(
        insights_path.read_text(encoding="utf-8")
    )


print("\nAI Report input summary:")
print("Validated evidence:", len(validated))
print("Sources:", len(sources))
print("Plan tasks:", len(plan.tasks))
print("Reusing existing AI insights:", insights is not None)


# Generate the AI report using a separate job ID.
start = time.time()

report = write_report(
    validated,
    plan,
    sources,
    question,
    job_id="job_ai_combined_report",
    insights=insights,
)

print(f"\nReport generation took {time.time() - start:.1f}s\n")


# Display generated report sections.
for sec in report.sections:
    flag = "  [NEEDS REVIEW]" if sec.needs_review else ""
    print(f"## {sec.title}{flag}")
    print(sec.content)
    print()


# Display report metadata.
print("Warnings:", report.warnings or "none")
print("Charts:", [c.title for c in report.charts])
print("PDF:", report.pdf_path)
print("Appendix rows:", len(report.evidence_appendix))


# ---------------------------------------------------------
# Citation and numerical rule checks
# ---------------------------------------------------------

appendix_ids = {
    item.id for item in report.evidence_appendix
}

cited = {
    citation
    for section in report.sections
    for citation in section.citations
}

print(
    "\nEvery citation is in the appendix:",
    cited <= appendix_ids,
)

uncited = []

for section in report.sections:
    if section.title in (
        "Method and Limitations",
        "Evidence Requiring Review",
        "Glossary",
    ):
        continue

    for line in section.content.split("\n"):
        sentences = re.split(r"(?<=[.!?])\s+", line)

        for sentence in sentences:
            if (
                re.search(r"\d", CITE.sub("", sentence))
                and not CITE.search(sentence)
            ):
                uncited.append(sentence)

print(
    "Sentences with a number but no citation:",
    len(uncited),
)

for sentence in uncited[:5]:
    print("  -", sentence)

if not cited <= appendix_ids:
    raise AssertionError("A report citation is missing from the evidence appendix.")

if uncited:
    raise AssertionError(
        f"Report contains {len(uncited)} numbered sentence(s) without citations."
    )


# ---------------------------------------------------------
# Save AI report output separately.
# ---------------------------------------------------------

output_path = d / "ai_report.json"

output_path.write_text(
    report.model_dump_json(indent=2),
    encoding="utf-8",
)

print("\nAI report JSON saved to:", output_path)
