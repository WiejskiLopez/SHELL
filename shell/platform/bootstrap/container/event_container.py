"""Container for event handlers (event bus subscribers)."""

from __future__ import annotations

from dependency_injector import containers, providers


class EventContainer(containers.DeclarativeContainer):
    """Container for event handlers (event bus subscribers) — cleaned up."""

    infra = providers.DependenciesContainer()
    domain = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()
