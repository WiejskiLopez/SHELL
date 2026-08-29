"""Koncept: fabryki aplikacji BC montują metryki/readiness przez jawny bundle.

Reguła: każde `app.py`, które woła `install_metrics` lub `mount_readiness`,
musi importować `ObservabilityProviders` (jawny frozen bundle), a nie
przekazywać surowego kontenera DI.

Poprawnie: fabryki przekazują do frameworku jawny zestaw providów.
"""

from __future__ import annotations

import ast

from _arch_helpers import BASE, architecture_assertion_message, parse_file

_OBSERVABILITY_PROVIDERS_IMPORT = "shell.platform.observability.framework.api.providers"


def _imports_providers(tree: ast.Module | None) -> bool:
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == _OBSERVABILITY_PROVIDERS_IMPORT:
            return True
    return False


def test_app_factories_use_observability_providers() -> None:
    violations: list[str] = []
    for service_dir in (*BASE.glob("*_service"),):
        for path in sorted((service_dir / "framework").rglob("app.py")):
            source = path.read_text(encoding="utf-8")
            calls_installer = "install_metrics(" in source or "mount_readiness(" in source
            if not calls_installer:
                continue
            if not _imports_providers(parse_file(path)):
                violations.append(str(path))
    assert not violations, architecture_assertion_message(
        "fabryki app.py wołające install_metrics/mount_readiness muszą używać jawnych providerów",
        "import 'shell.platform.observability.framework.api.providers'",
        violations,
    )
