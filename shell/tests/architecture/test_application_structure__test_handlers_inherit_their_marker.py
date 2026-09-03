"""Koncept: komendy i handlery komend/eventów dziedziczą po znacznikach.

Reguła: handlery w ``application/.../command_handlers`` dziedziczą po
platformowym ``CommandHandler``, handlery w ``application/.../event_handlers``
po ``EventHandler``. Znaczniki �yj� w ``platform/application/command_handlers`` oraz ``event_handlers``
i mogą być używane generycznie (``CommandHandler[X]``).

Poprawnie: ``class XHandler(CommandHandler[XCommand])`` /
``class XHandler(EventHandler[XEvent])``.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    iter_named_dirs,
    iter_py_files,
    parse_file,
)

_EXPECTED_BASE = {
    "command_handlers": "CommandHandler",
    "event_handlers": "EventHandler",
}

_MARKER_BASE_FILES = frozenset(
    {
        "platform/application/command_handlers/command_handler.py",
        "platform/application/event_handlers/event_handler.py",
    }
)


def _base_names(node: ast.ClassDef) -> set[str]:
    """Zbiera nazwy klas bazowych, rozwija ``Generic[X]`` do ``Generic``."""
    names: set[str] = set()
    for base in node.bases:
        if isinstance(base, ast.Name):
            names.add(base.id)
        elif isinstance(base, ast.Subscript) and isinstance(base.value, ast.Name):
            names.add(base.value.id)
    return names


def test_handlers_inherit_their_marker() -> None:
    violations: list[str] = []
    for handler_kind, expected_base in _EXPECTED_BASE.items():
        for handler_dir in iter_named_dirs("application", handler_kind):
            for path in iter_py_files(handler_dir):
                if path.relative_to(BASE).as_posix() in _MARKER_BASE_FILES:
                    continue
                tree = parse_file(path)
                if tree is None:
                    continue
                for node in find_classes(tree):
                    if not node.name.endswith("Handler"):
                        continue
                    if expected_base not in _base_names(node):
                        violations.append(
                            f"{path.relative_to(BASE)}: {node.name} nie dziedziczy po "
                            f"{expected_base}"
                        )
    assert not violations, architecture_assertion_message(
        "test_handlers_inherit_their_marker",
        "command handlers → CommandHandler, event handlers → EventHandler",
        violations,
    )
