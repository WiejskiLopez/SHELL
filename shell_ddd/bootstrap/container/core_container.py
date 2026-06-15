"""Główny kontener DI — składa infrastrukturę, domenę i warstwę aplikacyjną."""
from __future__ import annotations

from dependency_injector import containers, providers

from .application_container import ApplicationContainer
from .domain_container import DomainContainer
from .infrastructure_container import InfrastructureContainer
from .messaging_container import MessagingContainer


class CoreContainer(containers.DeclarativeContainer):
    """Kompozytor wszystkich sub-kontenerów DI."""

    config = providers.Configuration()
    config.messaging = providers.Configuration()  # nested config

    infra = providers.Container(InfrastructureContainer, config=config)
    domain = providers.Container(DomainContainer)
    messaging = providers.Container(
        MessagingContainer,
        config=config.messaging,
        infra=infra,
    )

    app = providers.Container(
        ApplicationContainer,
        config=config,
        infra=infra,
        domain=domain,
        messaging=messaging,  # pass messaging container
    )