"""ProjectProvisionSagaManager — maszyna stanów pilota sagi.

Krok ``provision_workspace`` wysyłany komendą delivery; wynik (sukces/porażka)
dociera jako fakt; w razie porażki dispatchowana jest kompensacja.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

from shell.platform.process.saga.base.saga_manager import SagaManager
from shell.platform.process.saga.base.saga_state import SagaStatus
from shell.platform.process.saga.saga_instance import SagaInstance
from shell.project_service.application.project.project_provision.commands.provision_workspace_command import (
    ProvisionWorkspaceCommand,
)
from shell.project_service.application.project.project_provision.integration_events.workspace_provision_failed_integration_event import (
    WorkspaceProvisionFailedIntegrationEvent,
)
from shell.project_service.application.project.project_provision.integration_events.workspace_provisioned_integration_event import (
    WorkspaceProvisionedIntegrationEvent,
)
from shell.project_service.application.project.project_provision.integration_events.workspace_released_integration_event import (
    WorkspaceReleasedIntegrationEvent,
)
from shell.project_service.process.project.project_provision.steps import PROJECT_PROVISION_STEPS

if TYPE_CHECKING:
    from collections.abc import Callable

    from shell.platform.application.events.integration_event import IntegrationEvent
    from shell.platform.process.saga.ports.command_delivery_dispatcher import (
        CommandDeliveryDispatcher,
    )
    from shell.platform.process.saga.ports.saga_repository import SagaRepository
    from shell.platform.process.saga.ports.saga_timeout_repository import (
        SagaTimeoutRepository,
    )
    from shell.platform.process.saga.saga_timed_out import SagaTimedOut

SAGA_TYPE = "project_provision"


class ProjectProvisionSagaManager(SagaManager):
    """Koordynator jednokrokowego procesu "provision workspace" projektu."""

    __slots__ = ()

    def __init__(
        self,
        saga_id: str,
        saga_key: str,
        *,
        repository: SagaRepository,
        dispatcher: CommandDeliveryDispatcher,
        timeouts: SagaTimeoutRepository,
    ) -> None:
        super().__init__(
            saga_id, saga_key, PROJECT_PROVISION_STEPS, dispatcher, repository, timeouts
        )

    async def start(self, project_id: str, fail: bool = False) -> None:
        """Tworzy instancję i uruchamia pierwszy krok (komenda delivery)."""
        step = self._steps.by_name("provision_workspace")
        instance = SagaInstance(
            saga_id=self.saga_id,
            saga_type=SAGA_TYPE,
            saga_key=self.saga_key,
            status=SagaStatus.RUNNING,
            business_payload={"project_id": project_id},
            current_step=step.name,
        )
        await self._repository.create(instance)
        await self.dispatch_step(step, ProvisionWorkspaceCommand(project_id=project_id, fail=fail))

    async def on_event(self, event: IntegrationEvent) -> None:
        """Guard na bieżącym stanie → mutacja → ewentualna kompensacja."""
        if isinstance(event, WorkspaceProvisionedIntegrationEvent):
            await self._complete(event.project_id)
        elif isinstance(event, WorkspaceProvisionFailedIntegrationEvent):
            await self._fail(event.project_id)
        elif isinstance(event, WorkspaceReleasedIntegrationEvent):
            await self._complete_compensation(event.project_id)

    async def on_timeout(self, event: SagaTimedOut) -> None:
        instance = await self._repository.get_by_key(SAGA_TYPE, event.saga_key)
        if (
            instance is None
            or instance.saga_id != event.saga_id
            or instance.status is not SagaStatus.RUNNING
            or instance.current_step != event.step
        ):
            return
        await self._fail(event.saga_key, expected_saga_id=event.saga_id, failed_step=event.step)

    async def _complete(self, project_id: str) -> None:
        instance = await self._repository.get_by_key(SAGA_TYPE, project_id)
        if (
            instance is None
            or instance.status is not SagaStatus.RUNNING
            or instance.current_step != "provision_workspace"
        ):
            return
        await self._timeouts.cancel(saga_id=instance.saga_id, step="provision_workspace")
        await self._repository.update(
            SagaInstance(
                saga_id=instance.saga_id,
                saga_type=SAGA_TYPE,
                saga_key=self.saga_key,
                status=SagaStatus.COMPLETED,
                business_payload=instance.business_payload,
                completed_steps=instance.completed_steps + ("provision_workspace",),
                current_step=None,
                version=instance.version,
                completed_at=datetime.now(tz=UTC),
            )
        )

    async def _fail(
        self,
        project_id: str,
        *,
        expected_saga_id: str | None = None,
        failed_step: str = "provision_workspace",
    ) -> None:
        instance = await self._repository.get_by_key(SAGA_TYPE, project_id)
        if (
            instance is None
            or instance.status is not SagaStatus.RUNNING
            or instance.current_step != failed_step
            or (expected_saga_id is not None and instance.saga_id != expected_saga_id)
        ):
            return
        step = self._steps.by_name(failed_step)
        failed_steps = instance.failed_steps + (failed_step,)
        if step.compensation_command is not None and (
            failed_step in instance.completed_steps or step.compensate_on_failure
        ):
            compensation = cast("Any", step.compensation_command)(project_id=project_id)
            await self._repository.update(
                SagaInstance(
                    saga_id=instance.saga_id,
                    saga_type=SAGA_TYPE,
                    saga_key=instance.saga_key,
                    status=SagaStatus.COMPENSATING,
                    business_payload=instance.business_payload,
                    failed_steps=failed_steps,
                    current_step=f"compensation:{failed_step}",
                    version=instance.version,
                    failed_at=datetime.now(tz=UTC),
                )
            )
            await self.dispatch_compensation(step, compensation)
            return
        now = datetime.now(tz=UTC)
        await self._repository.update(
            SagaInstance(
                saga_id=instance.saga_id,
                saga_type=SAGA_TYPE,
                saga_key=instance.saga_key,
                status=SagaStatus.COMPENSATED,
                business_payload=instance.business_payload,
                failed_steps=failed_steps,
                current_step=None,
                version=instance.version,
                failed_at=now,
                compensated_at=now,
            )
        )

    async def _complete_compensation(self, project_id: str) -> None:
        instance = await self._repository.get_by_key(SAGA_TYPE, project_id)
        if (
            instance is None
            or instance.status is not SagaStatus.COMPENSATING
            or instance.current_step != "compensation:provision_workspace"
        ):
            return
        await self._repository.update(
            SagaInstance(
                saga_id=instance.saga_id,
                saga_type=SAGA_TYPE,
                saga_key=instance.saga_key,
                status=SagaStatus.COMPENSATED,
                business_payload=instance.business_payload,
                failed_steps=instance.failed_steps,
                current_step=None,
                version=instance.version,
                failed_at=instance.failed_at,
                compensated_at=datetime.now(tz=UTC),
            )
        )


def build_project_provision_manager_factory(
    *,
    repository: SagaRepository,
    dispatcher: CommandDeliveryDispatcher,
    timeouts: SagaTimeoutRepository,
) -> Callable[..., ProjectProvisionSagaManager]:
    """Fabryka managerów per instancja (używana przez handlery i Composition Root)."""

    def _factory(saga_key: str, *, saga_id: str | None = None) -> ProjectProvisionSagaManager:
        return ProjectProvisionSagaManager(
            saga_id=saga_id or str(uuid.uuid4()),
            saga_key=saga_key,
            repository=repository,
            dispatcher=dispatcher,
            timeouts=timeouts,
        )

    return _factory
