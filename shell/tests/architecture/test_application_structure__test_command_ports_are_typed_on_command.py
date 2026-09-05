"""Koncept: CommandBus i CommandDeliveryDispatcher przyjmują komendy jako Command.

Reguła: sygnatury ``dispatch`` w ``CommandBus`` i ``CommandDeliveryDispatcher``
używają typu ``Command`` (albo ``type[Command]`` w ``register``), a NIE
``object``/``Any``/``typing.Any``. Dzięki temu myPy odrzuca wrzucenie
nie-komendy (query/event) do brama komend.

Poprawnie: parametry dispatch/register są adnotowane ``Command`` lub
``type[Command]``.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    parse_file,
)

_TARGETS = (
    (
        "platform/application/bus/command_bus.py",
        {
            "dispatch": {"command"},
            "register": {"command_type"},
        },
    ),
    (
        "../packaging/saga-orchestration/saga_orchestration/process/saga/ports/command_delivery_dispatcher.py",
        {
            "dispatch": {"command"},
        },
    ),
)


def _annotation_uses_command(annotation: ast.AST | None) -> bool:
    if annotation is None:
        return False
    return "Command" in ast.unparse(annotation)


def _is_bad_annotation(annotation: ast.AST) -> bool:
    unparsed = ast.unparse(annotation)
    return unparsed in {"object", "Any", "typing.Any"}


def test_command_ports_are_typed_on_command() -> None:
    violations: list[str] = []
    for rel, method_params in _TARGETS:
        path = BASE / rel
        tree = parse_file(path)
        if tree is None:
            violations.append(f"{rel}: nie można sparsować")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            params = method_params.get(node.name)
            if params is None:
                continue
            arg_names = {arg.arg for arg in node.args.args}
            for param in params:
                if param not in arg_names:
                    violations.append(f"{rel}: parametr {param!r} w {node.name} nie istnieje")
                    continue
                arg = next(a for a in node.args.args if a.arg == param)
                if arg.annotation is None:
                    violations.append(f"{rel}: {node.name}({param}) bez adnotacji typu")
                elif _is_bad_annotation(arg.annotation) or not _annotation_uses_command(
                    arg.annotation
                ):
                    violations.append(
                        f"{rel}: {node.name}({param}) typowany jako "
                        f"{ast.unparse(arg.annotation)} zamiast Command"
                    )
    assert not violations, architecture_assertion_message(
        "test_command_ports_are_typed_on_command",
        "CommandBus/CommandDeliveryDispatcher przyjmują Command a nie object/Any",
        violations,
    )
