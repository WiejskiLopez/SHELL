from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetSessionExecutionByIdQuery:
    session_execution_id: str
