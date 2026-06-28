from __future__ import annotations

import uuid

from typing import TypeVar

TId = TypeVar("TId")


class UuidIdGenerator:
    def new_id(self, id_type: type[TId]) -> TId:
        return id_type(str(uuid.uuid4()))
