"""Koncept: dispatch komend delivery występuje wyłącznie w warstwie process.

Reguła: rozgałęzione wywołanie ``.dispatch(..., target_service=...)`` (delivery)
jest dozwolone tylko w plikach warstwy ``process/``, adapterów ``infrastructure/``
i wiringu ``bootstrap/``. Wszędzie indziej (pomijając testy) to naruszenie.

Poprawnie: jedynym producentem komend delivery jest warstwa process (saga);
aplikacja ich nie dispatchuje.
"""

from __future__ import annotations

import ast

from _arch_helpers import (
    BASE,
    SERVICE_ROOTS,
    architecture_assertion_message,
    iter_py_files,
    parse_file,
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


def _allowed_location(rel: str) -> bool:
    return (
        rel.startswith("process/")
        or rel.startswith("platform/process/")
        or "/infrastructure/" in rel
        or "/bootstrap/" in rel
    )


def test_delivery_dispatch_only_from_process() -> None:
    violations: list[str] = []
    for service_root in SERVICE_ROOTS:
        for path in iter_py_files(service_root):
            tree = parse_file(path)
            if tree is None:
                continue
            if not _calls_delivery_dispatch(tree):
                continue
            rel = path.relative_to(BASE).as_posix()
            if not _allowed_location(rel):
                violations.append(f"{rel}: dispatch(..., target_service=...)")
    assert not violations, architecture_assertion_message(
        "test_delivery_dispatch_only_from_process",
        "dispatch delivery tylko w process/infrastructure/bootstrap",
        violations,
    )
