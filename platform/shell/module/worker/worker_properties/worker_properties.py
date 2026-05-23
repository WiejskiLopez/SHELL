"""WorkerProperties — placeholder for future worker execution parameters."""

from __future__ import annotations

_VALID_TYPES: frozenset[str] = frozenset({'script', 'process', 'python_module'})


class WorkerProperties:
    """Holds Worker runtime parameters extracted from YAML config."""

    __slots__ = ("_app",)

    def __init__(self, app) -> None:
        self._app = app

    def init_worker_properties(self) -> None:
        app_properties = self._app.app_properties_
        if app_properties.type_ not in _VALID_TYPES:
            raise ValueError(
                f"Invalid worker type: {app_properties.type_!r}. Must be one of {sorted(_VALID_TYPES)}"
            )
        if not app_properties.command_:
            raise ValueError("config.yaml missing required field: 'command'")
