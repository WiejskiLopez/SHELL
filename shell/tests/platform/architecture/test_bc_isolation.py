from __future__ import annotations

from _arch_helpers import BASE, get_imports, iter_py_files, parse_file

# Bounded contexts in the project
# NOTE: Only execution and definition are actively enforced.
# Other BCs (scheduling, projekt, user) are still evolving and have known cross-BC deps.
_BCS = frozenset({"execution", "definition"})

# Allowed cross-BC import targets (ports, contracts, DTOs)
_ALLOWED_CROSS_BC = frozenset({
    "shell.domain.platform",
    "shell.application.platform",
})


def _is_cross_bc_import(imp: str, source_bc: str) -> str | None:
    """If imp crosses a BC boundary (is not platform), return the target BC name."""
    for bc in _BCS:
        if bc == source_bc or bc == "platform":
            continue
        if imp.startswith(f"shell.domain.{bc}") or imp.startswith(f"shell.application.{bc}"):
            return bc
    return None


def _is_allowed_cross_bc(imp: str) -> bool:
    for allowed in _ALLOWED_CROSS_BC:
        if imp == allowed or imp.startswith(allowed + "."):
            return True
    return False


# ── 1. No direct cross-BC imports ────────────────────────────────


_CROSS_BC_KNOWN_VIOLATIONS: list[str] = [
    # execution -> definition via ports (acceptable pattern - port in one BC, adapter in another)
    "domain/execution/ports/runner_config_provider.py: imports 'shell.domain.definition.",
    # execution -> definition via handlers and strategies
    "application/execution/event_handlers/: imports 'shell.domain.definition.",
    "application/execution/strategies/: imports 'shell.domain.definition.",
    # execution -> definition via application mappers  
    "application/platform/mappers/mappers.py: imports 'shell.domain.definition.",
    # definition -> execution via entities
    "domain/definition/entities/graph_node_transition_definition.py: imports 'shell.domain.execution.",
    # platform -> execution/definition (acceptable - platform is shared)
    "domain/platform/ports/identity.py: imports 'shell.domain.execution.",
    "domain/platform/ports/identity.py: imports 'shell.domain.definition.",
    "domain/platform/services/: imports 'shell.domain.execution.",
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
