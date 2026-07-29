from __future__ import annotations

from _arch_helpers import BASE, get_imports, iter_py_files

# Bounded contexts in the project
# Known violations are listed in _CROSS_BC_KNOWN_VIOLATIONS.
# Fix them one by one — each should eventually be resolved via IdRef or platform VOs.
_BCS = frozenset(
    {"execution", "definition", "session", "user", "project", "scheduling", "messaging"}
)

# Allowed cross-BC import targets (ports, contracts, DTOs)
_ALLOWED_CROSS_BC = frozenset(
    {
        "shell.platform.domain",
        "shell.platform.application",
        # Source-owned integration events — designed to be consumed cross-BC
        "shell.application.user.user.integration_events",
    }
)


def _is_cross_bc_import(imp: str, source_bc: str) -> str | None:
    """If imp crosses a BC boundary (is not platform), return the target BC name."""
    for bc in _BCS:
        if bc == source_bc or bc == "platform":
            continue
        if imp.startswith(f"shell.domain.{bc}") or imp.startswith(f"shell.application.{bc}"):
            return bc
    return None


def _is_allowed_cross_bc(imp: str) -> bool:
    return any(imp == allowed or imp.startswith(allowed + ".") for allowed in _ALLOWED_CROSS_BC)


# ── 1. No direct cross-BC imports ────────────────────────────────


_CROSS_BC_KNOWN_VIOLATIONS: list[str] = [
    # SessionDto cross-BC reference — port owned by execution BC, DTO owned by session BC.
    # Infrastructure adapter (HTTP) bridges the boundary at runtime.
    "application/execution/session_execution/ports/session_query_service.py",
    "application/execution/session_execution/query_handlers/get_session_history_handler.py",
]


def test_no_direct_cross_bc_imports() -> None:
    violations: list[str] = []
    for bc in _BCS:
        for layer in ["domain", "application"]:
            bc_path = BASE / layer / bc
            if not bc_path.exists():
                continue
            for path in iter_py_files(bc_path):
                for imp in get_imports(path):
                    target_bc = _is_cross_bc_import(imp, bc)
                    if target_bc is not None and not _is_allowed_cross_bc(imp):
                        key = f"{path.relative_to(BASE).as_posix()}: imports {imp!r} (from BC {target_bc})"
                        if not any(key.startswith(k) for k in _CROSS_BC_KNOWN_VIOLATIONS):
                            violations.append(key)
    assert not violations, (
        "Bounded contexts must not import each other directly (use platform contracts/ports):\n"
        + "\n".join(violations)
    )


# ── 2. Infrastructure adapter is the only known cross-BC bridge ───


def test_cross_bc_imports_only_in_infrastructure() -> None:
    violations: list[str] = []
    for bc in _BCS:
        for layer in ["domain", "application"]:
            bc_path = BASE / layer / bc
            if not bc_path.exists():
                continue
            for path in iter_py_files(bc_path):
                for imp in get_imports(path):
                    target_bc = _is_cross_bc_import(imp, bc)
                    if target_bc is not None and not _is_allowed_cross_bc(imp):
                        key = f"{path.relative_to(BASE).as_posix()}: imports {imp!r} (from BC {target_bc})"
                        if not any(key.startswith(k) for k in _CROSS_BC_KNOWN_VIOLATIONS):
                            violations.append(key)
    assert not violations, (
        "Cross-BC imports should live in infrastructure adapters, not in domain/application:\n"
        + "\n".join(violations)
    )


# ── 3. Cross-BC infrastructure adapters must use HTTP (not SQL/repos) ─


def test_cross_bc_http_adapters_use_httpx_not_sql() -> None:
    """All cross-BC HTTP adapter files must import httpx and must NOT
    import persistence.sql or domain repositories from other BCs."""
    http_adapter_dirs = [
        BASE / "infrastructure" / "execution" / "http",
        BASE / "infrastructure" / "user" / "http",
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
