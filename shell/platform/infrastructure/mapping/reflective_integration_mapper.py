"""Single reflective mapper — maps any domain event to its integration event.

Uses naming convention: ``SessionOpenedEvent`` → ``SessionOpenedIntegrationEvent``
and module path convention: ``shell.domain.…`` → ``shell.application.…``

No per-aggregate mappers, no isinstance, no try/except, no fallbacks.
"""

from __future__ import annotations

import dataclasses
import importlib
import re
from typing import Any

from shell.platform.application.context.causation_id import get_causation_id
from shell.platform.application.context.correlation_id import get_correlation_id
from shell.platform.application.events import IntegrationEvent

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
        if parts[1] == "platform":
            # shell.platform.domain.events.aggregate_deleted_event
            # → shell.application.domain.integration_events.aggregate_deleted_integration_event
            int_file = re.sub(r"(?<!^)(?=[A-Z])", "_", int_name).lower()
            full_mod = f"shell.application.domain.integration_events.{int_file}"
        else:
            # shell.domain.<bc>.aggregates.<agg>.events.<file>
            # → shell.application.<bc>.<agg>.integration_events.<file>
            bc = parts[2]
            agg = parts[4]
            int_file = re.sub(r"(?<!^)(?=[A-Z])", "_", int_name).lower()
            full_mod = f"shell.application.{bc}.{agg}.integration_events.{int_file}"

        try:
            mod = importlib.import_module(full_mod)
        except ModuleNotFoundError:
            raise ValueError(f"Cannot find integration event {int_name} in {full_mod}") from None
        int_cls = getattr(mod, int_name, None)
        if int_cls is None:
            raise ValueError(f"Cannot find integration event {int_name} in {full_mod}")
        return int_cls  # type: ignore[no-any-return]

    def _to_str(self, raw: Any) -> str | None:
        if raw is None:
            return None
        return str(raw.value)
