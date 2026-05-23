"""runtime.py
Runtime — container for runtime-level objects shared across the graph run.

Slots:
    _app                — Optional; App instance
    _manifest           — Optional; Manifest instance
    _runtime_config     — Optional; Config instance
    _runtime_properties — Optional; RuntimeProperties instance
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.component.manifest.manifest import Manifest
from shell.component.config.config.config import Config
from shell.component.runtime.runtime_properties.runtime_properties import RuntimeProperties
from shell.component.runtime.runtime.internal._init_runtime import _init_runtime

if TYPE_CHECKING:
    from shell.app.app.app import App


class Runtime:

    __slots__ = ("_app", "_manifest", "_runtime_config", "_runtime_properties")

    def __init__(self) -> None:
        self._app: App | None = None
        self._manifest: Manifest | None = None
        self._runtime_config: Config | None = None
        self._runtime_properties: RuntimeProperties | None = None

    @property
    def app_(self) -> App:
        return self._app

    @property
    def manifest_(self) -> Manifest:
        if self._manifest is None:
            self._manifest = Manifest(self._app)
        return self._manifest

    @property
    def runtime_config_(self) -> Config:
        if self._runtime_config is None:
            self._runtime_config = Config(self._app)
        return self._runtime_config

    @property
    def runtime_properties_(self) -> RuntimeProperties:
        if self._runtime_properties is None:
            self._runtime_properties = RuntimeProperties(self)
        return self._runtime_properties

    def init_runtime(self, version_info: tuple[int, ...] | None = None) -> None:
        _init_runtime(self, version_info=version_info)

