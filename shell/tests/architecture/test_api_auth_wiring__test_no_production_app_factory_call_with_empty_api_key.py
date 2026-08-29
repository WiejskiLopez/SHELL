"""Koncept: zakaz budowania produkcyjnej aplikacji z pustym kluczem API.

Reguła: żadna produkcyjna fabryka w ``shell/platform`` lub ``shell/*_service``
nie może wywoływać ``create_*_app`` z literalnym ``api_key=""``. Pusty klucz jest
sygnałem otwartego API; taki przepływ dozwolony jest wyłącznie w testach.

Poprawnie: wszystkie produkcyjne wywołania fabryk app przekazują klucz z
konfiguracji/środowiska, a nie pusty literał.
"""

from __future__ import annotations

import ast

from _arch_helpers import BASE, architecture_assertion_message

SERVICE_ROOTS = (BASE / "platform", *sorted(BASE.glob("*_service")))


def _app_factory_calls(tree: ast.Module) -> list[tuple[ast.Call, str]]:
    calls: list[tuple[ast.Call, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name.startswith("create_") and name.endswith("app"):
                calls.append((node, name))
    return calls


def test_no_production_app_factory_call_with_empty_api_key() -> None:
    violations: list[str] = []
    for root in SERVICE_ROOTS:
        for path in root.rglob("*.py"):
            if "tests" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for call, name in _app_factory_calls(tree):
                for keyword in call.keywords:
                    if keyword.arg != "api_key":
                        continue
                    if (
                        isinstance(keyword.value, ast.Constant)
                        and isinstance(keyword.value.value, str)
                        and keyword.value.value == ""
                    ):
                        violations.append(f'{path}: {name} called with api_key=""')

    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_no_production_app_factory_call_with_empty_api_key",
        "warunek zapisany w asercji musi być spełniony",
        "Production code must never build an app with an empty api_key literal:\n"
        + "\n".join(violations),
    )
