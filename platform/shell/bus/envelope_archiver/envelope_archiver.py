"""envelope_archiver.py
EnvelopeArchiver — DB-only archiver of finalized envelopes (envelope_archive table).

Slots:
    _node_dir — node directory whose archived envelopes are scoped to
    _bus      — MessageBus instance (driver used to record archive events)
"""

from __future__ import annotations

from datetime import datetime, timezone

from shell.bus.envelope.envelope import Envelope
from shell.bus.envelope_archiver.internal._archive_envelope import _archive_envelope
from shell.bus.message_bus.message_bus import MessageBus
from shell.utils.path.path import PathType


class EnvelopeArchiver:
    """Archives finalized envelopes to the envelope_archive table."""

    __slots__ = ("_node_dir", "_bus")

    def __init__(self) -> None:
        self._node_dir: PathType | None = None
        self._bus: MessageBus | None = None

    @property
    def node_dir_(self) -> PathType:
        return self._node_dir

    @property
    def bus_(self) -> MessageBus:
        return self._bus

    def init_envelope_archiver(self, node_dir: PathType, bus: MessageBus) -> None:
        self._node_dir = node_dir
        self._bus = bus

    def archive_envelope(self, envelope: Envelope) -> None:
        _archive_envelope(self, envelope)
        now = datetime.now(timezone.utc).isoformat()
        self._bus.driver_.execute(
            """
            INSERT INTO envelope_event (envelope_id, event_type, to_value, source, timestamp)
            VALUES (?, 'ARCHIVED', NULL, 'archiver', ?)
            """,
            (envelope.id_, now),
        )
        self._bus.driver_.commit()
