#!/usr/bin/env python
"""Fix ALL remaining syntax and parameter ordering issues at once."""

from pathlib import Path
import re

# Fix merged annotations
for f in Path("shell/domain").rglob("**/*.py"):
    c = f.read_text("utf-8")
    orig = c
    c = c.replace("CreatedAt_updated_at", "CreatedAt\n    _updated_at")
    c = c.replace("CreatedAtdef ", "CreatedAt\n    def ")
    c = c.replace("UpdatedAtdef ", "UpdatedAt\n    def ")
    c = c.replace("DeletedAtdef ", "DeletedAt\n    def ")
    c = c.replace("CreatedAtclass", "CreatedAt\nclass")
    if c != orig:
        f.write_text(c, encoding="utf-8")
        print(f"MERGED: {f}")

# Fix parameter ordering - move created_at before optional params
fixes = {
    "shell/domain/execution/aggregates/edge_execution/edge_execution.py": [
        (
            "target_node_execution_id: NodeExecutionId | None = None,\n        created_at: CreatedAt,",
            "created_at: CreatedAt,\n        target_node_execution_id: NodeExecutionId | None = None,",
        ),
    ],
    "shell/domain/execution/aggregates/graph_execution/graph_execution.py": [
        (
            "parent_graph_execution_id: GraphExecutionId | None = None,\n        graph_definition_id: GraphDefinitionIdRef | None = None,\n        created_at: CreatedAt,",
            "created_at: CreatedAt,\n        parent_graph_execution_id: GraphExecutionId | None = None,\n        graph_definition_id: GraphDefinitionIdRef | None = None,",
        ),
    ],
}

for path_str, pairs in fixes.items():
    fp = Path(path_str)
    c = fp.read_text("utf-8")
    orig = c
    for old, new in pairs:
        c = c.replace(old, new)
    if c != orig:
        fp.write_text(c, encoding="utf-8")
        print(f"ORDER: {path_str}")

print("\nDone")
