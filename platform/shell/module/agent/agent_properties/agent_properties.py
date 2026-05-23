"""Agent execution parameters: model, timeout, retries, retry_delay."""

from __future__ import annotations


class AgentProperties:
    """Holds Agent runtime parameters extracted from YAML config."""

    __slots__ = ("_app", "_model", "_timeout", "_retries", "_retry_delay")

    def __init__(self, app) -> None:
        self._app = app
        self._model: str | None = None
        self._timeout: int | None = None
        self._retries: int | None = None
        self._retry_delay: float | None = None

    @property
    def model_(self) -> str | None:
        """Return the Agent model name."""
        return self._model

    @property
    def timeout_(self) -> int:
        """Return the Agent timeout in seconds (default 300)."""
        return self._timeout if self._timeout is not None else 300

    @property
    def retries_(self) -> int:
        """Return the number of retries (default 0)."""
        return self._retries if self._retries is not None else 0

    @property
    def retry_delay_(self) -> float:
        """Return the delay between retries in seconds (default 2.0)."""
        return float(self._retry_delay) if self._retry_delay is not None else 2.0

    def init_agent_properties(self) -> None:
        app_properties = self._app.app_properties_
        self._model = app_properties.model_
        self._timeout = app_properties.timeout_
        self._retries = app_properties.retries_
