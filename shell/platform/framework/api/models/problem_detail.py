from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel


class FieldError(BaseModel):
    field: str
    message: str
    code: str | None = None
    value: object | None = None


class ProblemDetail(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str | None = None
    errors: list[FieldError] | None = None
    correlation_id: str | None = None
    timestamp: str

    @staticmethod
    def now_iso() -> str:
        return datetime.now(UTC).isoformat()
