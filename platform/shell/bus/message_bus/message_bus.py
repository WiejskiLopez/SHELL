"""message_bus.py
MessageBus — DB-backed message broker (replaces filesystem stage subdirs).

Slots:
    _driver — SqlDriver (None until init_message_bus)
"""

from __future__ import annotations

from shell.bus.envelope.envelope import Envelope
from shell.bus.envelope.envelope_stage import EnvelopeStage
from shell.bus.envelope.envelope_status import EnvelopeStatus
from shell.bus.message_bus.internal._claim_next import _claim_next
from shell.bus.message_bus.internal._expire_ttl import _expire_ttl
from shell.bus.message_bus.internal._get_active_for_workflow import _get_active_for_workflow
from shell.bus.message_bus.internal._get_envelope import _get_envelope
from shell.bus.message_bus.internal._get_envelope_events import _get_envelope_events
from shell.bus.message_bus.internal._get_history_for_workflow import _get_history_for_workflow
from shell.bus.message_bus.internal._get_pending_for_node import _get_pending_for_node
from shell.bus.message_bus.internal._has_active import _has_active
from shell.bus.message_bus.internal._init_message_bus import _init_message_bus
from shell.bus.message_bus.internal._mark_status import _mark_status
from shell.bus.message_bus.internal._move_to_stage import _move_to_stage
from shell.bus.message_bus.internal._publish_envelope import _publish_envelope
from shell.memory.sql_driver.sql_driver import SqlDriver


class MessageBus:
    """DB-backed message broker."""

    __slots__ = ("_driver",)

    def __init__(self) -> None:
        self._driver: SqlDriver | None = None

    @property
    def driver_(self) -> SqlDriver:
        return self._driver

    def init_message_bus(self, driver: SqlDriver) -> None:
        _init_message_bus(self, driver)

    def publish_envelope(
        self,
        workflow_id: str,
        source_role: str,
        payload: dict,
        parent_envelope_id: int | None = None,
        correlation_id: str | None = None,
        sender_node_id: str | None = None,
        receiver_node_id: str | None = None,
        target_role: str | None = None,
        step: int = 0,
        status: EnvelopeStatus = EnvelopeStatus.REQUESTED,
        stage: EnvelopeStage | None = None,
        artifact_uri: str | None = None,
    ) -> int:
        return _publish_envelope(
            self, workflow_id, source_role, payload, parent_envelope_id, correlation_id,
            sender_node_id, receiver_node_id, target_role, step, status, stage, artifact_uri,
        )

    def claim_next(self, workflow_id: str, receiver_node_id: str) -> Envelope | None:
        return _claim_next(self, workflow_id, receiver_node_id)

    def mark_status(self, envelope_id: int, new_status: EnvelopeStatus, source: str | None = None) -> None:
        _mark_status(self, envelope_id, new_status, source)

    def move_to_stage(
        self,
        envelope_id: int,
        new_stage: EnvelopeStage,
        source: str | None = None,
        reason: str | None = None,
    ) -> None:
        _move_to_stage(self, envelope_id, new_stage, source, reason)

    def expire_ttl(self, workflow_id: str, max_step: int) -> int:
        return _expire_ttl(self, workflow_id, max_step)

    def get_envelope(self, envelope_id: int) -> Envelope | None:
        return _get_envelope(self, envelope_id)

    def get_envelope_events(self, envelope_id: int) -> list[dict]:
        return _get_envelope_events(self, envelope_id)

    def get_pending_for_node(self, workflow_id: str, receiver_node_id: str) -> list[Envelope]:
        return _get_pending_for_node(self, workflow_id, receiver_node_id)

    def get_active_for_workflow(self, workflow_id: str) -> list[Envelope]:
        return _get_active_for_workflow(self, workflow_id)

    def get_history_for_workflow(self, workflow_id: str) -> list[Envelope]:
        return _get_history_for_workflow(self, workflow_id)

    def has_active(self, workflow_id: str) -> bool:
        return _has_active(self, workflow_id)
