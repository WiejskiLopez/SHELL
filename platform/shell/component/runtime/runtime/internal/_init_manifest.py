from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.component.runtime.runtime.runtime import Runtime


def _init_manifest(runtime: Runtime) -> None:
    runtime.manifest_.init_manifest()
