"""Koncept: warstwa aplikacji nie dispatchuje komend delivery.

Reguła: żaden plik w ``application/`` (platform + BC) nie importuje portu
``CommandDeliveryDispatcher`` ani adapterów outbox komend i nie wywołuje
``.dispatch(..., target_service=...)``. Dispatch komend delivery należy do
warstwy ``process/`` (saga) oraz infra/bootstrap.

Poprawnie: aplikacja publikuje wyłącznie eventy albo dispatchuje lokalnie
przez ``CommandBus``.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    get_imports,
    iter_layer_files,
    parse_file,
)

_FORBIDDEN_IMPORT_PREFIXES = (
    "saga_orchestration.process.saga.ports.command_delivery_dispatcher",
    "shell.platform.infrastructure.messaging.command",
)


def _import_forbidden(imp: str) -> bool:
    return any(
        imp == prefix or imp.startswith(prefix + ".") for prefix in _FORBIDDEN_IMPORT_PREFIXES
    )


def _calls_delivery_dispatch(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "dispatch":
            continue
        if any(kw.arg == "target_service" for kw in node.keywords):
            return True
    return False


def test_application_does_not_dispatch_delivery_commands() -> None:
    violations: list[str] = []
    for path in iter_layer_files("application"):
        tree = parse_file(path)
        if tree is None:
            continue
        rel = path.relative_to(BASE).as_posix()
        for imp in get_imports(path):
            if _import_forbidden(imp):
                violations.append(f"{rel}: import {imp!r}")
        if _calls_delivery_dispatch(tree):
            violations.append(f"{rel}: dispatch(..., target_service=...)")
    assert not violations, architecture_assertion_message(
        "test_application_does_not_dispatch_delivery_commands",
        "application nie używa toru delivery komend (portu/anadapterów ani .dispatch(target_service=...))",
        violations,
    )
