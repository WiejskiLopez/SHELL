"""Koncept: fail-fast na pusty klucz API w każdym production entrypoint.

Reguła: każdy ``bootstrap/*/main.py`` musi obliczyć ``api_key`` i podnieść
``ValueError`` gdy wynik jest pusty — zanim powstanie aplikacja bez autha.

Poprawnie: wszystkie 7 entrypointów posiada rozwiązanie klucza (``api_key =``)
oraz strażnika ``if not api_key: raise ValueError``.
"""

from __future__ import annotations

from _arch_helpers import BASE, architecture_assertion_message


def test_non_empty_api_key_enforced_in_every_service_main() -> None:
    violations: list[str] = []
    for path in tuple(BASE.glob("*_service/bootstrap/*/main.py")):
        content = path.read_text(encoding="utf-8")
        resolves_api_key = "api_key =" in content
        has_fail_fast = "if not api_key:" in content and "raise ValueError" in content
        if not resolves_api_key or not has_fail_fast:
            violations.append(f"{path}: missing api_key resolution or fail-fast")

    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_non_empty_api_key_enforced_in_every_service_main",
        "warunek zapisany w asercji musi być spełniony",
        "Every service main.py must compute api_key and fail fast when empty:\n"
        + "\n".join(violations),
    )
