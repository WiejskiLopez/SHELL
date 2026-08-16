"""Koncept: własność seedowania przez Bounded Context.

Reguła: każdy BC musi posiadać własny seed subpakiet
``infrastructure/<bc>/seed/`` z ustalonym publicznym API: ``bootstrap_<bc>_database``,
``seed_<bc>_dev_data`` oraz providerem ``<Bc>SeedProvider`` implementującym
platformowy port ``SeedProvider``.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from _arch_helpers import BASE, architecture_assertion_message

if TYPE_CHECKING:
    import pathlib

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

_BC_DOMAIN_NAME = {
    "user_service": "user",
    "session_service": "session",
    "definition_service": "definition",
    "execution_service": "execution",
    "scheduling_service": "scheduling",
    "project_service": "project",
    "ingestion_service": "ingestion",
}

_BC_PROVIDER_NAME = {
    "user_service": "UserSeedProvider",
    "session_service": "SessionSeedProvider",
    "definition_service": "DefinitionSeedProvider",
    "execution_service": "ExecutionSeedProvider",
    "scheduling_service": "SchedulingSeedProvider",
    "project_service": "ProjectSeedProvider",
    "ingestion_service": "IngestionSeedProvider",
}


def _seed_package_path(bc: str) -> pathlib.Path:
    return BASE / bc / "infrastructure" / _BC_DOMAIN_NAME[bc] / "seed"


def _public_function_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith(
            "_"
        ):
            names.add(node.name)
    return names


def _class_names(tree: ast.Module) -> set[str]:
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def test_every_bc_owns_a_seed_package() -> None:
    violations: list[str] = []
    for bc in _BCS:
        package_init = _seed_package_path(bc) / "__init__.py"
        if not package_init.exists():
            violations.append(f"{bc}: missing seed package {package_init.relative_to(BASE)}")
            continue
        tree = ast.parse(package_init.read_text(encoding="utf-8"))
        expected_functions = {
            f"bootstrap_{_BC_DOMAIN_NAME[bc]}_database",
            f"seed_{_BC_DOMAIN_NAME[bc]}_dev_data",
        }
        missing_functions = expected_functions - _public_function_names(tree)
        for name in sorted(missing_functions):
            violations.append(f"{package_init.relative_to(BASE)}: missing public function {name}")
        if _BC_PROVIDER_NAME[bc] not in _class_names(tree):
            violations.append(
                f"{package_init.relative_to(BASE)}: missing provider {_BC_PROVIDER_NAME[bc]}"
            )
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_every_bc_owns_a_seed_package",
        "każdy BC posiada seed subpakiet z publicznym API i providerem",
        violations,
    )
