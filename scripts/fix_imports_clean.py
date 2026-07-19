#!/usr/bin/env python3
"""Move DeletedAt/UpdatedAt from TYPE_CHECKING to runtime imports.

Only modifies the specific files where DeletedAt/UpdatedAt is imported
under TYPE_CHECKING but used at runtime (as default values or constructor calls).
"""

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "shell"

# Files where DeletedAt is in TYPE_CHECKING but used at runtime
FILES_DELETED = [
    "domain/definition/aggregates/runner_config/runner_config.py",
    "domain/execution/aggregates/edge_execution/edge_execution.py",
    "domain/execution/aggregates/edge_link_execution/edge_link_execution.py",
    "domain/execution/aggregates/graph_execution/graph_execution.py",
    "domain/execution/aggregates/graph_execution_state/graph_execution_state.py",
    "domain/execution/aggregates/session_execution/session_execution.py",
    "domain/execution/aggregates/session_execution_state/session_execution_state.py",
    "domain/execution/aggregates/task_execution/task_execution.py",
    "domain/execution/aggregates/task_execution_state/task_execution_state.py",
    "domain/execution/aggregates/user_execution/user_execution.py",
    "domain/execution/aggregates/user_execution_state/user_execution_state.py",
    "domain/execution/aggregates/workflow/workflow.py",
    "domain/execution/aggregates/workflow_state/workflow_state.py",
    "domain/project/aggregates/project/project.py",
    "domain/project/aggregates/project_skill/project_skill.py",
    "domain/project/aggregates/project_state/project_state.py",
    "domain/session/aggregates/session/session.py",
    "domain/session/aggregates/session_state/session_state.py",
    "domain/user/aggregates/user/user.py",
    "domain/user/aggregates/user_skill/user_skill.py",
    "domain/user/aggregates/user_state/user_state.py",
]

# Files where UpdatedAt is in TYPE_CHECKING but used at runtime  
FILES_UPDATED = [
    "domain/definition/aggregates/runner_config/runner_config.py",
]

def process_file(relpath: str) -> bool:
    fpath = BASE / relpath
    if not fpath.exists():
        print(f"  NOT FOUND: {relpath}")
        return False
    
    content = fpath.read_text(encoding="utf-8")
    original = content
    modified = False
    
    for name, mod, filenames in [
        ("DeletedAt", "deleted_at", FILES_DELETED),
        ("UpdatedAt", "updated_at", FILES_UPDATED)
    ]:
        if relpath not in filenames:
            continue
        
        # Check if name is already imported at runtime
        before_tc = content[:content.find("if TYPE_CHECKING:")] if "if TYPE_CHECKING:" in content else content
        if f"from shell.platform.domain.value_objects.{mod} import {name}" in before_tc:
            continue
        
        # Find ALL TYPE_CHECKING blocks
        for tc_match in list(re.finditer(r'if TYPE_CHECKING:\n(  .*\n)*', content)):
            tc_block = tc_match.group()
            tc_start = tc_match.start()
            tc_end = tc_match.end()
            
            if name not in tc_block:
                continue
            
            # Remove import from this TYPE_CHECKING block
            single = f"    from shell.platform.domain.value_objects.{mod} import {name}"
            if single in tc_block:
                new_tc = tc_block.replace(single + "\n", "")
                new_tc = new_tc.replace(single, "")
                content = content[:tc_start] + new_tc + content[tc_end:]
                modified = True
                break
            else:
                # Try multi-line: 
                multi_start = f"    from shell.platform.domain.value_objects.{mod} import ("
                if multi_start in tc_block:
                    tc_lines = tc_block.split("\n")
                    new_lines = []
                    skip = 0
                    for line in tc_lines:
                        if skip > 0:
                            skip -= 1
                            continue
                        if multi_start in line:
                            skip = 1
                            for j in range(tc_lines.index(line) + 1, len(tc_lines)):
                                if ")" in tc_lines[j]:
                                    break
                                skip += 1
                            continue
                        new_lines.append(line)
                    new_tc = "\n".join(new_lines)
                    content = content[:tc_start] + new_tc + content[tc_end:]
                    modified = True
                    break
    
    if modified:
        # Add runtime import after last runtime import but before TYPE_CHECKING
        insert_pos = content.find("if TYPE_CHECKING:")
        before = content[:insert_pos]
        last_import = list(re.finditer(r'^from .*\n', before, re.MULTILINE))
        if last_import:
            insert_pos = last_import[-1].end()
        
        for name, mod in [("DeletedAt", "deleted_at"), ("UpdatedAt", "updated_at")]:
            if relpath in (FILES_DELETED if name == "DeletedAt" else FILES_UPDATED):
                import_line = f"from shell.platform.domain.value_objects.{mod} import {name}\n"
                if import_line not in content:
                    content = content[:insert_pos] + import_line + content[insert_pos:]
                    insert_pos += len(import_line)
    
    if content != original:
        fpath.write_text(content, encoding="utf-8")
        return True
    return False

for relpath in sorted(set(FILES_DELETED + FILES_UPDATED)):
    if process_file(relpath):
        print(f"Fixed: {relpath}")

print("Done!")
