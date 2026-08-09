"""Pure-DI factories for execution command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.edge_execution.command_handlers.create_edge_execution_handler import (
        CreateEdgeExecutionHandler,
    )
    from shell.application.execution.edge_execution.command_handlers.delete_edge_execution_handler import (
        DeleteEdgeExecutionHandler,
    )
    from shell.application.execution.edge_execution.command_handlers.update_edge_execution_handler import (
        UpdateEdgeExecutionHandler,
    )
    from shell.application.execution.edge_link_execution.command_handlers.create_edge_link_execution_handler import (
        CreateEdgeLinkExecutionHandler,
    )
    from shell.application.execution.edge_link_execution.command_handlers.delete_edge_link_execution_handler import (
        DeleteEdgeLinkExecutionHandler,
    )
    from shell.application.execution.edge_link_execution.command_handlers.update_edge_link_execution_handler import (
        UpdateEdgeLinkExecutionHandler,
    )
    from shell.application.execution.node_execution.command_handlers.create_node_execution_handler import (
        CreateNodeExecutionHandler,
    )
    from shell.application.execution.node_execution.command_handlers.delete_node_execution_handler import (
        DeleteNodeExecutionHandler,
    )
    from shell.platform.bootstrap.container.infrastructure import Infrastructure


class ExecutionCommandFactories:
    """Factories for command handlers owned by the execution bounded context."""

    _infra: Infrastructure

    def delete_node_execution_handler_factory(self) -> DeleteNodeExecutionHandler:
        from shell.application.execution.node_execution.command_handlers.delete_node_execution_handler import (
            DeleteNodeExecutionHandler,
        )

        return DeleteNodeExecutionHandler(
            unit_of_work=self._infra.node_execution_unit_of_work_factory(),
            clock=self._infra.clock_factory(),
        )

    def create_node_execution_handler_factory(self) -> CreateNodeExecutionHandler:
        from shell.application.execution.node_execution.command_handlers.create_node_execution_handler import (
            CreateNodeExecutionHandler,
        )

        return CreateNodeExecutionHandler(
            unit_of_work=self._infra.node_execution_unit_of_work_factory(),
            identity=self._infra.id_generator_factory(),
            time=self._infra.clock_factory(),
        )

    def create_edge_execution_handler_factory(self) -> CreateEdgeExecutionHandler:
        from shell.application.execution.edge_execution.command_handlers.create_edge_execution_handler import (
            CreateEdgeExecutionHandler,
        )

        return CreateEdgeExecutionHandler(
            unit_of_work=self._infra.edge_execution_unit_of_work_factory(),
            identity=self._infra.id_generator_factory(),
            time=self._infra.clock_factory(),
        )

    def update_edge_execution_handler_factory(self) -> UpdateEdgeExecutionHandler:
        from shell.application.execution.edge_execution.command_handlers.update_edge_execution_handler import (
            UpdateEdgeExecutionHandler,
        )

        return UpdateEdgeExecutionHandler(
            unit_of_work=self._infra.edge_execution_unit_of_work_factory(),
            time=self._infra.clock_factory(),
            logger=self._infra.stdlib_logger,
        )

    def delete_edge_execution_handler_factory(self) -> DeleteEdgeExecutionHandler:
        from shell.application.execution.edge_execution.command_handlers.delete_edge_execution_handler import (
            DeleteEdgeExecutionHandler,
        )

        return DeleteEdgeExecutionHandler(
            unit_of_work=self._infra.edge_execution_unit_of_work_factory(),
            time=self._infra.clock_factory(),
            logger=self._infra.stdlib_logger,
        )

    def create_edge_link_execution_handler_factory(self) -> CreateEdgeLinkExecutionHandler:
        from shell.application.execution.edge_link_execution.command_handlers.create_edge_link_execution_handler import (
            CreateEdgeLinkExecutionHandler,
        )

        return CreateEdgeLinkExecutionHandler(
            unit_of_work=self._infra.edge_link_execution_unit_of_work_factory(),
            identity=self._infra.id_generator_factory(),
            time=self._infra.clock_factory(),
        )

    def delete_edge_link_execution_handler_factory(self) -> DeleteEdgeLinkExecutionHandler:
        from shell.application.execution.edge_link_execution.command_handlers.delete_edge_link_execution_handler import (
            DeleteEdgeLinkExecutionHandler,
        )

        return DeleteEdgeLinkExecutionHandler(
            unit_of_work=self._infra.edge_link_execution_unit_of_work_factory(),
            time=self._infra.clock_factory(),
            logger=self._infra.stdlib_logger,
        )

    def update_edge_link_execution_handler_factory(self) -> UpdateEdgeLinkExecutionHandler:
        from shell.application.execution.edge_link_execution.command_handlers.update_edge_link_execution_handler import (
            UpdateEdgeLinkExecutionHandler,
        )

        return UpdateEdgeLinkExecutionHandler(
            unit_of_work=self._infra.edge_link_execution_unit_of_work_factory(),
            time=self._infra.clock_factory(),
            logger=self._infra.stdlib_logger,
        )


__all__ = ["ExecutionCommandFactories"]
