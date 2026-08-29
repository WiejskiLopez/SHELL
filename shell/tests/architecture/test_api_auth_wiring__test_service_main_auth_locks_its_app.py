"""Koncept: architektoniczna reguła auth wiring — fabryki app są zamykane kluczem.

Reguła: każdy serwis w ``bootstrap/*/main.py`` przekazuje ``api_key`` do fabryki
``create_*_app`` i nigdy nie wywołuje jej z pustym literałem ``api_key=""``.

Poprawnie: ``main.py`` wiąże klucz z środowiska/konfiguracji w factory; pusty klucz
jest dozwolony wyłącznie w testach, nigdy w production entrypoint.
"""

from __future__ import annotations

import ast

from _arch_helpers import BASE, architecture_assertion_message


def _app_factory_calls(tree: ast.Module) -> list[tuple[ast.Call, str]]:
    calls: list[tuple[ast.Call, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name.startswith("create_") and name.endswith("app"):
                calls.append((node, name))
    return calls


def test_every_service_main_auth_locks_its_app() -> None:
    main_files = tuple(BASE.glob("*_service/bootstrap/*/main.py"))
    assert len(main_files) == 7

    violations: list[str] = []
    for path in main_files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = _app_factory_calls(tree)
        if not calls:
            violations.append(f"{path}: no create_*_app call found")
            continue
        for call, name in calls:
            keyword_values = {
                keyword.arg: keyword.value for keyword in call.keywords if keyword.arg is not None
            }
            api_key_value = keyword_values.get("api_key")
            if api_key_value is None:
                violations.append(f"{path}: {name} called without api_key=")
            elif (
                isinstance(api_key_value, ast.Constant)
                and isinstance(api_key_value.value, str)
                and api_key_value.value == ""
            ):
                violations.append(f"{path}: {name} called with empty api_key literal")

    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_every_service_main_auth_locks_its_app",
        "warunek zapisany w asercji musi być spełniony",
        "Every service main.py must pass a non-empty api_key to create_*_app:\n"
        + "\n".join(violations),
    )
