"""placeholders.py
Placeholders — utility class for replacing $$name$$ tokens in prompt text.

Slots:
    _app              — parent App
    _placeholder_list — list of (placeholder, value) tuples
"""

from __future__ import annotations

from shell.component.placeholders.internal._add_placeholder import _add_placeholder
from shell.component.placeholders.internal._apply import _apply
from shell.component.placeholders.internal._assert_no_unresolved_placeholders import _assert_no_unresolved_placeholders
from shell.component.placeholders.internal._bind_dict import _bind_dict
from shell.component.placeholders.internal._bind_slots import _bind_slots
from shell.component.placeholders.internal._set_placeholder import _set_placeholder
from shell.component.placeholders.internal._wrap import _wrap


class Placeholders:
    """Holds a list of placeholder→value pairs and applies them to prompt text."""

    __slots__ = ("_app", "_placeholder_list")

    def __init__(self, app) -> None:
        self._app = app
        self._placeholder_list: list[tuple[str, str]] = []

    @property
    def placeholder_list_(self) -> list[tuple[str, str]]:
        return self._placeholder_list

    def add_placeholder(self, name: str, value: str) -> None:
        _add_placeholder(self, name, value)

    def bind_slots(self, obj) -> None:
        _bind_slots(self, obj)

    def bind_dict(self, config_dict: dict) -> None:
        _bind_dict(self, config_dict)

    def set_placeholder(self, name: str, value: str) -> None:
        _set_placeholder(self, name, value)

    def apply(self, text: str) -> str:
        return _apply(self, text)

    def assert_no_unresolved(self, text: str) -> None:
        _assert_no_unresolved_placeholders(text)

    def wrap(self, text: str) -> str:
        return _wrap(self, text)
