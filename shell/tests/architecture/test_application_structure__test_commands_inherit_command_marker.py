"""Koncept: wszystkie komendy dziedziczą po wspólnym znaczniku Command.

Reguła: kazda klasa komendy w katalogu ``application/.../commands`` ma w
definicji klas bazowych ``Command`` (platformowy supertyp znacznikowy).

Poprawnie: kazda komenda deklaruje ``class XxxCommand(Command)`` i importuje
znacznik z ``shell.platform.application.commands``.
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

_MARKER_BASE_FILES = frozenset(
    {
        "platform/application/commands/command.py",
    }
)


def _has_command_base(node: ast.ClassDef) -> bool:
    return any(isinstance(base, ast.Name) and base.id == "Command" for base in node.bases)


def test_all_commands_inherit_command_marker() -> None:
    violations: list[str] = []
    for cmd_dir in iter_named_dirs("application", "commands"):
        for path in iter_py_files(cmd_dir):
            if path.relative_to(BASE).as_posix() in _MARKER_BASE_FILES:
                continue
            tree = parse_file(path)
            if tree is None:
                continue
            for node in find_classes(tree):
                if not node.name.endswith("Command"):
                    continue
                if not _has_command_base(node):
                    violations.append(f"{path.relative_to(BASE)}: {node.name}")
    assert not violations, architecture_assertion_message(
        "test_all_commands_inherit_command_marker",
        "komenda dziedziczy po znaczniku Command",
        violations,
    )
