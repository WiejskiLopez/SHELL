from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import yaml

from shell.bus.envelope.envelope import Envelope

if TYPE_CHECKING:
    from shell.bus.envelope_archiver.envelope_archiver import EnvelopeArchiver


def _archive_envelope(archiver: EnvelopeArchiver, envelope: Envelope) -> None:
    frontmatter = {
        "envelope_id": envelope.id_,
        "workflow_id": envelope.workflow_id_,
        "parent_envelope_id": envelope.parent_envelope_id_,
        "correlation_id": envelope.correlation_id_,
        "sender_node_id": envelope.sender_node_id_,
        "receiver_node_id": envelope.receiver_node_id_,
        "source_role": envelope.source_role_,
        "target_role": envelope.target_role_,
        "sequence_id": envelope.sequence_id_,
        "step": envelope.step_,
        "status": envelope.status_.value,
        "stage": envelope.stage_.value,
        "created_at": envelope.created_at_,
        "updated_at": envelope.updated_at_,
        "artifact_uri": envelope.artifact_uri_,
    }
    frontmatter_yaml = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False).rstrip()
    archived_at = datetime.now(timezone.utc).isoformat()
    archiver.bus_.driver_.execute(
        "INSERT INTO envelope_archive "
        "(envelope_id, workflow_id, sequence_id, sender_node_id, receiver_node_id, "
        " status, stage, payload_json, frontmatter_yaml, archive_uri, archived_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            envelope.id_,
            envelope.workflow_id_,
            envelope.sequence_id_,
            envelope.sender_node_id_,
            envelope.receiver_node_id_,
            envelope.status_.value,
            envelope.stage_.value,
            envelope.payload_json_,
            frontmatter_yaml,
            None,
            archived_at,
        ),
    )
    archiver.bus_.driver_.commit()
