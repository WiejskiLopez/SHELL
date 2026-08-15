from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateEdgeExecutionRequest(BaseModel):
    edge_definition_id: str = Field(..., min_length=1)
    source_node_execution_id: str = Field(..., min_length=1)
    target_node_execution_id: str | None = None

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return super().model_dump(*args, **kwargs)
