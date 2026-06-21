from __future__ import annotations

from shell.infrastructure.execution.filesystem.envelope_archive_fs import FileSystemEnvelopeArchive


class TestFileSystemEnvelopeArchive:
    async def test_archive_writes_json_file(self, tmp_path: object) -> None:
        from datetime import UTC, datetime

        from shell.domain.execution.aggregates.envelope import Envelope
        from shell.domain.execution.value_objects.ids import (
            EnvelopeId,
            GraphNodeExecutionId,
            WorkflowId,
        )

        archive = FileSystemEnvelopeArchive(str(tmp_path))
        now = datetime.now(tz=UTC)
        envelope = Envelope.new(
            id_=EnvelopeId("env-arch-1"),
            workflow_id=WorkflowId("wf-arch-1"),
            sender_graph_node_execution_id=GraphNodeExecutionId("node-s"),
            receiver_graph_node_execution_id=GraphNodeExecutionId("node-r"),
            source_role="agent",
            target_role="worker",
            now=now,
        )
        uri = await archive.archive(envelope)
        assert uri.startswith("fs://archive/wf-arch-1/env-arch-1")

        import json
        import pathlib

        stored = json.loads(
            (pathlib.Path(str(tmp_path)) / "wf-arch-1" / "env-arch-1.json").read_text()
        )
        assert stored["id"] == "env-arch-1"
        assert stored["workflow_id"] == "wf-arch-1"
