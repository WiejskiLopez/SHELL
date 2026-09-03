"""UuidCorrelationIdGenerator — adapter CorrelationIdGenerator przez UUID."""

from __future__ import annotations

import uuid


class UuidCorrelationIdGenerator:
    """Adapter — generuje identyfikator korelacji jako UUID4."""

    def generate(self) -> str:
        return str(uuid.uuid4())
