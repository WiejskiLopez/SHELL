"""Koncept: odporność komunikacji HTTP między bounded contexts.

Reguła: adaptery HTTP Execution są składane z odpornego klienta z ograniczonym retry i circuit breakerem.

Poprawnie: composition root używa ResilientAsyncClient dla wszystkich klientów zależności HTTP.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_CONTAINER = (
    ROOT
    / "execution_service"
    / "bootstrap"
    / "execution"
    / "container"
    / "execution_core_container.py"
)


def test_execution_http_clients_use_bounded_resilience_policy() -> None:
    tree = ast.parse(_CONTAINER.read_text(encoding="utf-8"))
    resilient_factories = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "Factory"
        and node.args
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "ResilientAsyncClient"
    ]

    assert len(resilient_factories) == 2
    for client in resilient_factories:
        keyword_names = {keyword.arg for keyword in client.keywords}
        assert {"timeout", "retry_policy", "circuit_breaker_policy"} <= keyword_names

    retry_attempts = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "RetryPolicy"
    ]
    assert len(retry_attempts) == 2
    assert all(
        any(
            keyword.arg == "max_attempts"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == 3
            for keyword in retry_policy.keywords
        )
        for retry_policy in retry_attempts
    )
