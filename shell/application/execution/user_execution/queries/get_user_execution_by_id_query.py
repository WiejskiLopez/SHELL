from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetUserExecutionByIdQuery:
    user_execution_id: str
