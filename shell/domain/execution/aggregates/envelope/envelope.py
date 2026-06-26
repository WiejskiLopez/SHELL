from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.envelope.entities.envelope_event import EnvelopeEvent
from shell.domain.execution.aggregates.envelope.events.envelope_deadlettered_event import (
    EnvelopeDeadletteredEvent,
)
from shell.domain.execution.aggregates.envelope.events.envelope_receiver_changed_event import (
    EnvelopeReceiverChangedEvent,
)
from shell.domain.execution.aggregates.envelope.events.envelope_routed_event import (
    EnvelopeRoutedEvent,
)
from shell.domain.execution.aggregates.envelope.events.envelope_stage_changed_event import (
    EnvelopeStageChangedEvent,
)
from shell.domain.execution.aggregates.envelope.events.envelope_status_changed_event import (
    EnvelopeStatusChangedEvent,
)
from shell.domain.execution.aggregates.envelope.exceptions.invalid_envelope_transition import (
    InvalidEnvelopeTransition,
)
from shell.domain.execution.aggregates.envelope.value_objects.archive_uri import ArchiveUri
from shell.domain.execution.aggregates.envelope.value_objects.artifact_uri import ArtifactUri
from shell.domain.execution.aggregates.envelope.value_objects.correlation_id import CorrelationId
from shell.domain.execution.aggregates.envelope.value_objects.envelope_id import EnvelopeId
from shell.domain.execution.aggregates.envelope.value_objects.payload import Payload
from shell.domain.execution.aggregates.envelope.value_objects.sequence_id import SequenceId
from shell.domain.execution.aggregates.envelope.value_objects.source_role import SourceRole
from shell.domain.execution.aggregates.envelope.value_objects.step import Step
from shell.domain.execution.aggregates.envelope.value_objects.target_role import TargetRole
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
from shell.domain.platform.value_objects.updated_at import UpdatedAt

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
        correlation_id: CorrelationId,
        sender_graph_node_execution_id: GraphNodeExecutionId,
        receiver_graph_node_execution_id: GraphNodeExecutionId,
        source_role: SourceRole,
        target_role: TargetRole,
        sequence_id: SequenceId,
        step: Step,
        status: EnvelopeStatus,
        stage: EnvelopeStage,
        payload: Payload,
        artifact_uri: ArtifactUri,
        archive_uri: ArchiveUri,
        created_at: CreatedAt,
        updated_at: UpdatedAt,
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

    @classmethod
    def restore(
        cls,
        id: EnvelopeId,
        workflow_id: WorkflowId,
        parent_id: EnvelopeId | None,
        correlation_id: CorrelationId,
        sender_graph_node_execution_id: GraphNodeExecutionId,
        receiver_graph_node_execution_id: GraphNodeExecutionId,
        source_role: SourceRole,
        target_role: TargetRole,
        sequence_id: SequenceId,
        step: Step,
        status: EnvelopeStatus,
        stage: EnvelopeStage,
        payload: Payload,
        artifact_uri: ArtifactUri,
        archive_uri: ArchiveUri,
        created_at: CreatedAt,
        updated_at: UpdatedAt,
        events: list[EnvelopeEvent] | None = None,
    ) -> Self:
        return cls(
            id=id,
            workflow_id=workflow_id,
            parent_id=parent_id,
            correlation_id=correlation_id,
            sender_graph_node_execution_id=sender_graph_node_execution_id,
            receiver_graph_node_execution_id=receiver_graph_node_execution_id,
            source_role=source_role,
            target_role=target_role,
            sequence_id=sequence_id,
            step=step,
            status=status,
            stage=stage,
            payload=payload,
            artifact_uri=artifact_uri,
            archive_uri=archive_uri,
            created_at=created_at,
            updated_at=updated_at,
            events=events,
        )

    @property
    def workflow_id(self) -> WorkflowId:
        return self._workflow_id

    @property
    def parent_id(self) -> EnvelopeId | None:
        return self._parent_id

    @property
    def correlation_id(self) -> CorrelationId:
        return self._correlation_id

    @property
    def sender_graph_node_execution_id(self) -> GraphNodeExecutionId:
        return self._sender_graph_node_execution_id

    @property
    def receiver_graph_node_execution_id(self) -> GraphNodeExecutionId:
        return self._receiver_graph_node_execution_id

    @property
    def source_role(self) -> SourceRole:
        return self._source_role

    @property
    def target_role(self) -> TargetRole:
        return self._target_role

    @property
    def sequence_id(self) -> SequenceId:
        return self._sequence_id

    @property
    def step(self) -> Step:
        return self._step

    @property
    def status(self) -> EnvelopeStatus:
        return self._status

    @property
    def stage(self) -> EnvelopeStage:
        return self._stage

    @property
    def payload(self) -> Payload:
        return self._payload

    @property
    def artifact_uri(self) -> ArtifactUri:
        return self._artifact_uri

    @property
    def archive_uri(self) -> ArchiveUri:
        return self._archive_uri

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt:
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
            correlation_id=CorrelationId(correlation_id or str(id_)),
            sender_graph_node_execution_id=sender_graph_node_execution_id,
            receiver_graph_node_execution_id=receiver_graph_node_execution_id,
            source_role=SourceRole(source_role),
            target_role=TargetRole(target_role),
            sequence_id=SequenceId(sequence_id),
            step=Step(step),
            status=EnvelopeStatus.PENDING,
            stage=EnvelopeStage.DRAFT,
            payload=Payload(payload or {}),
            artifact_uri=ArtifactUri(""),
            archive_uri=ArchiveUri(""),
            created_at=CreatedAt.from_datetime(now),
            updated_at=UpdatedAt.from_datetime(now),
        )

    def transition_status(self, new_status: EnvelopeStatus, now: datetime) -> None:
        allowed = _STATUS_TRANSITIONS.get(self._status, set())
        if new_status not in allowed:
            raise InvalidEnvelopeTransition(
                f"Cannot transition envelope {self.id.value!r} "
                f"from {self._status.value!r} to {new_status.value!r}"
            )
        previous_status = self._status
        self._status = new_status
        self._updated_at = UpdatedAt.from_datetime(now)
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
        self.append_event(
            EnvelopeStatusChangedEvent.now(self.id, previous_status, new_status, now=now)
        )
        if new_status == EnvelopeStatus.DELIVERED:
            self.append_event(EnvelopeRoutedEvent.now(self.id, self._workflow_id, now=now))
        elif new_status == EnvelopeStatus.DEAD:
            self.append_event(
                EnvelopeDeadletteredEvent.now(self.id, self._workflow_id, reason="deadlettered", now=now)
            )

    def transition_stage(self, new_stage: EnvelopeStage, now: datetime) -> None:
        self._stage = new_stage
        self._updated_at = UpdatedAt.from_datetime(now)
        self.append_event(EnvelopeStageChangedEvent.now(self.id, new_stage, now=now))

    def deliver_to(self, graph_node_execution_id: GraphNodeExecutionId, now: datetime) -> None:
        self._receiver_graph_node_execution_id = graph_node_execution_id
        self._updated_at = UpdatedAt.from_datetime(now)
        self.append_event(
            EnvelopeReceiverChangedEvent.now(self.id, graph_node_execution_id, now=now)
        )

    def archive(self, archive_uri: str, now: datetime) -> None:
        self._archive_uri = ArchiveUri(archive_uri)
        self.transition_stage(EnvelopeStage.ARCHIVED, now)
