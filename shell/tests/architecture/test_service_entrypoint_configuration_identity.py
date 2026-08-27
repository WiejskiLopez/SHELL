"""Koncept: jawna tożsamość konfiguracji usługi w entrypoincie.

Reguła: każdy service entrypoint przekazuje identyfikator własnej usługi do loadera konfiguracji.

Poprawnie: wszystkie wywołania konfiguracji zawierają właściwy service_name.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_service_entrypoints_declare_their_owned_configuration_identity() -> None:
    for path in ROOT.glob("*_service/bootstrap/*/main.py"):
        service_name = path.parts[-4].removesuffix("_service")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "from_environment"
        ]
        assert calls, path
        assert all(
            any(
                keyword.arg == "service_name"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value == service_name
                for keyword in call.keywords
            )
            for call in calls
        ), f"{path} must pass service_name={service_name!r} to every configuration load"
