from __future__ import annotations

import os
import uuid
from typing import Any, Dict

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

try:
    from langgraph.checkpoint.sqlite import SqliteSaver  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    SqliteSaver = None  # type: ignore

from ..models.workflow_state import WorkflowState, derive_project_name_from_path
from ..utils.logger import get_logger


logger = get_logger(__name__)


def _append_log(state: WorkflowState, text: str) -> None:
    logs = state.get("logs") or []
    logs.append(text)
    state["logs"] = logs


def node_init_input(state: WorkflowState) -> WorkflowState:
    analysis_id = state.get("analysis_id") or str(uuid.uuid4())
    project = state.get("project_name") or derive_project_name_from_path(
        state.get("codebase_path") or state.get("upload_temp_dir")
    )
    flags = state.get("flags") or {}
    flags.setdefault("deterministic", True)
    flags.setdefault("use_llm", False)
    flags.setdefault("engine", "langgraph")
    out: WorkflowState = {
        "analysis_id": analysis_id,
        "project_name": project,
        "progress": 5,
        "message": "Initialized workflow",
        "flags": flags,
    }
    _append_log(out, "init_input: initialized")
    return out


def node_analyze_codebase(state: WorkflowState) -> WorkflowState:
    # Keep behavior identical to legacy: call CodebaseAnalyzer().analyze_codebase
    from ..analyzer.codebase_analyzer import CodebaseAnalyzer

    codebase_dir = state.get("upload_temp_dir") or state.get("codebase_path") or "."
    analyzer = CodebaseAnalyzer()
    result: Dict[str, Any] = analyzer.analyze_codebase(codebase_dir)
    out: WorkflowState = {
        "analyzed": result,
        "progress": max(20, state.get("progress", 0)),
        "message": "Codebase analyzed",
    }
    _append_log(out, "analyze_codebase: completed")
    return out


def node_convert_to_frontend(state: WorkflowState) -> WorkflowState:
    # Reuse existing conversion for AST-level and export splits
    from ..web.flask_app import convert_analysis_result_to_frontend_format

    analyzed = state.get("analyzed")
    if not analyzed:
        return {"message": "No analysis available", "progress": state.get("progress", 20)}
    frontend = convert_analysis_result_to_frontend_format(analyzed)
    out: WorkflowState = {
        "frontend_graph_core": frontend,
        "progress": max(40, state.get("progress", 0)),
        "message": "Converted to frontend format",
    }
    _append_log(out, "convert_to_frontend: completed")
    return out


def node_build_viz(state: WorkflowState) -> WorkflowState:
    # Reuse existing visualization draft builder for positions/colors/depends_on
    from ..web.flask_app import _build_viz_from_frontend

    frontend = state.get("frontend_graph_core") or {}
    codebase_dir = state.get("upload_temp_dir") or state.get("codebase_path") or ""
    viz = _build_viz_from_frontend(frontend, codebase_dir)
    out: WorkflowState = {
        "viz_graph": viz,
        "progress": max(70, state.get("progress", 0)),
        "message": "Visualization built",
    }
    _append_log(out, "build_viz: completed")
    return out


def node_finalize(state: WorkflowState) -> WorkflowState:
    out: WorkflowState = {
        "progress": 100,
        "message": "Analysis completed successfully",
    }
    _append_log(out, "finalize: completed")
    return out


def create_workflow(project_name: str | None = None, analysis_id: str | None = None, checkpointer_path: str | None = None):
    graph = StateGraph(WorkflowState)

    graph.add_node("init_input", node_init_input)
    graph.add_node("analyze_codebase", node_analyze_codebase)
    graph.add_node("convert_to_frontend", node_convert_to_frontend)
    graph.add_node("build_viz", node_build_viz)
    graph.add_node("finalize", node_finalize)

    graph.set_entry_point("init_input")
    graph.add_edge("init_input", "analyze_codebase")
    graph.add_edge("analyze_codebase", "convert_to_frontend")
    graph.add_edge("convert_to_frontend", "build_viz")
    graph.add_edge("build_viz", "finalize")
    graph.add_edge("finalize", END)

    # Checkpointer selection
    checkpointer = None
    if checkpointer_path and SqliteSaver is not None:
        os.makedirs(os.path.dirname(checkpointer_path), exist_ok=True)
        checkpointer = SqliteSaver(checkpointer_path)
    else:
        checkpointer = MemorySaver()

    app = graph.compile(checkpointer=checkpointer)
    return app


