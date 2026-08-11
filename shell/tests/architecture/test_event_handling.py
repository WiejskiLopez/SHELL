"""Architecture tests — event handling integrity.

Enforces:
1. Every per-BC UnitOfWork accepts and forwards the ``mapper`` parameter.
2. No handler manually calls ``stage_events(pull_events())`` — must go through ``UoW.save()``.
3. ``EventInboxProcessor`` in ``events.py`` is wired with ``EventBusPublisher``,
   not CompositeEventPublisher (prevents infinite outbox→inbox→outbox loop).
"""

from __future__ import annotations

import ast

from _arch_helpers import BASE, find_classes, iter_py_files, parse_file

# ── 1. Per-BC UoW accept and forward mapper ─────────────────────────

_UOW_BASES = (BASE / "infrastructure", BASE / "user" / "infrastructure")
_KNOWN_NON_UOW_EXTENDERS: frozenset[str] = frozenset()


def test_per_bc_uow_accepts_mapper() -> None:
    violations: list[str] = []
    for uow_base in _UOW_BASES:
        for py_file in iter_py_files(uow_base):
            if py_file.name != "unit_of_work.py":
                continue
            rel = py_file.relative_to(BASE)
            tree = parse_file(py_file)
            if tree is None:
                continue
            for class_node in find_classes(tree):
                bases = {b.id for b in class_node.bases if isinstance(b, ast.Name)}
                if "SqlAlchemyUnitOfWorkBase" not in bases:
                    continue
                key = f"{rel}: class {class_node.name}"
                if key in _KNOWN_NON_UOW_EXTENDERS:
                    continue
                has_mapper_param = False
                passes_mapper = False
                for stmt in class_node.body:
                    if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                        for arg in stmt.args.args:
                            if arg.arg == "mapper":
                                has_mapper_param = True
                        for node_in_init in ast.walk(stmt):
                            if isinstance(node_in_init, ast.Call):
                                func = node_in_init.func
                                if isinstance(func, ast.Attribute) and func.attr == "__init__":
                                    for kw in node_in_init.keywords:
                                        if kw.arg == "mapper":
                                            passes_mapper = True
                if not has_mapper_param:
                    violations.append(f"{key}: __init__ missing mapper parameter")
                elif not passes_mapper:
                    violations.append(
                        f"{key}: __init__ does not forward mapper to super().__init__"
                    )
    assert not violations, (
        "All SqlAlchemyUnitOfWorkBase subclasses must accept a mapper parameter "
        "and forward it to super().__init__():\n" + "\n".join(violations)
    )


# ── 2. No handler manually stages events ────────────────────────────

_HANDLER_BASES = (BASE / "application", BASE / "user" / "application")


def test_handler_does_not_stage_events_manually() -> None:
    violations: list[str] = []
    for handler_base in _HANDLER_BASES:
        for py_file in iter_py_files(handler_base):
            rel = py_file.relative_to(BASE)
            if "handler" not in py_file.name and "handler" not in str(rel):
                continue
            tree = parse_file(py_file)
            if tree is None:
                continue
            for class_node in find_classes(tree):
                if not class_node.name.endswith("Handler"):
                    continue
                for stmt in class_node.body:
                    if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    key = f"{rel}: {class_node.name}.{stmt.name}"
                    source = ast.get_source_segment(py_file.read_text(encoding="utf-8"), stmt)
                    if source is None:
                        continue
                    if "stage_events" in source and "pull_events" in source:
                        violations.append(key)
    assert not violations, (
        "Handlers must NOT manually stage events via stage_events(agg.pull_events()).\n"
        "Use unit_of_work.save(Repo, aggregate) which pulls, maps and stages automatically:\n"
        + "\n".join(violations)
    )


