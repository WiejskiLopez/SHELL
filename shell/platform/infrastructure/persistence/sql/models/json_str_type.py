from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from sqlalchemy import TypeDecorator

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB
from shell.platform.types import JsonStr

if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import Dialect


class JsonStrType(TypeDecorator[JsonStr]):
    """SQLAlchemy type mapping ``JsonStr`` to a JSON/JSONB column.

    The domain exposes a concrete ``JsonStr`` (validated JSON string) instead
    of a raw ``dict``. This decorator is the only bridge between the two:
    the JSON object exists transiently here, at the DB adapter boundary.
    """

    impl = JSONB
    cache_ok = True

    def process_bind_param(self, value: JsonStr | str | None, dialect: Dialect) -> Any:
        if value is None:
            return None
        if isinstance(value, JsonStr):
            return json.loads(value.value)
        return json.loads(value)

    def process_result_value(self, value: Any, dialect: Dialect) -> JsonStr | None:
        if value is None:
            return None
        return JsonStr(json.dumps(value))
