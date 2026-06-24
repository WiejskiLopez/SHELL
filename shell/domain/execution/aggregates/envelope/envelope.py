from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.envelope.entities.envelope_event import EnvelopeEvent
from shell.domain.execution.aggregates.envelope.events.envelope_deadlettered_event import EnvelopeDeadletteredEvent
from shell.domain.execution.aggregates.envelope.events.envelope_routed_event import EnvelopeRoutedEvent
from shell.domain.execution.aggregates.envelope.value_objects.envelope_id import EnvelopeId
from shell.domain.execution.aggregates.envelope.exceptions.invalid_envelope_transition import (
    InvalidEnvelopeTransition,
)
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId

_STATUS_TRANSITIONS: dict[EnvelopeStatus, set[EnvelopeStatus]] = {
    EnvelopeStatus.PENDING: {EnvelopeStatus.ACTIVE, EnvelopeStatus.DEAD},
    EnvelopeStatus.ACTIVE: {EnvelopeStatus.DELIVERED, EnvelopeStatus.FAILED},
    EnvelopeStatus.DELIVERED: set(),
    EnvelopeStatus.FAILED: {EnvelopeStatus.PENDING, EnvelopeStatus.DEAD},
    EnvelopeStatus.DEAD: set(),
}


class Envelope(AggregateRoot[EnvelopeId]):
    __slots__ = (
        "_workflow_id",
        "_parent_id",
        "_correlation_id",
        "_sender_graph_node_execution_id",
        "_receiver_graph_node_execution_id",
        "_source_role",
        "_target_role",
        "_sequence_id",
        "_step",
        "_status",
        "_stage",
        "_payload",
        "_artifact_uri",
        "_archive_uri",
        "_created_at",
        "_updated_at",
        "_envelope_events",
    )

    def __init__(
        self,
        id: EnvelopeId,
        workflow_id: WorkflowId,
        parent_id: EnvelopeId | None,
        correlation_id: str,
        sender_graph_node_execution_id: GraphNodeExecutionId,
        receiver_graph_node_execution_id: GraphNodeExecutionId,
        source_role: str,
        target_role: str,
        sequence_id: int,
        step: int,
        status: EnvelopeStatus,
        stage: EnvelopeStage,
        payload: dict[str, object],
        artifact_uri: str,
        archive_uri: str,
        created_at: datetime,
        updated_at: datetime,
        events: list[EnvelopeEvent] | None = None,
    ) -> None:
        super().__init__(id)
        self._workflow_id = workflow_id
        self._parent_id = parent_id
        self._correlation_id = correlation_id
        self._sender_graph_node_execution_id = sender_graph_node_execution_id
        self._receiver_graph_node_execution_id = receiver_graph_node_execution_id
        self._source_role = source_role
        self._target_role = target_role
        self._sequence_id = sequence_id
        self._step = step
        self._status = status
        self._stage = stage
        self._payload = payload
        self._artifact_uri = artifact_uri
        self._archive_uri = archive_uri
        self._created_at = created_at
        self._updated_at = updated_at
        self._envelope_events = events or []

    @property
    def workflow_id(self) -> WorkflowId:
        return self._workflow_id

    @property
    def parent_id(self) -> EnvelopeId | None:
        return self._parent_id

    @property
    def correlation_id(self) -> str:
        return self._correlation_id

    @property
    def sender_graph_node_execution_id(self) -> GraphNodeExecutionId:
        return self._sender_graph_node_execution_id

    @property
    def receiver_graph_node_execution_id(self) -> GraphNodeExecutionId:
        return self._receiver_graph_node_execution_id

    @property
    def source_role(self) -> str:
        return self._source_role

    @property
    def target_role(self) -> str:
        return self._target_role

    @property
    def sequence_id(self) -> int:
        return self._sequence_id

    @property
    def step(self) -> int:
        return self._step

    @property
    def status(self) -> EnvelopeStatus:
        return self._status

    @property
    def stage(self) -> EnvelopeStage:
        return self._stage

    @property
    def payload(self) -> dict[str, object]:
        return dict(self._payload)

    @property
    def artifact_uri(self) -> str:
        return self._artifact_uri

    @property
    def archive_uri(self) -> str:
        return self._archive_uri

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def events(self) -> list[EnvelopeEvent]:
        return self._envelope_events.copy()

    @classmethod
    def new(
        cls,
        *,
        id_: EnvelopeId,
        workflow_id: WorkflowId,
        sender_graph_node_execution_id: GraphNodeExecutionId,
        receiver_graph_node_execution_id: GraphNodeExecutionId,
        source_role: str,
        target_role: str,
        correlation_id: str = "",
        parent_id: EnvelopeId | None = None,
        sequence_id: int = 0,
        step: int = 0,
        payload: dict[str, object] | None = None,
        now: datetime,
    ) -> Envelope:
        return cls(
            id=id_,
            workflow_id=workflow_id,
            parent_id=parent_id,
            correlation_id=correlation_id or str(id_),
            sender_graph_node_execution_id=sender_graph_node_execution_id,
            receiver_graph_node_execution_id=receiver_graph_node_execution_id,
            source_role=source_role,
            target_role=target_role,
            sequence_id=sequence_id,
            step=step,
            status=EnvelopeStatus.PENDING,
            stage=EnvelopeStage.DRAFT,
            payload=payload or {},
            artifact_uri="",
            archive_uri="",
            created_at=now,
            updated_at=now,
        )

    def transition_status(self, new_status: EnvelopeStatus, now: datetime) -> None:
        allowed = _STATUS_TRANSITIONS.get(self._status, set())
        if new_status not in allowed:
            raise InvalidEnvelopeTransition(
                f"Cannot transition envelope {self.id.value!r} "
                f"from {self._status.value!r} to {new_status.value!r}"
            )
        self._status = new_status
        self._updated_at = now
        from shell.domain.execution.aggregates.envelope.value_objects.envelope_event_id import (
            EnvelopeEventId,
        )

        self._envelope_events.append(
            EnvelopeEvent(
                id=EnvelopeEventId.generate(),
                kind="status_changed",
                payload={"status": new_status.value},
                created_at=now,
            )
        )
        if new_status == EnvelopeStatus.DELIVERED:
            self.append_event(EnvelopeRoutedEvent.now(self.id, self._workflow_id, now=now))
        elif new_status == EnvelopeStatus.DEAD:
            self.append_event(
                EnvelopeDeadletteredEvent.now(self.id, self._workflow_id, reason="deadlettered", now=now)
            )

    def transition_stage(self, new_stage: EnvelopeStage, now: datetime) -> None:
        self._stage = new_stage
        self._updated_at = now

    def deliver_to(self, graph_node_execution_id: GraphNodeExecutionId) -> None:
        self._receiver_graph_node_execution_id = graph_node_execution_id

    def archive(self, archive_uri: str, now: datetime) -> None:
        self._archive_uri = archive_uri
        self.transition_stage(EnvelopeStage.ARCHIVED, now)
