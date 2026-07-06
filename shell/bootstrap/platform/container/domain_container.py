"""Container for domain services."""

from __future__ import annotations

from dependency_injector import containers, providers


class DomainContainer(containers.DeclarativeContainer):
    """Container for domain services — cleaned up."""

    infra = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()
