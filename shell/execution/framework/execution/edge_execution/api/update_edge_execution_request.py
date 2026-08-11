from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class UpdateEdgeExecutionRequest(BaseModel):
    target_node_execution_id: str | None = None

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return super().model_dump(*args, **kwargs)
