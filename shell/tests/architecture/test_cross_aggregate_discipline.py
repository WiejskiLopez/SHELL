"""Architecture test — cross-aggregate / cross-BC repository discipline.

Rule (microservices-in-a-monolith):
  A handler in bounded context X must NOT use unit_of_work.repository() to
  access a repository that belongs to bounded context Y (X != Y).

  Cross-BC data access must go through an injected port (Protocol) defined
  in the domain layer of the *consuming* BC, implemented by an HTTP adapter
  in infrastructure/ — never through another BC's repository.

  Query handlers must not access any repository via UnitOfWork at all;
  they use QueryService only.

  Process (saga) handlers that inject repositories directly must also only
  inject repositories from their own BC.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from _arch_helpers import BASE, find_classes, iter_py_files, parse_file

if TYPE_CHECKING:
    import pathlib

# ──────────────────────────────────────────────────────────────────────
# 1.  Repository → Bounded Context  mapping
# ──────────────────────────────────────────────────────────────────────

_REPO_TO_BC: dict[str, str] = {}
"""Maps every domain repository class name to its owning BC,
e.g. "WorkflowRepository" → "execution"."""


def _build_repo_to_bc_map() -> dict[str, str]:
    """Scan shell/domain/* for repository Protocols and return {name → bc}."""
    if _REPO_TO_BC:
        return _REPO_TO_BC

    domain = BASE / "domain"
    if not domain.is_dir():
        return _REPO_TO_BC

    for bc_dir in sorted(domain.iterdir()):
        if not bc_dir.is_dir() or bc_dir.name.startswith("_"):
            continue
        bc_name = bc_dir.name
        for repos_dir in bc_dir.rglob("repositories"):
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
                        and node.name not in _REPO_TO_BC
                    ):
                        _REPO_TO_BC[node.name] = bc_name
    return _REPO_TO_BC


# ──────────────────────────────────────────────────────────────────────
# 2.  Helpers
# ──────────────────────────────────────────────────────────────────────


def _handler_bc(path: pathlib.Path) -> str | None:
    """Derive the BC for a handler from its filesystem path.

    Rules:
      application/<bc>/...          → <bc>
      process/<bc>/...              → <bc>
    """
    rel = path.relative_to(BASE).as_posix()
    parts = rel.split("/")
    if len(parts) >= 2 and parts[0] in ("application", "process"):
        return parts[1]
    return None


def _find_repo_calls_in_tree(tree: ast.Module) -> list[str]:
    """Return every repository name used via unit_of_work.repository(Name)."""
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "repository":
            continue
        val = node.func.value
        is_uow = (isinstance(val, ast.Name) and val.id in ("unit_of_work", "uow")) or (
            isinstance(val, ast.Attribute)
            and isinstance(val.value, ast.Name)
            and val.value.id == "self"
            and val.attr in ("_unit_of_work", "_uow")
        )
        if is_uow and node.args and isinstance(node.args[0], ast.Name):
            found.append(node.args[0].id)
    return found


def _find_repo_injected_in_init(tree: ast.Module) -> list[str]:
    """Check __init__ parameters with type-hints that reference a known
    domain repository and return those repository names."""
    known_repos = _build_repo_to_bc_map()
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
        if left and right:
            return left  # take first for union types
        return left or right
    return None


# ──────────────────────────────────────────────────────────────────────
# 3.  Known-violations allowlist
#     Entries are removed one-by-one as the violations are refactored.
# ──────────────────────────────────────────────────────────────────────


def _violation_key(path: pathlib.Path, repo: str) -> str:
    rel = path.relative_to(BASE).as_posix()
    return f"{rel}:{repo}"


# ──────────────────────────────────────────────────────────────────────
# 4.  Tests
# ──────────────────────────────────────────────────────────────────────


def _test_handlers_in_dir(handler_dir: pathlib.Path, *, check_repo_injection: bool = False) -> None:
    """Shared logic: walk all .py files in *handler_dir*, find handlers
    that use unit_of_work.repository() or have repos injected, and
    assert they never access repos from another BC.

    If *check_repo_injection* is True, also inspect __init__ parameters
    for direct repository injections (process/saga handlers).
    """
    repo_bc = _build_repo_to_bc_map()
    violations: list[str] = []

    if not handler_dir.exists():
        return

    for path in iter_py_files(handler_dir):
        tree = parse_file(path)
        if tree is None:
            continue

        bc = _handler_bc(path)
        if bc is None:
            continue

        # ── Pattern A: unit_of_work.repository(XxxRepo) ──────────
        used_repos = _find_repo_calls_in_tree(tree)

        # ── Pattern B: direct injection via __init__ param ───────
        if check_repo_injection:
            used_repos.extend(_find_repo_injected_in_init(tree))

        for repo_name in set(used_repos):
            owning_bc = repo_bc.get(repo_name)
            if owning_bc is None:
                continue  # unknown repo, skip
            if owning_bc == bc:
                continue  # same BC — allowed
            if owning_bc == "platform":
                continue  # platform repos are shared
            key = _violation_key(path, repo_name)
            violations.append(f"{key}  (handler BC={bc!r}, repo BC={owning_bc!r})")

    assert not violations, (
        "Handlers must not access repositories from other bounded contexts "
        "via unit_of_work.repository() or direct injection. "
        "Use a port (Protocol) in domain/ports/ + HTTP adapter instead.\n" + "\n".join(violations)
    )


# ── 4a. Command handlers ─────────────────────────────────────────────


def test_command_handlers_dont_use_cross_bc_repos() -> None:
    _test_handlers_in_dir(BASE / "application" / "command_handlers")


# ── 4b. Event handlers ───────────────────────────────────────────────


def test_event_handlers_dont_use_cross_bc_repos() -> None:
    _test_handlers_in_dir(BASE / "application" / "event_handlers")


# ── 4c. Process (saga) handlers ──────────────────────────────────────


def test_process_handlers_dont_use_cross_bc_repos() -> None:
    _test_handlers_in_dir(BASE / "process", check_repo_injection=True)


# ── 4d. Query handlers — must NOT use unit_of_work at all ────────────


def test_query_handlers_dont_use_unit_of_work() -> None:
    """Query handlers must use QueryService, never unit_of_work.repository()."""
    dirs = [
        BASE / "application" / "query_handlers",
    ]
    violations: list[str] = []

    for d in dirs:
        if not d.exists():
            continue
        for path in iter_py_files(d):
            tree = parse_file(path)
            if tree is None:
                continue
            if _find_repo_calls_in_tree(tree):
                rel = path.relative_to(BASE).as_posix()
                violations.append(rel)

    assert not violations, (
        "Query handlers must NOT use unit_of_work.repository(). "
        "Use QueryService instead.\n" + "\n".join(violations)
    )
