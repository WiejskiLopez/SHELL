from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class GraphDefinitionSemanticQuery(ValueObject):
    text: str
    purpose: str | None = None
    limit: int = 1
    default_graph_definition: str | None = None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "query": self.text,
            "purpose": self.purpose,
            "limit": self.limit,
        }
        if self.default_graph_definition is not None:
            payload["default_graph_definition"] = self.default_graph_definition
        return payload