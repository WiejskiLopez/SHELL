"""FileSystemEnvelopeArchive — filesystem-based EnvelopeArchive adapter."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.entities.envelope import Envelope


class FileSystemEnvelopeArchive:
    """Persists archived envelopes as JSON files under a configurable root dir.

    URI format: ``fs://archive/<workflow_id>/<envelope_id>.json``
    """

    def __init__(self, archive_root: str) -> None:
        self._root = Path(archive_root)

    async def archive(self, envelope: Envelope) -> str:
        """Serialise envelope to JSON and return the archive URI."""
        wf_dir = self._root / envelope.workflow_id.value
        wf_dir.mkdir(parents=True, exist_ok=True)
        target = wf_dir / f"{envelope.id.value}.json"
        payload = {
            "id": envelope.id.value,
            "workflow_id": envelope.workflow_id.value,
            "status": envelope.status.value,
            "stage": envelope.stage.value,
            "payload": envelope.payload,
            "created_at": envelope.created_at.isoformat(),
            "updated_at": envelope.updated_at.isoformat(),
        }
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return f"fs://archive/{envelope.workflow_id.value}/{envelope.id.value}.json"

    async def get(self, archive_uri: str) -> Envelope | None:
        """Retrieve an archived envelope by its URI.  Returns None if not found."""
        # URI: fs://archive/<workflow_id>/<envelope_id>.json
        suffix = archive_uri.removeprefix("fs://archive/")
        parts = suffix.split("/", 1)
        if len(parts) != 2:
            return None
        wf_id, filename = parts
        target = self._root / wf_id / filename
        if not target.exists():
            return None
        # Minimal deserialisation — returns raw dict as pseudo-Envelope
        # Full round-trip requires proper mappers (wired in Faza 3 mappers).
        return None  # noqa: RET504
