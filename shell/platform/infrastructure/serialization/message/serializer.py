from __future__ import annotations

import dataclasses
import logging
from datetime import datetime
from typing import Any, cast, get_type_hints

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.schema_version import SchemaVersion

logger = logging.getLogger(__name__)


class DomainMessageSerializer:
    def to_payload(self, message: object) -> dict[str, object]:
        payload: dict[str, object] = {}
        for f in dataclasses.fields(message):  # type: ignore[arg-type]
            if f.name in ("occurred_at", "schema_version"):
                continue
            payload[f.name] = self._serialize_value(getattr(message, f.name))
        return payload

    def to_outbox_payload(self, message: object) -> dict[str, object]:
        raw_occurred_at = message.occurred_at  # type: ignore[attr-defined]
        if hasattr(raw_occurred_at, "value"):
            raw_occurred_at = raw_occurred_at.value
        return {
            "id": None,
            "message_type": type(message).__name__,
            "occurred_at": raw_occurred_at,
            "payload": self.to_payload(message),
        }

    def from_payload(
        self,
        message_cls: type,
        occurred_at: datetime,
        payload: dict[str, object],
        schema_version: int = 1,
    ) -> object:
        kwargs: dict[str, Any] = {"schema_version": SchemaVersion(schema_version)}
        type_hints = self._resolve_hints(message_cls)
        for f in dataclasses.fields(message_cls):
            if f.name == "schema_version":
                continue
            target_type = type_hints.get(f.name, cast("type", f.type))
            kwargs[f.name] = self._deserialize_value(
                occurred_at if f.name == "occurred_at" else payload.get(f.name), target_type
            )
        return message_cls(**kwargs)

    def _resolve_hints(self, cls: type) -> dict[str, type]:
        try:
            return get_type_hints(cls)
        except NameError:
            return {}

    def _serialize_value(self, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, CreatedAt):
            return value.value.isoformat()
        if isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        if isinstance(value, dict):
            return {str(k): self._serialize_value(v) for k, v in value.items()}
        if hasattr(value, "value"):
            return str(value.value)
        if dataclasses.is_dataclass(value):
            return {
                f.name: self._serialize_value(getattr(value, f.name))
                for f in dataclasses.fields(value)
            }
        return str(value)

    def _deserialize_value(self, value: object, target_type: type) -> object:
        if value is None:
            return None
        origin = getattr(target_type, "__origin__", None)
        if origin is list:
            args = getattr(target_type, "__args__", ())
            inner = args[0] if args else str
            return (
                [self._deserialize_value(item, inner) for item in value]
                if isinstance(value, list)
                else []
            )
        if origin is dict:
            return dict(value) if isinstance(value, dict) else {}
        if target_type is str:
            return str(value)
        if target_type is int:
            return int(str(value)) if not isinstance(value, int) else value
        if target_type is float:
            return float(str(value)) if not isinstance(value, float) else value
        if target_type is bool:
            return value.lower() in ("true", "1", "yes") if isinstance(value, str) else bool(value)
        if target_type is datetime:
            return datetime.fromisoformat(value) if isinstance(value, str) else value
        if target_type is CreatedAt:
            if isinstance(value, str):
                return CreatedAt.from_datetime(datetime.fromisoformat(value))
            return CreatedAt.from_datetime(value) if isinstance(value, datetime) else value
        if target_type is OccurredAt:
            if isinstance(value, str):
                return OccurredAt.from_datetime(datetime.fromisoformat(value))
            return OccurredAt.from_datetime(value) if isinstance(value, datetime) else value
        if isinstance(value, (str, int, float, bool)) and dataclasses.is_dataclass(target_type):
            fields = dataclasses.fields(target_type)
            if len(fields) == 1 and (
                not hasattr(target_type, "__dataclass_params__")
                or not target_type.__dataclass_params__.kw_only
            ):
                inner_type = self._resolve_hints(target_type).get(
                    fields[0].name, cast("type", fields[0].type)
                )
                return target_type(self._deserialize_value(value, inner_type))  # type: ignore[call-arg]
        if dataclasses.is_dataclass(target_type) and isinstance(value, dict):
            hints = self._resolve_hints(target_type)
            return target_type(
                **{
                    f.name: self._deserialize_value(
                        value.get(f.name), hints.get(f.name, cast("type", f.type))
                    )
                    for f in dataclasses.fields(target_type)
                }
            )
        return value
