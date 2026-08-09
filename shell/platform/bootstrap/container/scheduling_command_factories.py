"""Pure-DI factories for scheduling command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.scheduling.scheduler_definition.command_handlers.create_scheduler_definition_handler import (
        CreateSchedulerDefinitionHandler,
    )
    from shell.application.scheduling.scheduler_definition.command_handlers.delete_scheduler_definition_handler import (
        DeleteSchedulerDefinitionHandler,
    )
    from shell.application.scheduling.scheduler_definition.command_handlers.update_scheduler_definition_handler import (
        UpdateSchedulerDefinitionHandler,
    )
    from shell.application.scheduling.scheduler_execution.command_handlers.create_scheduler_execution_handler import (
        CreateSchedulerExecutionHandler,
    )
    from shell.application.scheduling.scheduler_execution.command_handlers.delete_scheduler_execution_handler import (
        DeleteSchedulerExecutionHandler,
    )
    from shell.application.scheduling.scheduler_execution.command_handlers.update_scheduler_execution_handler import (
        UpdateSchedulerExecutionHandler,
    )
    from shell.application.scheduling.scheduler_job.command_handlers.create_scheduler_job_handler import (
        CreateSchedulerJobHandler,
    )
    from shell.application.scheduling.scheduler_job.command_handlers.delete_scheduler_job_handler import (
        DeleteSchedulerJobHandler,
    )
    from shell.application.scheduling.scheduler_job.command_handlers.update_scheduler_job_handler import (
        UpdateSchedulerJobHandler,
    )
    from shell.platform.bootstrap.container.infrastructure import Infrastructure


class SchedulingCommandFactories:
    """Factories for scheduling command handlers."""

    _infra: Infrastructure

    def create_scheduler_definition_handler_factory(self) -> CreateSchedulerDefinitionHandler:
        from shell.application.scheduling.scheduler_definition.command_handlers.create_scheduler_definition_handler import (
            CreateSchedulerDefinitionHandler,
        )

        return CreateSchedulerDefinitionHandler(
            unit_of_work=self._infra.scheduler_definition_unit_of_work_factory(),
            clock=self._infra.clock_factory(),
            id_generator=self._infra.id_generator_factory(),
        )

    def update_scheduler_definition_handler_factory(self) -> UpdateSchedulerDefinitionHandler:
        from shell.application.scheduling.scheduler_definition.command_handlers.update_scheduler_definition_handler import (
            UpdateSchedulerDefinitionHandler,
        )

        return UpdateSchedulerDefinitionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def delete_scheduler_definition_handler_factory(self) -> DeleteSchedulerDefinitionHandler:
        from shell.application.scheduling.scheduler_definition.command_handlers.delete_scheduler_definition_handler import (
            DeleteSchedulerDefinitionHandler,
        )

        return DeleteSchedulerDefinitionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def create_scheduler_execution_handler_factory(self) -> CreateSchedulerExecutionHandler:
        from shell.application.scheduling.scheduler_execution.command_handlers.create_scheduler_execution_handler import (
            CreateSchedulerExecutionHandler,
        )

        return CreateSchedulerExecutionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
            id_generator=self._infra.id_generator_factory(),
        )

    def update_scheduler_execution_handler_factory(self) -> UpdateSchedulerExecutionHandler:
        from shell.application.scheduling.scheduler_execution.command_handlers.update_scheduler_execution_handler import (
            UpdateSchedulerExecutionHandler,
        )

        return UpdateSchedulerExecutionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def delete_scheduler_execution_handler_factory(self) -> DeleteSchedulerExecutionHandler:
        from shell.application.scheduling.scheduler_execution.command_handlers.delete_scheduler_execution_handler import (
            DeleteSchedulerExecutionHandler,
        )

        return DeleteSchedulerExecutionHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def create_scheduler_job_handler_factory(self) -> CreateSchedulerJobHandler:
        from shell.application.scheduling.scheduler_job.command_handlers.create_scheduler_job_handler import (
            CreateSchedulerJobHandler,
        )

        return CreateSchedulerJobHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
            id_generator=self._infra.id_generator_factory(),
        )

    def update_scheduler_job_handler_factory(self) -> UpdateSchedulerJobHandler:
        from shell.application.scheduling.scheduler_job.command_handlers.update_scheduler_job_handler import (
            UpdateSchedulerJobHandler,
        )

        return UpdateSchedulerJobHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def delete_scheduler_job_handler_factory(self) -> DeleteSchedulerJobHandler:
        from shell.application.scheduling.scheduler_job.command_handlers.delete_scheduler_job_handler import (
            DeleteSchedulerJobHandler,
        )

        return DeleteSchedulerJobHandler(
            unit_of_work=self._infra.unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )


__all__ = ["SchedulingCommandFactories"]
