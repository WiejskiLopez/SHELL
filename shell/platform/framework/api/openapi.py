from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI


OPENAPI_TAGS = [
    {"name": "users", "description": "User management — CRUD + status lifecycle"},
    {"name": "sessions", "description": "Session lifecycle — create, list, close, history"},
    {"name": "graph-definitions", "description": "Graph definitions — query by ID or semantic query"},
    {"name": "workflows", "description": "Workflow execution — query workflow status and results"},
    {"name": "node-executions", "description": "Node execution results — query individual node results"},
    {"name": "edge-executions", "description": "Edge execution — manage edges between nodes in a workflow"},
    {"name": "edge-link-executions", "description": "Edge link execution — link nodes to edges"},
    {"name": "projects", "description": "Project management — CRUD for projects"},
    {"name": "health", "description": "Health monitoring — service liveness and version info"},
]


def configure_openapi(app: FastAPI) -> None:
    app.title = "SHELL Control Plane API"
    app.version = "0.1.0"
    app.description = (
        "SHELL — system execution orchestration API. "
        "Manages users, sessions, graph definitions, workflow execution, "
        "and project resources."
    )
    app.openapi_tags = OPENAPI_TAGS
