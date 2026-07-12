from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ListWorkflowsQuery:
    page: int = 1
    page_size: int = 100
    status: str | None = None
