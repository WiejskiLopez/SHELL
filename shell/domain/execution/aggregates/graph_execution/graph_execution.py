from __future__ import annotations
from shell.platform.domain.exceptions.domain_error import DomainError

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_definition_id_ref import (
    GraphDefinitionIdRef,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_status import (
    GraphExecutionStatus,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.max_subgraph_depth import (
    MaxSubgraphDepth,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.platform.domain.value_objects.deleted_at import DeletedAt
    from shell.platform.domain.value_objects.updated_at import UpdatedAt


from shell.domain.execution.aggregates.graph_execution.events.graph_execution_created_event import (
    GraphExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_deleted_event import (
    GraphExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_updated_event import (
    GraphExecutionUpdatedEvent,
)


class GraphExecution(AggregateRoot[GraphExecutionId]):
    __slots__ = (
        "_task_execution_id",
        "_parent_graph_execution_id",
        "_depth",
        "_max_subgraph_depth",
        "_execution_status",
        "_graph_definition_id",
        "_created_at",
        "_updated_at",
        "_deleted_at",
    )

    def __init__(
        self,
        id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        depth: GraphDepth,
        max_subgraph_depth: MaxSubgraphDepth,
        parent_graph_execution_id: GraphExecutionId | None = None,
        graph_definition_id: GraphDefinitionIdRef | None = None,
        created_at: CreatedAt,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._task_execution_id = task_execution_id
        self._parent_graph_execution_id = parent_graph_execution_id
        self._depth = depth
        self._max_subgraph_depth = max_subgraph_depth
        self._execution_status = GraphExecutionStatus.PENDING
        self._graph_definition_id = (
            graph_definition_id
            if graph_definition_id is not None
            else GraphDefinitionIdRef.generate()
        )
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @classmethod
    def restore(
        cls,
        id: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        depth: GraphDepth,
        max_subgraph_depth: MaxSubgraphDepth,
        parent_graph_execution_id: GraphExecutionId | None = None,
        graph_definition_id: GraphDefinitionIdRef | None = None,
        created_at: CreatedAt,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
    ) -> Self:
        instance = cls(
            id=id,
            task_execution_id=task_execution_id,
            parent_graph_execution_id=parent_graph_execution_id,
            depth=depth,
            max_subgraph_depth=max_subgraph_depth,
            graph_definition_id=graph_definition_id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )
        return instance

    @classmethod
    def initialize(
        cls,
        id_: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        graph_definition_id: GraphDefinitionIdRef,
        now: CreatedAt,
    ) -> GraphExecution:
        instance = cls(
            id=id_,
            task_execution_id=task_execution_id,
            depth=GraphDepth(0),
            max_subgraph_depth=MaxSubgraphDepth(5),
            graph_definition_id=graph_definition_id,
            created_at=now,
        )

        instance.append_event(
            GraphExecutionCreatedEvent.now(
                graph_execution_id=id_,
                task_execution_id=task_execution_id,
                now=now,
            )
        )
        return instance

    def update_status(self, new_status: GraphExecutionStatus, now: UpdatedAt) -> None:
        if self._deleted_at is not None:
            raise DomainError("Cannot update status of a deleted graph execution")
        self._execution_status = new_status
        self._updated_at = now
        self.append_event(
            GraphExecutionUpdatedEvent.now(
                graph_execution_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )

    def soft_delete(self, now: DeletedAt) -> None:
        if self._deleted_at is not None:
            raise DomainError("Graph execution already deleted")
        self._deleted_at = now
        self.append_event(
            GraphExecutionDeletedEvent.now(
                graph_execution_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )

    @classmethod
    def create_main_round(
        cls,
        id_: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        depth: GraphDepth,
        max_subgraph_depth: MaxSubgraphDepth,
    ) -> GraphExecution:
        return cls(
            id=id_,
            task_execution_id=task_execution_id,
            parent_graph_execution_id=None,
            depth=depth,
            max_subgraph_depth=max_subgraph_depth,
        )

    @classmethod
    def create_sub_graph(
        cls,
        id_: GraphExecutionId,
        task_execution_id: TaskExecutionId,
        parent_id: GraphExecutionId,
        parent_depth: GraphDepth,
        max_subgraph_depth: MaxSubgraphDepth,
    ) -> GraphExecution:
        depth_val = GraphDepth(parent_depth.value + 1)
        if depth_val.value > max_subgraph_depth.value:
            raise DomainError(
                f"Cannot create sub-graph at depth {depth_val.value}, max is {max_subgraph_depth.value}"
            )
        return cls(
            id=id_,
            task_execution_id=task_execution_id,
            parent_graph_execution_id=parent_id,
            depth=depth_val,
            max_subgraph_depth=max_subgraph_depth,
        )




    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            GraphExecutionDeletedEvent.now(
                graphexecution_id=self._id,
                now=now,
            )
        )


    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            GraphExecutionUpdatedEvent.now(
                graphexecution_id=self._id,
                now=now,
            )
        )

    @property
    def task_execution_id(self) -> TaskExecutionId:
        return self._task_execution_id

    @property
    def parent_graph_execution_id(self) -> GraphExecutionId | None:
        return self._parent_graph_execution_id

    @property
    def depth(self) -> GraphDepth:
        return self._depth

    @property
    def max_subgraph_depth(self) -> MaxSubgraphDepth:
        return self._max_subgraph_depth

    @property
    def execution_status(self) -> GraphExecutionStatus:
        return self._execution_status

    @property
    def status(self) -> GraphExecutionStatus:
        return self._execution_status

    @property
    def graph_definition_id(self) -> GraphDefinitionIdRef:
        return self._graph_definition_id

    @property
    def created_at(self) -> CreatedAt | None:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt | None:
        return self._updated_at

    @property
    def deleted_at(self) -> DeletedAt | None:
        return self._deleted_at
