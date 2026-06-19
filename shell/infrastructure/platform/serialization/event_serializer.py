from __future__ import annotations

import dataclasses
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from shell.domain.platform.events import DomainEvent

logger = logging.getLogger(__name__)


class DomainEventSerializer:
    def to_payload(self, event: DomainEvent) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for f in dataclasses.fields(event):
            if f.name in ("occurred_at", "schema_version"):
                continue
            raw = getattr(event, f.name)
            payload[f.name] = self._serialize_value(raw)
        return payload

    def to_outbox_payload(self, event: DomainEvent) -> dict[str, Any]:
        return {
            "id": None,
            "event_type": type(event).__name__,
            "occurred_at": event.occurred_at,
            "payload": self.to_payload(event),
        }

    def from_payload(
        self,
        event_cls: type[DomainEvent],
        occurred_at: datetime,
        payload: dict[str, Any],
        schema_version: int = 1,
    ) -> DomainEvent:
        kwargs: dict[str, Any] = {"occurred_at": occurred_at, "schema_version": schema_version}
        for f in dataclasses.fields(event_cls):
            if f.name in ("occurred_at", "schema_version"):
                continue
            raw = payload.get(f.name)
            kwargs[f.name] = self._deserialize_value(raw, cast("type", f.type))
        return event_cls(**kwargs)

    def _serialize_value(self, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
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
        from shell.domain.execution.value_objects.ids import (
    EnvelopeId,
    GraphNodeExecutionId,
    TaskExecutionId,
    WorkflowId
)

        if value is None:
            return None
        origin = getattr(target_type, "__origin__", None)
        if origin is list:
            args = getattr(target_type, "__args__", ())
            inner = args[0] if args else str
            if isinstance(value, list):
                return [self._deserialize_value(item, inner) for item in value]
            return []
        if origin is dict:
            return dict(value) if isinstance(value, dict) else {}
        if target_type is str:
            return str(value)
        if target_type is int:
            return int(str(value)) if not isinstance(value, int) else value
        if target_type is float:
            return float(str(value)) if not isinstance(value, float) else value
        if target_type is bool:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)
        if target_type is datetime:
            if isinstance(value, str):
                return datetime.fromisoformat(value)
            return value
        value_obj_map: dict[type, type] = {
            EnvelopeId: EnvelopeId,
            WorkflowId: WorkflowId,
            TaskExecutionId: TaskExecutionId,
            GraphNodeExecutionId: GraphNodeExecutionId,
        }
        vo_cls = value_obj_map.get(target_type)
        if vo_cls is not None:
            return vo_cls(value) if not isinstance(value, vo_cls) else value
        if dataclasses.is_dataclass(target_type) and isinstance(value, dict):
            init_kwargs = {}
            for f in dataclasses.fields(target_type):
                init_kwargs[f.name] = self._deserialize_value(
                    value.get(f.name), cast("type", f.type)
                )
            return target_type(**init_kwargs)
        return value
