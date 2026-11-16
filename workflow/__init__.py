"""LangGraph workflow layer for AI Market Research.

This package is an alternative orchestration path. It reuses the existing
agents and services and does not replace orchestrator.py.
"""

from workflow.state import ResearchState
from workflow.graph import build_graph, run_research_graph

__all__ = ["ResearchState", "build_graph", "run_research_graph"]
