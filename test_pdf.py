from services.charts import make_chart
from services.pdf import make_pdf

chart = make_chart(["2025", "2026", "2030"],
                   {"IMARC": [1.45, None, None], "Markets and Markets": [None, 5.76, None],
                    "Expert Market Research": [7.38, None, 25.0]},
                   "Estimates of the India EV market ($ billion)", "Year", "USD billion", "estimates", job_id="job_pdf")

report = {
    "job_id": "job_pdf",
    "sections": [
        {"title": "Executive Summary",
         "content": "AI-generated draft for consultant review. Estimates of the India EV market differ widely [E1] [E2]. "
                    "Public chargers exceed 29,000 [E3].",
         "citations": ["E1", "E2", "E3"], "needs_review": False},
        {"title": "Market Insights",
         "content": "Charging fees range from ₹15–18 per kWh at public DC fast chargers [E4]. “Quoted” text and an em dash — work.\n"
                    "A second paragraph in the same section [E1]. Needs human review.",
         "citations": ["E4", "E1"], "needs_review": True},
    ],
    "charts": [chart],
    "evidence_appendix": [
        {"id": "E1", "claim": "IMARC estimated the India EV market size reached $1.45 billion in 2025.",
         "source": "evinfrastructurenews.com", "source_url": "https://www.evinfrastructurenews.com/emobility/india-ev-market-2026-growth-infrastructure-and-investment-opportunity",
         "date": "2026-09-25", "confidence": 0.84, "status": "accepted"},
        {"id": "E2", "claim": "Markets and Markets reported the India EV market size was $5.76 billion in 2026.",
         "source": "evinfrastructurenews.com", "source_url": "https://www.evinfrastructurenews.com/a", "date": "2026-09-25",
         "confidence": 0.84, "status": "accepted"},
        {"id": "E3", "claim": "India had over 29,000 public EV charging stations.", "source": "iea.org",
         "source_url": "", "date": "", "confidence": 0.86, "status": "accepted"},
        {"id": "E4", "claim": "Public DC fast charging costs ₹15–18 per kWh.", "source": "imarcengineering.com",
         "source_url": "https://www.imarcengineering.com/x", "date": "2026-08-01", "confidence": 0.55, "status": "needs_review"},
    ],
}
print("PDF:", make_pdf(report, "Analyze the Indian EV market and its competitors"))
print("empty report ->", make_pdf({"job_id": "job_empty", "sections": []}))
print("bad input ->", make_pdf(None))