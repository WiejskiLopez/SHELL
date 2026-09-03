"""Koncept: reguła architektoniczna dotycząca application structure: test commands are frozen dataclass.

Reguła: test sprawdza kontrakt architektoniczny application structure: test commands are frozen dataclass.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    is_frozen_dataclass,
    iter_named_dirs,
    iter_py_files,
    parse_file,
)

_KNOWN_HANDLER_EXCEPTIONS: frozenset[str] = frozenset({})
_KNOWN_QUERIES_NOT_FROZEN: frozenset[str] = frozenset({})


_MARKER_BASE_FILES = frozenset(
    {
        "platform/application/commands/command.py",
    }
)


def test_commands_are_frozen_dataclass() -> None:
    violations: list[str] = []
    for cmd_dir in iter_named_dirs("application", "commands"):
        for path in iter_py_files(cmd_dir):
            if path.relative_to(BASE).as_posix() in _MARKER_BASE_FILES:
                continue
            tree = parse_file(path)
            if tree is None:
                continue
            for node in find_classes(tree):
                if not is_frozen_dataclass(node):
                    violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_commands_are_frozen_dataclass",
        "warunek zapisany w asercji musi być spełniony",
        "Commands must be @dataclass(frozen=True):\n" + "\n".join(violations),
    )
