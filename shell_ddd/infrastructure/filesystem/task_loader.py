"""FileSystemTaskLoader — reads task.md + task.yaml from the filesystem."""
from __future__ import annotations

import asyncio
from pathlib import Path


class FileSystemTaskLoader:
    """Reads task markdown and yaml files asynchronously (via thread pool)."""

    async def load(self, md_path: str, yaml_path: str) -> tuple[str, str]:
        """Return (body_md, body_yaml_raw).  Both paths must exist."""
        loop = asyncio.get_event_loop()
        body_md, body_yaml_raw = await asyncio.gather(
            loop.run_in_executor(None, Path(md_path).read_text, "utf-8"),
            loop.run_in_executor(None, Path(yaml_path).read_text, "utf-8"),
        )
        return body_md, body_yaml_raw
