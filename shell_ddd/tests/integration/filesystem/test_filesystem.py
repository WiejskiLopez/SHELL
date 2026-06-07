"""Integration tests for filesystem infrastructure (NodeWorkspace, TaskLoader, EnvelopeArchive)."""
from __future__ import annotations

import pytest

from shell_ddd.infrastructure.filesystem.node_workspace import NodeWorkspaceFs
from shell_ddd.infrastructure.filesystem.task_loader import FileSystemTaskLoader
from shell_ddd.infrastructure.filesystem.envelope_archive_fs import FileSystemEnvelopeArchive


# ---------------------------------------------------------------------------
# NodeWorkspaceFs
# ---------------------------------------------------------------------------


class TestNodeWorkspaceFs:
    async def test_prepare_creates_dot_node_subdirs(self, tmp_path: object) -> None:
        ws = NodeWorkspaceFs()
        path = await ws.prepare("my-node", str(tmp_path))

        import pathlib
        dot_node = pathlib.Path(path) / ".node"
        assert dot_node.exists()
        for subdir in ["input", "output", "logs", "temp", "prompt"]:
            assert (dot_node / subdir).is_dir(), f".node/{subdir} should be a directory"

    async def test_prepare_returns_workspace_path(self, tmp_path: object) -> None:
        ws = NodeWorkspaceFs()
        path = await ws.prepare("node-abc", str(tmp_path))
        import pathlib
        assert pathlib.Path(path).name == "node-abc"

    async def test_cleanup_removes_workspace(self, tmp_path: object) -> None:
        ws = NodeWorkspaceFs()
        path = await ws.prepare("node-to-clean", str(tmp_path))
        import pathlib
        assert pathlib.Path(path).exists()
        await ws.cleanup(path)
        assert not pathlib.Path(path).exists()

    async def test_write_and_read_output(self, tmp_path: object) -> None:
        ws = NodeWorkspaceFs()
        path = await ws.prepare("node-io", str(tmp_path))
        out = await ws.write_output(path, "result.txt", "hello world")
        import pathlib
        assert pathlib.Path(out).read_text() == "hello world"

    async def test_read_input_missing_returns_empty(self, tmp_path: object) -> None:
        ws = NodeWorkspaceFs()
        path = await ws.prepare("node-empty-input", str(tmp_path))
        content = await ws.read_input(path)
        assert content == ""


# ---------------------------------------------------------------------------
# FileSystemTaskLoader
# ---------------------------------------------------------------------------


class TestFileSystemTaskLoader:
    async def test_load_reads_both_files(self, tmp_path: object) -> None:
        import pathlib
        md = pathlib.Path(str(tmp_path)) / "task.md"
        yaml = pathlib.Path(str(tmp_path)) / "task.yaml"
        md.write_text("# My Task", encoding="utf-8")
        yaml.write_text("graph: []", encoding="utf-8")

        loader = FileSystemTaskLoader()
        body_md = await loader.load(str(md))
        assert body_md == "# My Task"


# ---------------------------------------------------------------------------
# FileSystemEnvelopeArchive
# ---------------------------------------------------------------------------


class TestFileSystemEnvelopeArchive:
    async def test_archive_writes_json_file(self, tmp_path: object) -> None:
        from datetime import UTC, datetime

        from shell_ddd.domain.entities.envelope import Envelope
        from shell_ddd.domain.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
        from shell_ddd.domain.value_objects.ids import EnvelopeId, NodeId, WorkflowId

        archive = FileSystemEnvelopeArchive(str(tmp_path))
        now = datetime.now(tz=UTC)
        envelope = Envelope.new(
            id_=EnvelopeId("env-arch-1"),
            workflow_id=WorkflowId("wf-arch-1"),
            sender_node_id=NodeId("node-s"),
            receiver_node_id=NodeId("node-r"),
            source_role="agent",
            target_role="worker",
            now=now,
        )
        uri = await archive.archive(envelope)
        assert uri.startswith("fs://archive/wf-arch-1/env-arch-1")

        import json, pathlib
        stored = json.loads((pathlib.Path(str(tmp_path)) / "wf-arch-1" / "env-arch-1.json").read_text())
        assert stored["id"] == "env-arch-1"
        assert stored["workflow_id"] == "wf-arch-1"
