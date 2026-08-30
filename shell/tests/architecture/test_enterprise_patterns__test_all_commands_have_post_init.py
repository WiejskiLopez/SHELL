"""Koncept: reguła architektoniczna dotycząca enterprise patterns: test all commands have post init.

Reguła: test sprawdza kontrakt architektoniczny enterprise patterns: test all commands have post init.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    iter_named_dirs,
    iter_py_files,
    parse_file,
)

_KNOWN_COMMANDS_NO_POST_INIT: frozenset[str] = frozenset({})


def _is_frozen_dataclass(node: ast.ClassDef) -> bool:
    for dec in node.decorator_list:
        if isinstance(dec, ast.Call):
            func = dec.func
            if isinstance(func, ast.Name) and func.id == "dataclass":
                for kw in dec.keywords:
                    if (
                        kw.arg == "frozen"
                        and isinstance(kw.value, ast.Constant)
                        and (kw.value.value is True)
                    ):
                        return True
    return False


def test_all_commands_have_post_init() -> None:
    missing: list[str] = []
    for cmd_dir in iter_named_dirs("application", "commands"):
        for py_file in iter_py_files(cmd_dir):
            tree = parse_file(py_file)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                if not _is_frozen_dataclass(node):
                    continue
                key = f"{py_file.relative_to(BASE).as_posix()}: {node.name}"
                if key in _KNOWN_COMMANDS_NO_POST_INIT:
                    continue
                has_post_init = any(
                    isinstance(m, ast.FunctionDef) and m.name == "__post_init__" for m in node.body
                )
                if not has_post_init:
                    missing.append(f"{py_file.relative_to(BASE)}: {node.name}")
    assert not missing, architecture_assertion_message(
        "reguła testowana przez test_all_commands_have_post_init",
        "warunek zapisany w asercji musi być spełniony",
        "Command dataclasses must define __post_init__:\n" + "\n".join(missing),
    )
