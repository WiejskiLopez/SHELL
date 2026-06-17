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
    config.override(
        {
            "messaging": {
                "outbox_batch_size": 100,
                "inbox_batch_size": 50,
                "worker_poll_interval": 1.0,
                "worker_backoff_factor": 2.0,
                "worker_max_backoff": 30.0,
            }
        }
    )

    infra = providers.Container(InfrastructureContainer, config=config)
    domain = providers.Container(DomainContainer)
    messaging = providers.Container(
        MessagingContainer,
        config=config.messaging,
        infra=infra,
    )

    app: providers.Container[ApplicationContainer] = providers.Container(
        ApplicationContainer,
        config=config,
        infra=infra,
        domain=domain,
    )

    @property
    def app_container(self) -> ApplicationContainer:
        return self.app()
