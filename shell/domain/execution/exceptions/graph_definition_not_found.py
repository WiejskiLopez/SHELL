from __future__ import annotations

from shell.domain.platform.exceptions.domain_error import DomainError


class GraphDefinitionNotFound(DomainError):
    def __init__(self, query: str) -> None:
        super().__init__(f"GraphDefinition not found for query: {query!r}")
