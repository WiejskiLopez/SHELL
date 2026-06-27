"""Główny kontener DI — składa infrastrukturę, domenę i warstwę aplikacyjną."""

from __future__ import annotations

from dependency_injector import containers, providers
from shell.infrastructure.scheduling.services.scheduler_service import SchedulerService

from .application_container import ApplicationContainer
from .domain_container import DomainContainer
from .events_container import EventsContainer
from .infrastructure_container import InfrastructureContainer
from .process_container import ProcessContainer


class CoreContainer(containers.DeclarativeContainer):
    """Kompozytor wszystkich sub-kontenerów DI."""

    config = providers.Configuration()
    config.override(
        {
            "events": {
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

    app: providers.Container[ApplicationContainer] = providers.Container(
        ApplicationContainer,
        config=config,
        infra=infra,
        domain=domain,
    )

    events = providers.Container(
        EventsContainer,
        config=config.events,
        infra=infra,
        buses=app.buses,
    )

    process: providers.Container[ProcessContainer] = providers.Container(
        ProcessContainer,
        infra=infra,
        buses=app.buses,
    )

    scheduler_service = providers.Singleton(
        SchedulerService,
        session_factory=infra.session_factory,
        outbox_to_inbox_relay=events.outbox_to_inbox_relay,
        inbox_processor=events.inbox_processor,
    )
