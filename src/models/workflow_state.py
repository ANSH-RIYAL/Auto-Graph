from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class WorkflowFlags(TypedDict, total=False):
    use_llm: bool
    deterministic: bool
    engine: str


class WorkflowState(TypedDict, total=False):
    # Inputs
    codebase_path: Optional[str]
    upload_temp_dir: Optional[str]
    github_url: Optional[str]
    project_name: Optional[str]
    analysis_id: Optional[str]
    session_id: Optional[str]

    # Intermediate
    parsed: Dict[str, Any]
    analyzed: Dict[str, Any]
    graph: Any
    frontend_graph_core: Dict[str, Any]
    viz_graph: Dict[str, Any]

    # Artifacts and exports
    artifacts_paths: Dict[str, str]
    exports_report: Dict[str, Any]

    # Observability
    progress: int
    message: str
    logs: List[str]
    errors: List[str]
    flags: WorkflowFlags


def derive_project_name_from_path(path: Optional[str]) -> str:
    if not path:
        return "project"
    try:
        import os

        return os.path.basename(path.rstrip("/")) or "project"
    except Exception:
        return "project"


