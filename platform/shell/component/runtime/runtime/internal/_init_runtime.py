from __future__ import annotations

from typing import TYPE_CHECKING

from shell.utils.system.system import System
from shell.component.runtime.runtime.internal._init_manifest import _init_manifest
from shell.component.runtime.runtime.internal._init_runtime_config import _init_runtime_config

if TYPE_CHECKING:
    from shell.component.runtime.runtime.runtime import Runtime


def _init_runtime(runtime: Runtime, version_info: tuple[int, ...] | None = None) -> None:
    System().validate(version_info=version_info)
    _init_runtime_config(runtime)
    _init_manifest(runtime)
