from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateEdgeLinkExecutionRequest(BaseModel):
    node_execution_id: str = Field(..., min_length=1)
    edge_execution_id: str = Field(..., min_length=1)

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return super().model_dump(*args, **kwargs)
