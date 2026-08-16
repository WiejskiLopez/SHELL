"""Single reflective mapper for the current bounded-context event topology."""

from __future__ import annotations

import dataclasses
import importlib
import re
from typing import Any

from shell.platform.application.context.causation_id import get_causation_id
from shell.platform.application.context.correlation_id import get_correlation_id
from shell.platform.application.events import IntegrationEvent
from shell.platform.infrastructure.mapping.integration_mapping_error import (
    IntegrationMappingError,
)

ENVELOPE_FIELDS: frozenset[str] = frozenset(f.name for f in dataclasses.fields(IntegrationEvent))


class ReflectiveIntegrationMapper:
    def map(self, domain_event: object) -> object:
        int_cls = self._resolve_int_class(domain_event)

        kwargs: dict[str, Any] = {
            "event_id": str(domain_event.event_id.value),  # type: ignore[attr-defined]
            "correlation_id": get_correlation_id(),
            "causation_id": get_causation_id(),
            "occurred_at": domain_event.occurred_at.value,  # type: ignore[attr-defined]
            "aggregate_id": str(domain_event.aggregate_id.value),  # type: ignore[attr-defined]
            "aggregate_name": str(domain_event.aggregate_name.value),  # type: ignore[attr-defined]
            "schema_version": int(domain_event.schema_version.value),  # type: ignore[attr-defined]
        }

        for f in dataclasses.fields(int_cls):
            if f.name in ENVELOPE_FIELDS:
                continue

            raw: Any = getattr(domain_event, f.name)
            kwargs[f.name] = self._to_str(raw)

        return int_cls(**kwargs)

    def _resolve_int_class(self, domain_event: object) -> type:
        event_cls = type(domain_event)
        int_name = event_cls.__name__.replace("Event", "IntegrationEvent")

        parts = event_cls.__module__.split(".")
        if (
            len(parts) <= 5
            or parts[0] != "shell"
            or not parts[1].endswith("_service")
            or parts[2] != "domain"
        ):
            raise IntegrationMappingError(
                f"Unsupported domain event module topology: {event_cls.__module__}"
            )

        bc = parts[1][:-len("_service")]
        agg = parts[5]
        int_file = re.sub(r"(?<!^)(?=[A-Z])", "_", int_name).lower()
        full_mod = f"shell.{bc}_service.application.{bc}.{agg}.integration_events.{int_file}"

        try:
            mod = importlib.import_module(full_mod)
        except ModuleNotFoundError:
            raise IntegrationMappingError(
                f"Cannot find integration event {int_name} for domain event "
                f"{event_cls.__name__} in {full_mod}. Declare the integration event "
                "or mark the domain event as internal-only."
            ) from None
        int_cls = getattr(mod, int_name, None)
        if int_cls is None:
            raise IntegrationMappingError(
                f"Cannot find integration event {int_name} for domain event "
                f"{event_cls.__name__} in {full_mod}. Declare the integration event "
                "or mark the domain event as internal-only."
            )
        return int_cls  # type: ignore[no-any-return]

    def _to_str(self, raw: Any) -> str | None:
        if raw is None:
            return None
        return str(raw.value)
