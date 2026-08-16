"""Koncept: reguła architektoniczna dotycząca event registry isolation.

Reguła: test sprawdza kontrakt architektoniczny event registry isolation.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from _arch_helpers import architecture_assertion_message

from shell.definition_service.bootstrap.definition.event_registry import (
    build_definition_event_registry,
)
from shell.execution_service.bootstrap.execution.event_registry import (
    build_execution_event_registry,
)
from shell.ingestion_service.bootstrap.ingestion.event_registry import (
    build_ingestion_event_registry,
)
from shell.project_service.bootstrap.project.event_registry import build_project_event_registry
from shell.scheduling_service.bootstrap.scheduling.event_registry import (
    build_scheduling_event_registry,
)
from shell.session_service.bootstrap.session.event_registry import build_session_event_registry
from shell.user_service.bootstrap.user.event_registry import build_user_event_registry

if TYPE_CHECKING:
    from collections.abc import Callable
_ALLOWED_CROSS_BC = frozenset(
    {
        "shell.platform.domain",
        "shell.platform.application",
        "shell.user_service.application.user.user.integration_events",
        "shell.user_service.application.user.auth_session.integration_events",
    }
)
_REGISTRIES: tuple[tuple[str, Callable[[], dict[str, type]]], ...] = (
    ("definition", build_definition_event_registry),
    ("execution", build_execution_event_registry),
    ("ingestion", build_ingestion_event_registry),
    ("project", build_project_event_registry),
    ("scheduling", build_scheduling_event_registry),
    ("session", build_session_event_registry),
    ("user", build_user_event_registry),
)


def test_each_bc_event_registry_contains_only_owned_events() -> None:
    violations: list[str] = []
    for bounded_context, build_registry in _REGISTRIES:
        registry = build_registry()
        if not registry:
            violations.append(f"{bounded_context}: registry is empty")
            continue
        expected_prefix = f"shell.{bounded_context}_service.application.{bounded_context}."
        for event_name, event_type in registry.items():
            if event_name != event_type.__name__:
                violations.append(
                    f"{bounded_context}: key {event_name!r} does not match {event_type.__name__!r}"
                )
            is_owned = event_type.__module__.startswith(expected_prefix)
            is_explicitly_consumed = any(
                event_type.__module__.startswith(allowed + ".") for allowed in _ALLOWED_CROSS_BC
            )
            if not is_owned and (not is_explicitly_consumed):
                violations.append(
                    f"{bounded_context}: {event_type.__module__}.{event_name} is outside the owning BC and not an explicitly consumed cross-BC contract"
                )
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_each_bc_event_registry_contains_only_owned_events",
        "warunek zapisany w asercji musi być spełniony",
        "Invalid bounded-context event registries:\n" + "\n".join(violations),
    )
