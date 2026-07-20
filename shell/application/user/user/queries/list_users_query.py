from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ListUsersQuery:
    page: int = 1
    page_size: int = 100
