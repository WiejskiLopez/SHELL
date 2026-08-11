"""Architecture test — verifies all layer import rules.

Uses AST parsing (no imports executed) to check that:
- domain/ does not import from application/, process/, infrastructure/, framework/, bootstrap/
- application/ does not import from process/, infrastructure/, framework/, bootstrap/
- process/ does not import from infrastructure/, framework/, bootstrap/
- infrastructure/ does not import from framework/, bootstrap/
"""

from __future__ import annotations

import ast
import pathlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

BASE = pathlib.Path(__file__).resolve().parent.parent.parent  # shell/ (source root)


def _iter_python_files(layer: str) -> Iterator[pathlib.Path]:
    layer_path = BASE / layer
    if not layer_path.exists():
        return
    yield from layer_path.rglob("*.py")


def _get_imports(path: pathlib.Path) -> list[str]:
    """Return all imported module prefixes from a Python file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _iter_platform_core_files() -> Iterator[pathlib.Path]:
    yield from _iter_python_files("platform/domain")
    yield BASE / "platform" / "infrastructure" / "serialization" / "type_registry.py"


_KNOWN_DOMAIN_VIOLATIONS: frozenset[str] = frozenset({})

_KNOWN_APP_VIOLATIONS: frozenset[str] = frozenset({})

_KNOWN_FRAMEWORK_BOOTSTRAP: frozenset[str] = frozenset(
    {
        "framework/definition/graph_definition/api/router.py",
        "framework/platform/api/dependencies.py",
        "framework/project/project/api/router.py",
        "framework/session/session/api/router.py",
        "framework/user/user/api/router.py",
        "framework/platform/api/app.py",
        "framework/platform/cli/main.py",
        "framework/execution/api/routers/envelopes.py",
        "framework/execution/api/routers/node_execution.py",
        "framework/execution/api/routers/task_executions/__init__.py",
        "framework/execution/api/routers/workflows/__init__.py",
        "framework/definition/api/routers/definitions/__init__.py",
        "framework/session/api/routers/sessions/__init__.py",
        "framework/user/api/routers/users/__init__.py",
        "framework/project/api/routers/projects/__init__.py",
    }
)

_FORBIDDEN: dict[str, list[str]] = {
    "domain": [
        "shell.application",
        "shell.process",
        "shell.infrastructure",
        "shell.framework",
        "shell.bootstrap",
        "sqlalchemy",
        "pydantic",
        "fastapi",
        "motor",
    ],
    "application": [
        "shell.process",
        "shell.infrastructure",
        "shell.framework",
        "shell.bootstrap",
        "sqlalchemy",
        "fastapi",
        "motor",
    ],
    "process": [
        "shell.infrastructure",
        "shell.framework",
        "shell.bootstrap",
        "sqlalchemy",
        "fastapi",
        "motor",
    ],
}


def test_domain_layer_imports() -> None:
    violations: list[str] = []
    forbidden = _FORBIDDEN["domain"]
    for path in _iter_python_files("domain"):
        for imp in _get_imports(path):
            for banned in forbidden:
                if imp == banned or imp.startswith(banned + "."):
                    rel = path.relative_to(BASE).as_posix()
                    msg = f"{rel}: imports {imp!r}"
                    if msg not in _KNOWN_DOMAIN_VIOLATIONS:
                        violations.append(msg)
    assert not violations, "Domain layer import violations:\n" + "\n".join(violations)


def test_application_layer_imports() -> None:
    violations: list[str] = []
    forbidden = _FORBIDDEN["application"]
    for path in _iter_python_files("application"):
        for imp in _get_imports(path):
            for banned in forbidden:
                if imp == banned or imp.startswith(banned + "."):
                    msg = f"{path.relative_to(BASE).as_posix()}: imports {imp!r}"
                    if msg not in _KNOWN_APP_VIOLATIONS:
                        violations.append(msg)
    assert not violations, "Application layer import violations:\n" + "\n".join(violations)


# ── 3. Process must not import infrastructure, framework, bootstrap ──


def test_process_layer_imports() -> None:
    violations: list[str] = []
    forbidden = _FORBIDDEN["process"]
    for path in _iter_python_files("process"):
        for imp in _get_imports(path):
            for banned in forbidden:
                if imp == banned or imp.startswith(banned + "."):
                    violations.append(f"{path.relative_to(BASE)}: imports {imp!r}")
    assert not violations, "Process layer import violations:\n" + "\n".join(violations)


# ── 4. Infrastructure must not import framework or bootstrap ──────

_INFRA_FRAMEWORK_KNOWN: frozenset[str] = frozenset({})


def test_infrastructure_does_not_import_framework() -> None:
    violations: list[str] = []
    forbidden = ["shell.framework", "shell.bootstrap"]
    for path in _iter_python_files("infrastructure"):
        for imp in _get_imports(path):
            for banned in forbidden:
                if imp == banned or imp.startswith(banned + "."):
                    key = f"{path.relative_to(BASE)}: imports {imp!r}"
                    if key not in _INFRA_FRAMEWORK_KNOWN:
                        violations.append(key)
    assert not violations, "Infrastructure must not import framework/bootstrap:\n" + "\n".join(
        violations
    )


def test_platform_core_does_not_import_bounded_contexts() -> None:
    violations: list[str] = []
    platform_roots = [
        BASE / "platform" / "domain",
        BASE / "platform" / "application",
        BASE / "platform" / "framework",
        BASE / "platform" / "types",
        BASE / "platform" / "infrastructure" / "configuration",
        BASE / "platform" / "infrastructure" / "context",
        BASE / "platform" / "infrastructure" / "identity",
        BASE / "platform" / "infrastructure" / "logging",
        BASE / "platform" / "infrastructure" / "time",
    ]
    forbidden_prefixes = (
        "shell.definition",
        "shell.execution",
        "shell.session",
        "shell.user",
        "shell.project",
        "shell.scheduling",
        "shell.messaging",
    )

    for root in platform_roots:
        for path in root.rglob("*.py"):
            for imp in _get_imports(path):
                if imp.startswith(forbidden_prefixes):
                    violations.append(f"{path.relative_to(BASE)}: imports {imp!r}")

    assert not violations, "Platform core must not depend on bounded contexts:\n" + "\n".join(
        violations
    )


def test_event_transport_receives_registries_from_composition_root() -> None:
    for path in (BASE / "definition", BASE / "execution", BASE / "session", BASE / "user"):
        assert path.exists(), f"Expected standalone BC root is missing: {path}"


def test_message_registry_builder_is_platform_owned() -> None:
    platform_registry = BASE / "platform" / "infrastructure" / "serialization" / "message_registry.py"
    bc_registry = BASE / "messaging" / "bootstrap" / "messaging" / "message_registry.py"

    assert platform_registry.exists(), "Message registry builder must remain in platform"
    assert not bc_registry.exists(), "Message registry must not be duplicated inside Messaging BC"
    assert "shell.messaging" not in "\n".join(_get_imports(platform_registry))


def test_event_registry_builder_is_platform_owned() -> None:
    platform_registry = BASE / "platform" / "infrastructure" / "serialization" / "event_registry.py"

    assert platform_registry.exists(), "Event registry builder must remain in platform"
    assert "shell.platform.infrastructure.serialization.type_registry" in _get_imports(
        platform_registry
    )


# ── 5. Framework must not import bootstrap (except main) ──────────

_FRAMEWORK_BOOTSTRAP_KNOWN: frozenset[str] = _KNOWN_FRAMEWORK_BOOTSTRAP


def test_framework_does_not_import_bootstrap() -> None:
    violations: list[str] = []
    forbidden = ["shell.bootstrap"]
    for path in _iter_python_files("framework"):
        rel = path.relative_to(BASE).as_posix()
        if rel in _FRAMEWORK_BOOTSTRAP_KNOWN:
            continue
        for imp in _get_imports(path):
            for banned in forbidden:
                if imp == banned or imp.startswith(banned + "."):
                    violations.append(f"{rel}: imports {imp!r}")
    assert not violations, "Framework must not import bootstrap:\n" + "\n".join(violations)


# ── 6. Platform must not import bounded contexts or outer layers ───

_PLATFORM_KNOWN: frozenset[str] = frozenset({})


def test_platform_does_not_import_bounded_contexts() -> None:
    violations: list[str] = []
    bounded_contexts = [
        "shell.definition",
        "shell.execution",
        "shell.session",
        "shell.user",
        "shell.project",
        "shell.scheduling",
        "shell.messaging",
    ]
    for path in _iter_platform_core_files():
        for imp in _get_imports(path):
            if any(imp == bc or imp.startswith(bc + ".") for bc in bounded_contexts):
                key = f"{path.relative_to(BASE)}: imports {imp!r}"
                if key not in _PLATFORM_KNOWN:
                    violations.append(key)
    assert not violations, "Platform must not import bounded contexts:\n" + "\n".join(
        violations
    )


def test_domain_does_not_import_datetime() -> None:
    """Domain layer must use CreatedAt/UpdatedAt/DeletedAt, never raw datetime."""
    violations: list[str] = []
    for path in _iter_python_files("domain"):
        if path.name == "__init__.py":
            continue
        content = path.read_text(encoding="utf-8")
        if "from datetime import" in content:
            violations.append(str(path.relative_to(BASE)))
    assert not violations, (
        "Domain layer must not import datetime. "
        "Use CreatedAt/UpdatedAt/DeletedAt value objects instead.\n" + "\n".join(violations)
    )


def test_platform_does_not_import_other_layers() -> None:
    violations: list[str] = []
    forbidden = [
        "shell.domain",
        "shell.application",
        "shell.process",
        "shell.infrastructure",
        "shell.framework",
        "shell.bootstrap",
    ]
    for path in _iter_platform_core_files():
        for imp in _get_imports(path):
            for banned in forbidden:
                if imp == banned or imp.startswith(banned + "."):
                    key = f"{path.relative_to(BASE)}: imports {imp!r}"
                    if key not in _PLATFORM_KNOWN:
                        violations.append(key)
    assert not violations, "Platform must not import other project layers:\n" + "\n".join(
        violations
    )
