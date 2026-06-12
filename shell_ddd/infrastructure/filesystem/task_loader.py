"""FileSystemTaskLoader — reads task.md + task.yaml from the filesystem."""
from __future__ import annotations

import asyncio
from asyncio import to_thread
from pathlib import Path


class FileSystemTaskLoader:
    """Reads task markdown asynchronously (via thread pool)."""

    async def load(self, md_path: str) -> str:
        return await to_thread(
            Path(md_path).read_text,
            encoding="utf-8",
        )
