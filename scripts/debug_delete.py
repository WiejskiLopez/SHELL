#!/usr/bin/env python
"""Debug test logic for _delete method."""

import ast
import sys

sys.path.insert(0, "shell/tests/architecture")
from _arch_helpers import BASE, extends_any_base, find_classes, iter_py_files

AGGREGATE_BASES = {"AggregateRoot"}

for path in iter_py_files(BASE / "domain"):
    tree = ast.parse(path.read_text("utf-8"))
    if not tree:
        continue
    for node in find_classes(tree):
        if not extends_any_base(node, AGGREGATE_BASES):
            continue
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "_delete":
                source = ast.unparse(stmt)
                has_event = "append_event(" in source
                has_deleted = "_deleted_at" in source
                if not has_event or not has_deleted:
                    print(
                        f"{path.relative_to(BASE)}: {node.name}._delete() event={has_event} deleted_at={has_deleted}"
                    )
