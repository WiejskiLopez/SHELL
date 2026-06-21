"""SubGraphDiscovery Protocol — znajduje GraphDefinition ID na podstawie opisu."""

from __future__ import annotations

from typing import Protocol


class SubGraphDiscovery(Protocol):
    """Znajduje GraphDefinition ID najlepiej pasujące do zadanego opisu."""

    async def find_unique(self, query: str) -> str:
        """Zwraca graph_definition_id najlepiej pasującego grafu.

        Args:
            query: naturalny opis czego potrzebujemy (np. "agent zadający pytania")

        Returns:
            graph_definition_id pasującego GraphDefinition

        Raises:
            GraphDefinitionNotFound: gdy nie znaleziono pasującego grafu.
        """
        ...
