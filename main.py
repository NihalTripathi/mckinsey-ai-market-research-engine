from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import json

from orchestrator import run_research, model_to_dict

app = FastAPI(title="McKinsey AI Market Research & Strategy Engine")

# Website (Frontend) ko Python backend se connect karne ke liye CORS allow kar rahe hain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchJobRequest(BaseModel):
    question: str
    geography: Optional[str] = None
    timeframe: Optional[str] = None
    industry: Optional[str] = None
    per_task: int = 3


class FeedbackRequest(BaseModel):
    job_id: str
    approved: bool
    comments: Optional[str] = ""


@app.get("/")
def health_check():
    return {"status": "online", "message": "AI Market Research API is running"}


# 1. Naya Research Job Run Karne Ka Endpoint
@app.post("/api/research-jobs")
def create_and_run_job(req: ResearchJobRequest):
    try:
        result = run_research(
            question=req.question,
            geography=req.geography,
            timeframe=req.timeframe,
            industry=req.industry,
            per_task=req.per_task,
        )
        return {
            "job_id": result["job_id"],
            "status": "completed",
            "plan": model_to_dict(result["plan"]),
            "report": model_to_dict(result["report"]),
            "pdf_path": str(result["pdf_path"]) if result["pdf_path"] else None,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# 2. Saare Purane aur Naye Jobs ki List Dekhne Ka Endpoint
@app.get("/api/research-jobs")
def list_jobs():
    jobs_dir = Path("storage") / "jobs"
    if not jobs_dir.exists():
        return {"jobs": []}

    jobs = []
    for summary_file in sorted(jobs_dir.glob("*/run_summary.json"), reverse=True):
        with summary_file.open("r", encoding="utf-8") as f:
            jobs.append(json.load(f))
    return {"jobs": jobs}


# 3. Kisi Specific Job ki Report, Plan aur Evidence Dekhne Ka Endpoint
@app.get("/api/reports/{job_id}")
def get_job_report(job_id: str):
    job_dir = Path("storage") / "jobs" / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="Job ID nahi mila")

    def read_json_if_exists(filename: str):
        path = job_dir / filename
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        return None

    return {
        "job_id": job_id,
        "summary": read_json_if_exists("run_summary.json"),
        "plan": read_json_if_exists("plan.json"),
        "validated_evidence": read_json_if_exists("validated_evidence.json"),
        "report": read_json_if_exists("report.json"),
    }


# 4. Generated PDF Download Karne Ka Endpoint
@app.get("/api/reports/{job_id}/pdf")
def download_pdf(job_id: str):
    pdf_file = Path("storage") / "reports" / f"{job_id}.pdf"
    if not pdf_file.exists():
        raise HTTPException(status_code=404, detail="PDF file nahi mili")
    return FileResponse(path=pdf_file, filename=f"{job_id}_strategy_brief.pdf", media_type="application/pdf")


# 5. Consultant Review / Feedback Save Karne Ka Endpoint
@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest):
    job_dir = Path("storage") / "jobs" / req.job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="Job ID nahi mila")

    feedback_path = job_dir / "feedback.json"
    with feedback_path.open("w", encoding="utf-8") as f:
        json.dump(req.model_dump(), f, indent=2)
    return {"status": "saved", "job_id": req.job_id}