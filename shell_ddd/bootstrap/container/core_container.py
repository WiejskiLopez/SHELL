"""Główny kontener DI — składa infrastrukturę, domenę i warstwę aplikacyjną."""
from __future__ import annotations

from dependency_injector import containers, providers

from .application_container import ApplicationContainer
from .domain_container import DomainContainer
from .infrastructure_container import InfrastructureContainer


class CoreContainer(containers.DeclarativeContainer):
    """Kompozytor wszystkich sub-kontenerów DI."""

    config = providers.Configuration()

    infra = providers.Container(InfrastructureContainer, config=config)
    domain = providers.Container(DomainContainer)

    app = providers.Container(
        ApplicationContainer,
        config=config,
        infra=infra,
        domain=domain,
    )