#!/usr/bin/env python3
"""Fix remaining multi-line from_datetime patterns in model_to_entity files."""

from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "shell"

files = [
    "infrastructure/execution/edge_execution/persistence/sql/mappers/edge_execution_model_to_entity.py",
    "infrastructure/execution/edge_link_execution/persistence/sql/mappers/edge_link_execution_model_to_entity.py",
    "infrastructure/execution/graph_execution/persistence/sql/mappers/graph_execution_model_to_entity.py",
    "infrastructure/project/project/persistence/sql/mappers/project_model_to_entity.py",
    "infrastructure/project/project_skill/persistence/sql/mappers/project_skill_model_to_entity.py",
    "infrastructure/project/project_state/persistence/sql/mappers/project_state_model_to_entity.py",
    "infrastructure/user/user/persistence/sql/mappers/user_model_to_entity.py",
]

for relpath in files:
    fpath = BASE / relpath
    lines = fpath.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if this line has UpdatedAt.from_datetime( or DeletedAt.from_datetime(
        has_upd = "UpdatedAt.from_datetime(" in line or "DeletedAt.from_datetime(" in line
        has_if = False
        has_else = False
        if has_upd and i + 2 < len(lines):
            has_if = "if " in lines[i+1] and ("updated_at" in lines[i+1] or "deleted_at" in lines[i+1])
            has_else = "else None" in lines[i+2]
        if has_upd and has_if and has_else:
            # Fix: remove trailing whitespace, strip the if/else lines, add comma
            fixed_line = line.rstrip() + ",\n"
            new_lines.append(fixed_line)
            i += 3  # Skip the if and else None lines
        else:
            new_lines.append(line)
            i += 1
    new_content = "".join(new_lines)
    if new_content != fpath.read_text(encoding="utf-8"):
        fpath.write_text(new_content, encoding="utf-8")
        print(f"Fixed: {relpath}")
    else:
        print(f"No change: {relpath}")

print("Done!")
