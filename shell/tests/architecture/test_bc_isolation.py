from __future__ import annotations

from typing import TYPE_CHECKING

from _arch_helpers import BASE, get_imports, iter_py_files

if TYPE_CHECKING:
    import pathlib

# Bounded contexts in the project
# Known violations are listed in _CROSS_BC_KNOWN_VIOLATIONS.
# Fix them one by one — each should eventually be resolved via IdRef or platform VOs.
_BCS = frozenset(
    {
        "execution_service",
        "definition_service",
        "session_service",
        "user_service",
        "project_service",
        "scheduling_service",
        "ingestion_service",
    }
)

# Allowed cross-BC import targets (ports, contracts, DTOs)
_ALLOWED_CROSS_BC = frozenset(
    {
        "shell.platform.domain",
        "shell.platform.application",
        # Source-owned integration events — designed to be consumed cross-BC
        "shell.user_service.application.user.user.integration_events",
        "shell.user_service.application.user.auth_session.integration_events",
    }
)


def _is_cross_bc_import(imp: str, source_bc: str) -> str | None:
    """If imp crosses a BC boundary (is not platform), return the target BC name."""
    for bc in _BCS:
        if bc == source_bc or bc == "platform":
            continue
        prefixes = (
            f"shell.domain.{bc}",
            f"shell.application.{bc}",
            f"shell.{bc}.domain.{bc}",
            f"shell.{bc}.application.{bc}",
            f"shell.{bc}.",
        )
        if imp.startswith(prefixes):
            return bc
    return None


def _is_allowed_cross_bc(imp: str) -> bool:
    return any(imp == allowed or imp.startswith(allowed + ".") for allowed in _ALLOWED_CROSS_BC)


# ── 1. No direct cross-BC imports ────────────────────────────────


_CROSS_BC_KNOWN_VIOLATIONS: list[str] = []


def _bc_source_path(bc: str) -> pathlib.Path:
    """Return the source tree owned by a bounded context."""
    return BASE / bc


def _cross_bc_violations() -> list[str]:
    violations: list[str] = []
    for source_bc in _BCS:
        source_path = _bc_source_path(source_bc)
        if not source_path.exists():
            continue
        for path in iter_py_files(source_path):
            for imp in get_imports(path):
                target_bc = _is_cross_bc_import(imp, source_bc)
                if target_bc is None or _is_allowed_cross_bc(imp):
                    continue
                key = f"{path.relative_to(BASE).as_posix()}: imports {imp!r} (from BC {target_bc})"
                if not any(key.startswith(k) for k in _CROSS_BC_KNOWN_VIOLATIONS):
                    violations.append(key)
    return violations


def test_no_direct_cross_bc_imports() -> None:
    """No BC may import implementation code from another BC in any layer."""
    violations = _cross_bc_violations()
    assert not violations, (
        "Bounded contexts must not import each other directly in domain, application, "
        "process, infrastructure, framework, or per-BC bootstrap (use HTTP/event contracts):\n"
        + "\n".join(violations)
    )


# ── 2. Infrastructure adapter is the only known cross-BC bridge ───


def test_cross_bc_imports_only_in_infrastructure() -> None:
    """Keep the legacy rule name while checking every BC-owned layer."""
    violations = _cross_bc_violations()
    assert not violations, (
        "Cross-BC dependencies must use public HTTP/event contracts, not implementation imports:\n"
        + "\n".join(violations)
    )


# ── 3. Cross-BC infrastructure adapters must use HTTP (not SQL/repos) ─


def test_cross_bc_http_adapters_use_httpx_not_sql() -> None:
    """All cross-BC HTTP adapter files must import httpx and must NOT
    import persistence.sql or domain repositories from other BCs."""
    http_adapter_dirs = [
        BASE / "infrastructure" / "execution" / "http",
        BASE / "user" / "infrastructure" / "user" / "http",
        BASE / "infrastructure" / "project" / "http",
    ]
    violations: list[str] = []
    for adapter_dir in http_adapter_dirs:
        if not adapter_dir.exists():
            continue
        for path in iter_py_files(adapter_dir):
            rel = path.relative_to(BASE).as_posix()
            imports = get_imports(path)
            if not any("httpx" in imp for imp in imports):
                violations.append(f"{rel}: missing httpx import")
            for imp in imports:
                if "persistence.sql" in imp:
                    violations.append(f"{rel}: imports SQL persistence {imp!r}")
                if ".repositories." in imp:
                    violations.append(f"{rel}: imports repositories {imp!r}")
    assert not violations, (
        "Cross-BC HTTP adapters must use httpx, not SQL/repositories:\n" + "\n".join(violations)
    )
