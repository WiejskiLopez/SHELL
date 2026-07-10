"""Container for process layer (orchestration, sagas, process managers)."""

from __future__ import annotations

from dependency_injector import containers, providers


class ProcessContainer(containers.DeclarativeContainer):
    """Container for orchestration layer (sagas, process managers)."""

    infra = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()
