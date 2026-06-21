"""SubGraphSecurity — scope and permissions for sub-graph state access."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Protocol


class Scope(StrEnum):
    FULL = "full"
    FILTERED = "filtered"
    ISOLATED = "isolated"


class SubGraphSecurity(Protocol):
    """Określa co sub-graf widzi z parent state."""

    async def resolve_scope(
        self,
        parent_graph_execution_id: str,
        sub_graph_definition_id: str,
    ) -> Scope: ...

    async def filter_state(
        self,
        parent_state: dict[str, Any],
        scope: Scope,
    ) -> dict[str, Any]: ...
