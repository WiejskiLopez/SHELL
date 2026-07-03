from __future__ import annotations

from shell.infrastructure.execution.filesystem.workspace import Workspace


class TestWorkspace:
    async def test_prepare_creates_dot_node_subdirs(self, tmp_path: object) -> None:
        ws = Workspace()
        path = await ws.prepare("my-node", str(tmp_path))

        dot_node = pathlib.Path(path) / ".node"
        assert dot_node.exists()
        for subdir in ["input", "output", "logs", "temp", "prompt"]:
            assert (dot_node / subdir).is_dir(), f".node/{subdir} should be a directory"

    async def test_prepare_returns_workspace_path(self, tmp_path: object) -> None:
        ws = Workspace()
        path = await ws.prepare("node-abc", str(tmp_path))
        assert pathlib.Path(path).name == "node-abc"

    async def test_cleanup_removes_workspace(self, tmp_path: object) -> None:
        ws = Workspace()
        path = await ws.prepare("node-to-clean", str(tmp_path))
        assert pathlib.Path(path).exists()
        await ws.cleanup(path)
        assert not pathlib.Path(path).exists()

    async def test_write_and_read_output(self, tmp_path: object) -> None:
        ws = Workspace()
        path = await ws.prepare("node-io", str(tmp_path))
        out = await ws.write_output(path, "result.txt", "hello world")
        assert pathlib.Path(out).read_text() == "hello world"

    async def test_read_input_missing_returns_empty(self, tmp_path: object) -> None:
        ws = Workspace()
        path = await ws.prepare("node-empty-input", str(tmp_path))
        content = await ws.read_input(path)
        assert content == ""
