#!/usr/bin/env python
"""Fix all 7 syntax errors from merged annotations."""
from pathlib import Path

# Fix merged annotations: CreatedAtdef -> CreatedAt\n    def
files = [
    "shell/domain/execution/aggregates/agent_execution/agent_execution.py",
    "shell/domain/execution/aggregates/edge_execution/edge_execution.py",
    "shell/domain/execution/aggregates/graph_execution/graph_execution.py",
    "shell/domain/execution/aggregates/session_execution/session_execution.py",
    "shell/domain/execution/aggregates/task_execution/task_execution.py",
    "shell/domain/execution/aggregates/user_execution/user_execution.py",
    "shell/domain/user/aggregates/user/user.py",
]

for path_str in files:
    fp = Path(path_str)
    c = fp.read_text("utf-8")
    orig = c
    
    # Fix CreatedAt merged with next word
    c = c.replace("CreatedAtdef ", "CreatedAt\n    def ")
    c = c.replace("CreatedAtclass", "CreatedAt\nclass")
    c = c.replace("CreatedAt@", "CreatedAt\n@")
    c = c.replace("CreatedAt_updated_at", "CreatedAt\n    _updated_at")
    c = c.replace("UpdatedAtdef ", "UpdatedAt\n    def ")
    c = c.replace("DeletedAtdef ", "DeletedAt\n    def ")
    
    if c != orig:
        fp.write_text(c, "utf-8")
        print(f"FIXED: {path_str}")

# Fix parameter ordering for files that still have issues
for path_str in files:
    fp = Path(path_str)
    c = fp.read_text("utf-8")
    orig = c

    # Move created_at before first optional param in __init__
    if "def __init__(" in c:
        c = c.replace(
            ",\n        created_at: CreatedAt,\n        target_node_execution_id: NodeExecutionId | None = None,\n        updated_at: UpdatedAt | None = None,"
            if "target_node_execution_id: NodeExecutionId | None = None,\n        updated_at: UpdatedAt | None = None,\n        created_at: CreatedAt" in c
            else "TOKEN_THAT_DOESNT_EXIST",
            "TEMP_MARKER",
        )
    
    if c != orig:
        fp.write_text(c, "utf-8")

print("\nDone")
