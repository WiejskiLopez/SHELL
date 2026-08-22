from __future__ import annotations

import uuid


class UuidTechnicalIdGenerator:
    def new_id(self) -> str:
        return str(uuid.uuid4())
