from __future__ import annotations

from shell.platform.domain.exceptions.domain_error import DomainError


class GraphExecutionGraphDefinitionNotFoundError(DomainError):
    def __init__(self, query: str) -> None:
        self.query = query
        super().__init__(f"Graph definition not found for query: {query!r}")
