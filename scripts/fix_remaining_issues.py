#!/usr/bin/env python3
"""Fix remaining issues after option pattern refactor:
1. Move DeletedAt/UpdatedAt from TYPE_CHECKING to runtime imports
2. Fix _deleted_at is not None -> _deleted_at.value is not None
3. Fix empty TYPE_CHECKING blocks by adding 'pass'
"""

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "shell"

files_need_runtime_import = {
    "DeletedAt": [
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
    ],
    "UpdatedAt": [
        "domain/definition/aggregates/runner_config/runner_config.py",
    ],
}

def move_import_to_runtime(content: str, name: str, mod: str) -> str:
    """Move an import from TYPE_CHECKING to runtime. Returns modified content."""
    tc_match = re.search(r'if TYPE_CHECKING:\n(  .*\n)*', content)
    if not tc_match:
        return content
    tc_block = tc_match.group()
    if name not in tc_block:
        return content
    
    # Check runtime usage
    runtime = content[:tc_match.start()] + content[tc_match.end():]
    if not re.search(rf'{name}\s*[\(\.]', runtime) and not re.search(rf'=\s*{name}\b', runtime):
        return content
    
    # Remove import from TYPE_CHECKING
    single = f"    from shell.platform.domain.value_objects.{mod} import {name}"
    if single in tc_block:
        new_tc = tc_block.replace(single + "\n", "")
        new_tc = new_tc.replace(single, "")
    else:
        multi_start = f"    from shell.platform.domain.value_objects.{mod} import ("
        if multi_start in tc_block:
            tc_lines = tc_block.split("\n")
            new_tc_lines = []
            skip_remaining = 0
            for line in tc_lines:
                if skip_remaining > 0:
                    skip_remaining -= 1
                    continue
                if multi_start in line:
                    skip_remaining = 1
                    for j in range(tc_lines.index(line) + 1, len(tc_lines)):
                        if ")" in tc_lines[j]:
                            break
                        skip_remaining += 1
                    continue
                new_tc_lines.append(line)
            new_tc = "\n".join(new_tc_lines)
        else:
            return content
    
    content = content[:tc_match.start()] + new_tc + content[tc_match.end():]
    
    # Add runtime import before TYPE_CHECKING
    before_tc = content[:content.find("if TYPE_CHECKING:")]
    import_lines = list(re.finditer(r'^from .*\n', before_tc, re.MULTILINE))
    insert_pos = import_lines[-1].end() if import_lines else 0
    
    import_line = f"from shell.platform.domain.value_objects.{mod} import {name}\n"
    content = content[:insert_pos] + import_line + content[insert_pos:]
    return content

def fix_empty_type_checking(content: str) -> str:
    """Add 'pass' to empty TYPE_CHECKING blocks."""
    def add_pass(match):
        block = match.group()
        lines = block.split("\n")
        has_content = False
        for line in lines[1:]:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                has_content = True
                break
        if not has_content:
            # Add "    pass" after the if line
            return "if TYPE_CHECKING:\n    pass\n"
        return block
    
    return re.sub(
        r'if TYPE_CHECKING:\n(?:[ \t]*\n|[ \t]*#[^\n]*\n)*',
        add_pass,
        content
    )

def fix_deleted_is_not_none(content: str) -> str:
    """Fix _deleted_at is not None -> _deleted_at.value is not None."""
    return content.replace("self._deleted_at is not None", "self._deleted_at.value is not None")

# Process all domain aggregate files
for relpath in sorted(BASE.rglob("*.py")):
    if "__pycache__" in str(relpath) or ".venv" in str(relpath):
        continue
    fpath = relpath
    rel = fpath.relative_to(BASE.parent).as_posix()
    if "shell/" not in rel:
        continue
    
    content = fpath.read_text(encoding="utf-8")
    original = content
    
    # Move imports
    for name, mod in [("DeletedAt", "deleted_at"), ("UpdatedAt", "updated_at")]:
        key_lists = files_need_runtime_import.get(name, [])
        if rel in key_lists or rel.removeprefix("shell/") in key_lists:
            content = move_import_to_runtime(content, name, mod)
    
    # Fix _deleted_at is not None
    content = fix_deleted_is_not_none(content)
    
    if content != original:
        fpath.write_text(content, encoding="utf-8")
        print(f"Fixed: {rel}")

print("Done!")
