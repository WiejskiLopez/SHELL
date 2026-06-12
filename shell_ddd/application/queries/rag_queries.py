from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SearchSimilarQuery:
    query_text: str
    top_k: int = 5
    domain: str | None = None
