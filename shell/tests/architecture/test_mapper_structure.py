from __future__ import annotations

import ast

from _arch_helpers import BASE, parse_file

_KNOWN_MAPPER_EXCEPTIONS: frozenset[str] = frozenset({})


def test_infra_mappers_have_both_directions() -> None:
    """Each mappers/ directory (as a whole) must have both to_entity and to_model functions.
    Each function is in its own file named after the function (1 function = 1 file)."""
    violations: list[str] = []
    mapper_dirs: dict[str, set[str]] = {}
    for mapper_path in (BASE / "infrastructure").rglob("**/mappers/**/*.py"):
        if mapper_path.name == "__init__.py":
            continue
        rel = mapper_path.relative_to(BASE).as_posix()
        if rel in _KNOWN_MAPPER_EXCEPTIONS:
            continue
        dir_key = str(mapper_path.parent)
        if dir_key not in mapper_dirs:
            mapper_dirs[dir_key] = set()
        tree = parse_file(mapper_path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if "to_domain" in node.name or "to_entity" in node.name:
                    mapper_dirs[dir_key].add("to_entity")
                if "to_model" in node.name:
                    mapper_dirs[dir_key].add("to_model")
    for dir_key, found in mapper_dirs.items():
        rel_dir = dir_key.replace(str(BASE) + "\\", "").replace("\\", "/")
        if "to_entity" not in found:
            violations.append(f"{rel_dir}: missing to_domain/to_entity function")
        if "to_model" not in found:
            violations.append(f"{rel_dir}: missing to_model function")
    assert not violations, (
        "Infrastructure mappers must have both to_domain/to_entity and to_model:\n"
        + "\n".join(violations)
    )


# ── 2. Application mapper has *_to_dto ────────────────────────────


def test_app_mappers_have_to_dto() -> None:
    violations: list[str] = []
    for mapper_path in (BASE / "application").rglob("**/mappers/**/*.py"):
        if mapper_path.name == "__init__.py":
            continue
        tree = parse_file(mapper_path)
        if tree is None:
            continue
        has_to_dto = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.endswith(
                "_to_dto"
            ):
                has_to_dto = True
                break
        if not has_to_dto:
            violations.append(f"{mapper_path.relative_to(BASE)}: missing *_to_dto function")
    assert not violations, (
        "Application mappers must have at least a *_to_dto function:\n" + "\n".join(violations)
    )


# ── 3. Mapper functions have no business logic (if/elif/else) ─────


def test_mappers_have_no_business_logic() -> None:
    violations: list[str] = []
    for mapper_path in list((BASE / "infrastructure").rglob("**/mappers/**/*.py")) + list(
        (BASE / "application").rglob("**/mappers/**/*.py")
    ):
        if mapper_path.name == "__init__.py":
            continue
        tree = parse_file(mapper_path)
        if tree is None:
            continue
        content = mapper_path.read_text(encoding="utf-8")
        ast_lines = content.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for sub in ast.walk(node):
                    if isinstance(sub, ast.If):
                        test_src = ast.unparse(sub.test)
                        if "==" in test_src or "is" in test_src:
                            line = ast_lines[sub.lineno - 1].strip() if sub.lineno else ""
                            if not any(
                                kw in line
                                for kw in ["None", "is not None", "is None", "isinstance", "type("]
                            ):
                                violations.append(
                                    f"{mapper_path.relative_to(BASE)}: {node.name} has business logic at line {sub.lineno}"
                                )
    assert not violations, (
        "Mapper functions should contain no business logic (no if/elif with data checks):\n"
        + "\n".join(violations)
    )
