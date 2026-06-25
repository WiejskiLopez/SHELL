from __future__ import annotations

import ast

from _arch_helpers import BASE, iter_py_files, parse_file


_KNOWN_MAPPER_EXCEPTIONS: frozenset[str] = frozenset({})


def test_infra_mappers_have_both_directions() -> None:
    violations: list[str] = []
    for mapper_path in (BASE / "infrastructure").rglob("**/mappers/**/*.py"):
        if mapper_path.name == "__init__.py":
            continue
        rel = mapper_path.relative_to(BASE).as_posix()
        if rel in _KNOWN_MAPPER_EXCEPTIONS:
            continue
        tree = parse_file(mapper_path)
        if tree is None:
            continue
        has_to_domain = False
        has_to_model = False
        has_to_entity = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if "to_domain" in node.name:
                    has_to_domain = True
                if "to_model" in node.name:
                    has_to_model = True
                if "to_entity" in node.name:
                    has_to_entity = True
        if not has_to_domain and not has_to_entity:
            violations.append(f"{rel}: missing to_domain/to_entity function")
        if not has_to_model:
            violations.append(f"{rel}: missing to_model function")
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
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.endswith("_to_dto"):
                    has_to_dto = True
                    break
        if not has_to_dto:
            violations.append(f"{mapper_path.relative_to(BASE)}: missing *_to_dto function")
    assert not violations, (
        "Application mappers must have at least a *_to_dto function:\n"
        + "\n".join(violations)
    )


# ── 3. Mapper functions have no business logic (if/elif/else) ─────


def test_mappers_have_no_business_logic() -> None:
    violations: list[str] = []
    for mapper_path in list((BASE / "infrastructure").rglob("**/mappers/**/*.py")) + \
                        list((BASE / "application").rglob("**/mappers/**/*.py")):
        if mapper_path.name == "__init__.py":
            continue
        tree = parse_file(mapper_path)
        if tree is None:
            continue
        content = mapper_path.read_text(encoding="utf-8")
        ast_lines = content.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_lines = set(range(node.lineno or 0, (node.end_lineno or node.lineno) + 1))
                for sub in ast.walk(node):
                    if isinstance(sub, ast.If):
                        test_src = ast.unparse(sub.test)
                        if "==" in test_src or "is" in test_src:
                            line = ast_lines[sub.lineno - 1].strip() if sub.lineno else ""
                            if not any(kw in line for kw in ["None", "is not None", "is None", "isinstance", "type("]):
                                violations.append(
                                    f"{mapper_path.relative_to(BASE)}: {node.name} has business logic at line {sub.lineno}"
                                )
    assert not violations, (
        "Mapper functions should contain no business logic (no if/elif with data checks):\n"
        + "\n".join(violations)
    )
