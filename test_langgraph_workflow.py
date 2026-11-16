"""
Offline test for the LangGraph workflow. No API calls, no network.

All agents are replaced with fakes, so this checks only the wiring:
node order, single semantic check, job_id passing, PDF=None handling,
and the saved JSON files.

Run (from the project folder):
    python test_langgraph_workflow.py
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from schemas import (
    Plan, Task, Source, Evidence, ValidatedEvidence, Report, ReportSection,
)
import workflow.graph as g


def fake_plan():
    return Plan(
        research_objectives=["obj"],
        tasks=[Task(task_id="t1", task_name="n", search_queries=["q"])],
    )


def fake_sources():
    return [Source(source_id="s1", url="http://x.test", title="T")]


def fake_evidence():
    return [Evidence(claim="c", entity="e", topic="t", excerpt="x",
                     source_id="s1", excerpt_found=True, evidence_id="e1")]


def fake_validated(evidence):
    return [ValidatedEvidence(**e.model_dump(), status="accepted", reason="ok")
            for e in evidence]


class GraphTest(unittest.TestCase):

    def setUp(self):
        self.calls = []
        self.kwargs = {}
        self._old_cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)          # outputs go to a throwaway storage/

    def tearDown(self):
        os.chdir(self._old_cwd)
        self._tmp.cleanup()

    def _patches(self, pdf_result="storage/reports/x.pdf", empty_plan=False):
        calls, kw = self.calls, self.kwargs

        def f_plan(**k):
            calls.append("plan")
            return Plan(research_objectives=[], tasks=[]) if empty_plan else fake_plan()

        def f_search(plan):
            calls.append("search"); return fake_sources()

        def f_extract(sources, per_task=3, workers=4):
            calls.append("extract"); kw["extract"] = (per_task, workers)
            return fake_evidence()

        def f_validate(evidence, sources=None, plan=None, llm_check=True, **k):
            calls.append("validate"); kw["llm_check"] = llm_check
            return fake_validated(evidence)

        def f_support(validated, workers=3, **k):
            calls.append("check_support"); kw["support_workers"] = workers
            return validated

        def f_aggregate(validated, plan=None, sources=None, question="", job_id=""):
            calls.append("aggregate"); kw["agg_job"] = job_id
            return {"warnings": []}

        def f_report(validated, plan=None, sources=None, question="",
                     job_id="", insights=None):
            calls.append("report"); kw["rep_job"] = job_id
            return Report(job_id=job_id,
                          sections=[ReportSection(title="A", content="b")])

        def f_pdf(report, question="", out_dir=""):
            calls.append("pdf"); return pdf_result

        return [
            patch.object(g, "create_plan", f_plan),
            patch.object(g, "find_sources", f_search),
            patch.object(g, "extract_many", f_extract),
            patch.object(g, "validate", f_validate),
            patch.object(g, "check_support", f_support),
            patch.object(g, "aggregate", f_aggregate),
            patch.object(g, "write_report", f_report),
            patch.object(g, "make_pdf", f_pdf),
        ]

    def _run(self, **opts):
        ps = self._patches(**opts)
        for p in ps: p.start()
        try:
            return g.run_research_graph("test question", per_task=2,
                                        extraction_workers=5, support_workers=6)
        finally:
            for p in ps: p.stop()

    def test_order_and_single_support_check(self):
        out = self._run()
        self.assertEqual(
            self.calls,
            ["plan", "search", "extract", "validate", "check_support",
             "aggregate", "report", "pdf"])
        self.assertEqual(self.calls.count("check_support"), 1)
        self.assertIs(self.kwargs["llm_check"], False)
        self.assertEqual(
            out["stages"],
            ["planner", "search", "extract", "validate", "support_check",
             "aggregate", "report", "pdf", "persist"])

    def test_parameters_and_job_id_passed(self):
        out = self._run()
        self.assertEqual(self.kwargs["extract"], (2, 5))
        self.assertEqual(self.kwargs["support_workers"], 6)
        self.assertEqual(self.kwargs["agg_job"], out["job_id"])
        self.assertEqual(self.kwargs["rep_job"], out["job_id"])
        self.assertTrue(out["job_id"].startswith("job_"))

    def test_saved_files(self):
        out = self._run()
        job_dir = Path("storage") / "jobs" / out["job_id"]
        for name in ("plan.json", "validated_evidence.json",
                     "report.json", "run_summary.json"):
            self.assertTrue((job_dir / name).exists(), name)
        summary = json.loads((job_dir / "run_summary.json").read_text("utf-8"))
        self.assertEqual(summary["status"], "completed")
        self.assertEqual(summary["statistics"]["accepted"], 1)
        self.assertEqual(summary["outputs"]["pdf"], "storage/reports/x.pdf")
        self.assertEqual(out["report"].pdf_path, "storage/reports/x.pdf")

    def test_pdf_none_keeps_json_report(self):
        out = self._run(pdf_result=None)
        self.assertIsNone(out["pdf_path"])
        self.assertTrue(any("PDF generation" in w for w in out["report"].warnings))
        job_dir = Path("storage") / "jobs" / out["job_id"]
        self.assertTrue((job_dir / "report.json").exists())

    def test_empty_plan_stops_with_stage_message(self):
        ps = self._patches(empty_plan=True)
        for p in ps: p.start()
        try:
            with self.assertRaises(RuntimeError):
                g.run_research_graph("test question")
        finally:
            for p in ps: p.stop()
        self.assertEqual(self.calls, ["plan"])

    def test_bad_inputs(self):
        with self.assertRaises(ValueError):
            g.run_research_graph("   ")
        with self.assertRaises(ValueError):
            g.run_research_graph("q", per_task=0)

    def test_graph_builds(self):
        self.assertIsNotNone(g.build_graph())


if __name__ == "__main__":
    unittest.main(verbosity=2)
