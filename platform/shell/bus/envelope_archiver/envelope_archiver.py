"""envelope_archiver.py
EnvelopeArchiver — write-only mirror of finalized envelopes to <node_dir>/.node/archive/.

DB is the source of truth; archive is read-only audit trail for humans.

Slots:
    _node_dir — node directory whose .node/archive/ folder is the target
    _bus      — MessageBus instance (used to update archive_uri)
"""

from __future__ import annotations

from datetime import datetime, timezone

from shell.bus.envelope.envelope import Envelope
from shell.bus.envelope_archiver.internal._archive_envelope import _archive_envelope
from shell.bus.message_bus.message_bus import MessageBus
from shell.utils.path.path import PathType


class EnvelopeArchiver:
    """Writes finalized envelopes to .node/archive/ as audit-only mirror."""

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

    def archive_envelope(self, envelope: Envelope) -> PathType:
        archive_path = _archive_envelope(self, envelope)
        now = datetime.now(timezone.utc).isoformat()
        self._bus.driver_.execute(
            "UPDATE envelope SET archive_uri = ? WHERE id = ?",
            (str(archive_path), envelope.id_),
        )
        self._bus.driver_.execute(
            """
            INSERT INTO envelope_event (envelope_id, event_type, to_value, source, timestamp)
            VALUES (?, 'ARCHIVED', ?, 'archiver', ?)
            """,
            (envelope.id_, str(archive_path), now),
        )
        self._bus.driver_.commit()
        return archive_path
