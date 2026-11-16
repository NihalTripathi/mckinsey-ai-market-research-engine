"""
Run the AI Market Research pipeline through LangGraph.

This is an alternative to orchestrator.py. Same arguments, same outputs.

Run (from the project folder):
    python langgraph_runner.py "AI market opportunities in India" --geography India --timeframe "2025-2030" --industry "Artificial Intelligence"
"""

import argparse

from workflow.graph import run_research_graph


def main():
    parser = argparse.ArgumentParser(
        description="Run the AI Market Research pipeline with LangGraph."
    )
    parser.add_argument("question", help="Research question")
    parser.add_argument("--geography", default=None, help="e.g. India")
    parser.add_argument("--timeframe", default=None, help="e.g. 2025-2030")
    parser.add_argument("--industry", default=None, help="e.g. Artificial Intelligence")
    parser.add_argument("--per-task", type=int, default=3,
                        help="Maximum selected sources per research task")
    parser.add_argument("--extraction-workers", type=int, default=4)
    parser.add_argument("--support-workers", type=int, default=3)
    args = parser.parse_args()

    run_research_graph(
        question=args.question,
        geography=args.geography,
        timeframe=args.timeframe,
        industry=args.industry,
        per_task=args.per_task,
        extraction_workers=args.extraction_workers,
        support_workers=args.support_workers,
    )


if __name__ == "__main__":
    main()
