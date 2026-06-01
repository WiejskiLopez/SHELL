from __future__ import annotations

import json
from typing import TYPE_CHECKING

import yaml

from shell.bus.envelope.envelope import Envelope
from shell.constants.constants import DIR_ARCHIVE, DOT_NODE
from shell.utils.path.path import Path, PathType

if TYPE_CHECKING:
    from shell.bus.envelope_archiver.envelope_archiver import EnvelopeArchiver


def _archive_envelope(archiver: EnvelopeArchiver, envelope: Envelope) -> PathType:
    archive_dir = archiver.node_dir_ / DOT_NODE / DIR_ARCHIVE
    if not Path.exists(archive_dir):
        Path.mkdir(archive_dir)
    filename = f"{envelope.sequence_id_:06d}__{envelope.status_.value}__{envelope.id_}.md"
    archive_path = archive_dir / filename
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
    body_lines = [
        "---",
        yaml.dump(frontmatter, allow_unicode=True, sort_keys=False).rstrip(),
        "---",
        "",
    ]
    try:
        payload_obj = json.loads(envelope.payload_json_)
        body_lines.append("```json")
        body_lines.append(json.dumps(payload_obj, ensure_ascii=False, indent=2))
        body_lines.append("```")
    except (ValueError, TypeError):
        body_lines.append(envelope.payload_json_)
    Path.write_text(archive_path, "\n".join(body_lines))
    return archive_path
