#!/usr/bin/env python3
"""Move DeletedAt from TYPE_CHECKING to runtime imports in specific files."""

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "shell"

files = {
    "domain/definition/aggregates/runner_config/runner_config.py": ("DeletedAt", "UpdatedAt"),
    "domain/execution/aggregates/edge_execution/edge_execution.py": ("DeletedAt",),  # already fixed
    "domain/execution/aggregates/edge_link_execution/edge_link_execution.py": ("DeletedAt",),
    "domain/execution/aggregates/graph_execution/graph_execution.py": ("DeletedAt",),
    "domain/execution/aggregates/graph_execution_state/graph_execution_state.py": ("DeletedAt",),
    "domain/execution/aggregates/session_execution/session_execution.py": ("DeletedAt",),
    "domain/execution/aggregates/session_execution_state/session_execution_state.py": ("DeletedAt",),
    "domain/execution/aggregates/task_execution/task_execution.py": ("DeletedAt",),
    "domain/execution/aggregates/task_execution_state/task_execution_state.py": ("DeletedAt",),
    "domain/execution/aggregates/user_execution/user_execution.py": ("DeletedAt",),
    "domain/execution/aggregates/user_execution_state/user_execution_state.py": ("DeletedAt",),
    "domain/execution/aggregates/workflow/workflow.py": ("DeletedAt",),
    "domain/execution/aggregates/workflow_state/workflow_state.py": ("DeletedAt",),
    "domain/project/aggregates/project/project.py": ("DeletedAt",),
    "domain/project/aggregates/project_skill/project_skill.py": ("DeletedAt",),
    "domain/project/aggregates/project_state/project_state.py": ("DeletedAt",),
    "domain/session/aggregates/session/session.py": ("DeletedAt",),
    "domain/session/aggregates/session_state/session_state.py": ("DeletedAt",),
    "domain/user/aggregates/user/user.py": ("DeletedAt",),
    "domain/user/aggregates/user_skill/user_skill.py": ("DeletedAt",),
    "domain/user/aggregates/user_state/user_state.py": ("DeletedAt",),
}

def move_import(content: str, name: str, mod: str) -> str:
    """Move `from ... import name` from TYPE_CHECKING to runtime. Returns modified content."""
    # For each TYPE_CHECKING block, try to remove the import
    while True:
        tc_match = re.search(r'if TYPE_CHECKING:\n(  .*\n)*', content)
        if not tc_match:
            break
        tc_block = tc_match.group()
        if name not in tc_block:
            break
        
        # Check if name already imported at runtime
        before = content[:tc_match.start()]
        if f"from shell.platform.domain.value_objects.{mod} import {name}" in before:
            break
        
        # Single-line import
        single = f"    from shell.platform.domain.value_objects.{mod} import {name}"
        if single in tc_block:
            new_tc = tc_block.replace(single + "\n", "")
            new_tc = new_tc.replace(single, "")
            content = content[:tc_match.start()] + new_tc + content[tc_match.end():]
            # Add runtime import
            insert_pos = content.find("if TYPE_CHECKING:")
            if insert_pos < 0:
                insert_pos = 0
            before_insert = content[:insert_pos]
            last_import = list(re.finditer(r'^from .*\n', before_insert, re.MULTILINE))
            pos = last_import[-1].end() if last_import else 0
            content = content[:pos] + f"from shell.platform.domain.value_objects.{mod} import {name}\n" + content[pos:]
            return content
        
        # Multi-line import
        multi = f"    from shell.platform.domain.value_objects.{mod} import ("
        if multi in tc_block:
            tc_lines = tc_block.split("\n")
            new_lines = []
            skip = 0
            in_multi = False
            for line in tc_lines:
                if skip > 0:
                    skip -= 1
                    continue
                if multi in line:
                    in_multi = True
                    skip = 0
                    for j in range(tc_lines.index(line) + 1, len(tc_lines)):
                        if ")" in tc_lines[j]:
                            break
                        skip += 1
                    continue
                new_lines.append(line)
            new_tc = "\n".join(new_lines)
            content = content[:tc_match.start()] + new_tc + content[tc_match.end():]
            # Add runtime import
            insert_pos = content.find("if TYPE_CHECKING:")
            if insert_pos < 0:
                insert_pos = 0
            before_insert = content[:insert_pos]
            last_import = list(re.finditer(r'^from .*\n', before_insert, re.MULTILINE))
            pos = last_import[-1].end() if last_import else 0
            content = content[:pos] + f"from shell.platform.domain.value_objects.{mod} import {name}\n" + content[pos:]
            return content
        
        break  # No pattern found
    return content

for relpath, names in files.items():
    fpath = BASE / relpath
    if not fpath.exists():
        print(f"NOT FOUND: {relpath}")
        continue
    
    content = fpath.read_text(encoding="utf-8")
    original = content
    
    for name in names:
        mod = "deleted_at" if name == "DeletedAt" else "updated_at"
        content = move_import(content, name, mod)
    
    if content != original:
        fpath.write_text(content, encoding="utf-8")
        print(f"Fixed: {relpath}")

print("Done!")
