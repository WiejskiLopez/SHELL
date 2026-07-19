#!/usr/bin/env python3
"""Move DeletedAt/UpdatedAt from TYPE_CHECKING to runtime where used in runtime code."""

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "shell"

files_need_deleted_at = [
    "domain/definition/aggregates/runner_config/runner_config.py",
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

files_need_updated_at = [
    "domain/definition/aggregates/runner_config/runner_config.py",
]

all_files = set(files_need_deleted_at + files_need_updated_at)

for relpath in sorted(all_files):
    fpath = BASE / relpath
    if not fpath.exists():
        print(f"NOT FOUND: {relpath}")
        continue
    content = fpath.read_text(encoding="utf-8")
    original = content

    for name, mod in [("DeletedAt", "deleted_at"), ("UpdatedAt", "updated_at")]:
        if relpath not in (files_need_deleted_at if name == "DeletedAt" else files_need_updated_at):
            continue
        
        # Find the TYPE_CHECKING block
        tc_start = content.find("if TYPE_CHECKING:")
        if tc_start < 0:
            continue
        
        # Find end of TYPE_CHECKING block (lines at same/lesser indentation or EOF)
        rest = content[tc_start:]
        lines = rest.split("\n")
        tc_end_idx = len(lines)
        for i in range(1, len(lines)):
            if lines[i] == "" or not lines[i].startswith(" "):
                tc_end_idx = i
                break
        tc_end = tc_start + len("\n".join(lines[:tc_end_idx]))
        tc_block = "\n".join(lines[:tc_end_idx])
        
        if name not in tc_block:
            continue
        
        # Find and remove the import for name from the TYPE_CHECKING block
        # Try single-line pattern first
        single = f"    from shell.platform.domain.value_objects.{mod} import {name}"
        if single in tc_block:
            new_tc = tc_block.replace(single + "\n", "")
            new_tc = new_tc.replace(single, "")
        else:
            # Try multi-line: `    from shell... import (\n        ...\n        DeletedAt,\n    )`
            multi_start = f"    from shell.platform.domain.value_objects.{mod} import ("
            if multi_start in tc_block:
                tc_lines = tc_block.split("\n")
                new_tc_lines = []
                skip = 0
                for line in tc_lines:
                    if skip > 0:
                        skip -= 1
                        continue
                    if multi_start in line:
                        # skip until closing paren
                        skip = 1
                        for j in range(tc_lines.index(line) + 1, len(tc_lines)):
                            if ")" in tc_lines[j]:
                                break
                            skip += 1
                        continue
                    new_tc_lines.append(line)
                new_tc = "\n".join(new_tc_lines)
            else:
                print(f"  {relpath}: Can't find {name} import pattern in TYPE_CHECKING")
                continue
        
        # Reconstruct content with new TC block
        content = content[:tc_start] + new_tc + content[tc_end:]
        
        # Now add runtime import before TYPE_CHECKING
        # Find the last runtime import line before TYPE_CHECKING
        before_tc = content[:content.find("if TYPE_CHECKING:")]
        last_import_end = 0
        for m in re.finditer(r'^from .*\n', before_tc, re.MULTILINE):
            last_import_end = m.end()
        
        if last_import_end == 0:
            # No imports before, so add at the very beginning after __future__
            # Find end of __future__ import or start of file
            first_line_end = content.find("\n") + 1
            last_import_end = first_line_end
        
        import_line = f"from shell.platform.domain.value_objects.{mod} import {name}\n"
        content = content[:last_import_end] + import_line + content[last_import_end:]

    if content != original:
        fpath.write_text(content, encoding="utf-8")
        print(f"Fixed: {relpath}")

print("Done!")
