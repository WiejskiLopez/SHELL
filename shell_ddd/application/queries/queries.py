"""Application queries."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetTaskByNameQuery:
    name: str


@dataclass(frozen=True, slots=True)
class GetCurrentTaskQuery:
    name: str


@dataclass(frozen=True, slots=True)
class GetWorkflowQuery:
    workflow_id: str


@dataclass(frozen=True, slots=True)
class GetEnvelopesByWorkflowQuery:
    workflow_id: str
    pending_only: bool = False


@dataclass(frozen=True, slots=True)
class GetNodeResultQuery:
    node_id: str
    workflow_id: str


@dataclass(frozen=True, slots=True)
class GetPromptQuery:
    name: str


@dataclass(frozen=True, slots=True)
class GetRunnerConfigQuery:
    package_name: str


@dataclass(frozen=True, slots=True)
class SearchSimilarQuery:
    query_text: str
    top_k: int = 5
    domain: str | None = None


@dataclass(frozen=True, slots=True)
class GetSessionHistoryQuery:
    session_id: str
