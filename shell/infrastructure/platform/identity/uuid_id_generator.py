from __future__ import annotations

import uuid
from typing import TypeVar

from shell.domain.platform.base.entity_id import EntityId

TId = TypeVar("TId", bound=EntityId)


class UuidIdGenerator:
    def new_id(self, id_type: type[TId]) -> TId:
        return id_type(str(uuid.uuid4()))
