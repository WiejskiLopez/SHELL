from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ListSessionsQuery:
    page: int = 1
    page_size: int = 100
    user_id: str | None = None
