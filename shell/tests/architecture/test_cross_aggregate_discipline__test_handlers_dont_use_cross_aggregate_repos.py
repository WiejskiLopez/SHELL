"""Koncept: reguła architektoniczna dotycząca cross aggregate discipline: handlers must not use repositories of other aggregates — even within the same BC.

Reguła: handler może sięgać po repozytorium wyłącznie własnego agregatu. Repozytorium innego
agregatu (także w obrębie tego samego BC) jest dostępne wyłącznie przez port (Protocol) w
`domain/<bc>/aggregates/<aggregate>/ports/` + adapter w infrastrukturze konsumującego agregatu.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

import ast
import pathlib

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    find_classes,
    iter_layer_files,
    parse_file,
)

_REPO_INFO: dict[str, tuple[str, str]] = {}


def _build_repo_info() -> dict[str, tuple[str, str]]:
    """Scan shell/*_service/domain/<bc>/aggregates/<aggregate>/repositories/.

    Returns {repository class name -> (bc, aggregate)}.
    """
    if _REPO_INFO:
        return _REPO_INFO
    for service_dir in BASE.glob("*_service"):
        domain_dir = service_dir / "domain"
        if not domain_dir.is_dir():
            continue
        for bc_dir in domain_dir.iterdir():
            if not bc_dir.is_dir() or bc_dir.name.startswith("_"):
                continue
            aggregates_dir = bc_dir / "aggregates"
            if not aggregates_dir.is_dir():
                continue
            for agg_dir in aggregates_dir.iterdir():
                if not agg_dir.is_dir():
                    continue
                repos_dir = agg_dir / "repositories"
                if not repos_dir.is_dir():
                    continue
                for py_file in repos_dir.rglob("*.py"):
                    if py_file.name == "__init__.py":
                        continue
                    tree = parse_file(py_file)
                    if tree is None:
                        continue
                    for node in ast.walk(tree):
                        if (
                            isinstance(node, ast.ClassDef)
                            and node.name.endswith("Repository")
                            and node.name not in _REPO_INFO
                        ):
                            _REPO_INFO[node.name] = (bc_dir.name, agg_dir.name)
    return _REPO_INFO


def _handler_context(path: pathlib.Path) -> tuple[str | None, str | None]:
    """Derive (bc, aggregate) from `shell/<svc>/application/<bc>/<aggregate>/...`."""
    rel = path.relative_to(BASE).as_posix()
    parts = rel.split("/")
    if len(parts) >= 4 and parts[1] == "application":
        return parts[2], parts[3]
    return None, None


def _find_repo_calls_in_tree(tree: ast.Module) -> list[str]:
    """Return repository names used via `unit_of_work.repository(Name)`."""
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "repository":
            continue
        val = node.func.value
        is_uow = (
            isinstance(val, ast.Name)
            and val.id in ("unit_of_work", "uow")
            or (
                isinstance(val, ast.Attribute)
                and isinstance(val.value, ast.Name)
                and val.value.id == "self"
                and val.attr in ("_unit_of_work", "_uow")
            )
        )
        if is_uow and node.args and isinstance(node.args[0], ast.Name):
            found.append(node.args[0].id)
    return found


def _find_repo_injected_in_init(tree: ast.Module) -> list[str]:
    """Return repository names injected as __init__ parameters."""
    known_repos = _build_repo_info()
    repo_names: list[str] = []
    for class_node in find_classes(tree):
        for stmt in class_node.body:
            if (
                not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
                or stmt.name != "__init__"
            ):
                continue
            for arg in stmt.args.args:
                if arg.arg == "self" or arg.annotation is None:
                    continue
                rname = _extract_name(arg.annotation)
                if rname and rname in known_repos:
                    repo_names.append(rname)
    return repo_names


def _extract_name(annotation: ast.AST) -> str | None:
    """Resolve a type annotation AST node to a simple name."""
    if isinstance(annotation, ast.Name):
        return annotation.id
    if isinstance(annotation, ast.Subscript):
        return _extract_name(annotation.value)
    if isinstance(annotation, ast.Attribute):
        return annotation.attr
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        left = _extract_name(annotation.left)
        right = _extract_name(annotation.right)
        return left or right
    return None


def test_handlers_dont_use_cross_aggregate_repos() -> None:
    repo_info = _build_repo_info()
    violations: list[str] = []
    for path in iter_layer_files("application"):
        if not any(part.endswith("_handlers") for part in path.parts):
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        handler_bc, handler_agg = _handler_context(path)
        if handler_bc is None:
            continue
        used = _find_repo_calls_in_tree(tree)
        used.extend(_find_repo_injected_in_init(tree))
        for repo_name in set(used):
            info = repo_info.get(repo_name)
            if info is None:
                continue
            repo_bc, repo_agg = info
            if repo_bc == "platform":
                continue
            rel = path.relative_to(BASE).as_posix()
            if repo_bc != handler_bc:
                violations.append(
                    f"{rel}:{repo_name}  (handler BC={handler_bc!r}, repo BC={repo_bc!r})"
                )
            elif handler_agg is not None and repo_agg != handler_agg:
                violations.append(
                    f"{rel}:{repo_name}  "
                    f"(handler aggregate={handler_agg!r}, repo aggregate={repo_agg!r}, same BC)"
                )
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_handlers_dont_use_cross_aggregate_repos",
        "handler używa wyłącznie repozytorium własnego agregatu; dane innego agregatu pobiera przez port",
        "Handlers must not access repositories of other aggregates via unit_of_work.repository() or direct injection — including within the same BC. Use a port (Protocol) in domain/<bc>/aggregates/<aggregate>/ports/ + an adapter in infrastructure instead.\n"
        + "\n".join(violations),
    )
