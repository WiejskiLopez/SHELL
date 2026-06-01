"""envelope.py
Envelope — immutable value object representing a single message row.

Slots:
    _id                  — DB row id (Optional; None until persisted)
    _workflow_id         — workflow this envelope belongs to
    _parent_envelope_id  — Optional; id of the envelope that triggered this one
    _correlation_id      — Optional; conversation correlation id
    _sender_node_id      — Optional; node that emitted the envelope
    _receiver_node_id    — Optional; routed target node id (None = unrouted)
    _source_role         — role of the sender
    _target_role         — Optional; intended target role (used before routing)
    _sequence_id         — monotonic counter per workflow
    _step                — TTL counter
    _status              — EnvelopeStatus
    _stage               — EnvelopeStage
    _payload_json        — serialized payload (str)
    _artifact_uri        — Optional; path to oversized artifact
    _archive_uri         — Optional; path to archive mirror file
    _created_at          — ISO-8601
    _updated_at          — ISO-8601
"""

from __future__ import annotations

from shell.bus.envelope.envelope_stage import EnvelopeStage
from shell.bus.envelope.envelope_status import EnvelopeStatus


class Envelope:
    """Immutable value object for a single envelope row."""

    __slots__ = (
        "_id",
        "_workflow_id",
        "_parent_envelope_id",
        "_correlation_id",
        "_sender_node_id",
        "_receiver_node_id",
        "_source_role",
        "_target_role",
        "_sequence_id",
        "_step",
        "_status",
        "_stage",
        "_payload_json",
        "_artifact_uri",
        "_archive_uri",
        "_created_at",
        "_updated_at",
    )

    def __init__(
        self,
        id: int | None,
        workflow_id: str,
        parent_envelope_id: int | None,
        correlation_id: str | None,
        sender_node_id: str | None,
        receiver_node_id: str | None,
        source_role: str,
        target_role: str | None,
        sequence_id: int,
        step: int,
        status: EnvelopeStatus,
        stage: EnvelopeStage,
        payload_json: str,
        artifact_uri: str | None,
        archive_uri: str | None,
        created_at: str,
        updated_at: str,
    ) -> None:
        self._id = id
        self._workflow_id = workflow_id
        self._parent_envelope_id = parent_envelope_id
        self._correlation_id = correlation_id
        self._sender_node_id = sender_node_id
        self._receiver_node_id = receiver_node_id
        self._source_role = source_role
        self._target_role = target_role
        self._sequence_id = sequence_id
        self._step = step
        self._status = status
        self._stage = stage
        self._payload_json = payload_json
        self._artifact_uri = artifact_uri
        self._archive_uri = archive_uri
        self._created_at = created_at
        self._updated_at = updated_at

    @property
    def id_(self) -> int | None:
        return self._id

    @property
    def workflow_id_(self) -> str:
        return self._workflow_id

    @property
    def parent_envelope_id_(self) -> int | None:
        return self._parent_envelope_id

    @property
    def correlation_id_(self) -> str | None:
        return self._correlation_id

    @property
    def sender_node_id_(self) -> str | None:
        return self._sender_node_id

    @property
    def receiver_node_id_(self) -> str | None:
        return self._receiver_node_id

    @property
    def source_role_(self) -> str:
        return self._source_role

    @property
    def target_role_(self) -> str | None:
        return self._target_role

    @property
    def sequence_id_(self) -> int:
        return self._sequence_id

    @property
    def step_(self) -> int:
        return self._step

    @property
    def status_(self) -> EnvelopeStatus:
        return self._status

    @property
    def stage_(self) -> EnvelopeStage:
        return self._stage

    @property
    def payload_json_(self) -> str:
        return self._payload_json

    @property
    def artifact_uri_(self) -> str | None:
        return self._artifact_uri

    @property
    def archive_uri_(self) -> str | None:
        return self._archive_uri

    @property
    def created_at_(self) -> str:
        return self._created_at

    @property
    def updated_at_(self) -> str:
        return self._updated_at

    @staticmethod
    def from_row(row: dict) -> "Envelope":
        return Envelope(
            id=row["id"],
            workflow_id=row["workflow_id"],
            parent_envelope_id=row["parent_envelope_id"],
            correlation_id=row["correlation_id"],
            sender_node_id=row["sender_node_id"],
            receiver_node_id=row["receiver_node_id"],
            source_role=row["source_role"],
            target_role=row["target_role"],
            sequence_id=row["sequence_id"],
            step=row["step"],
            status=EnvelopeStatus(row["status"]),
            stage=EnvelopeStage(row["stage"]),
            payload_json=row["payload_json"],
            artifact_uri=row["artifact_uri"],
            archive_uri=row["archive_uri"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
