#!/usr/bin/env python3
"""Move DeletedAt/UpdatedAt from TYPE_CHECKING to runtime imports where needed."""

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "shell"

# Files that need DeletedAt moved out of TYPE_CHECKING
files = [
    "domain/definition/aggregates/graph_definition/graph_definition.py",
    "domain/definition/aggregates/node_definition/node_definition.py",
    "domain/definition/aggregates/node_link_definition/node_link_definition.py",
    "domain/definition/aggregates/runner_config/runner_config.py",
    "domain/execution/aggregates/agent_config_execution/agent_config_execution.py",
    "domain/execution/aggregates/agent_execution/agent_execution.py",
    "domain/execution/aggregates/agent_skill_execution/agent_skill_execution.py",
    "domain/execution/aggregates/edge_link_execution/edge_link_execution.py",
    "domain/execution/aggregates/graph_execution/graph_execution.py",
    "domain/execution/aggregates/graph_execution_state/graph_execution_state.py",
    "domain/execution/aggregates/node_execution/node_execution.py",
    "domain/execution/aggregates/node_execution_state/node_execution_state.py",
    "domain/execution/aggregates/node_link_execution/node_link_execution.py",
    "domain/execution/aggregates/session_execution/session_execution.py",
    "domain/execution/aggregates/session_execution_state/session_execution_state.py",
    "domain/execution/aggregates/task_execution/task_execution.py",
    "domain/execution/aggregates/task_execution_state/task_execution_state.py",
    "domain/execution/aggregates/user_execution/user_execution.py",
    "domain/execution/aggregates/user_execution_state/user_execution_state.py",
    "domain/execution/aggregates/workflow/workflow.py",
    "domain/execution/aggregates/workflow_state/workflow_state.py",
    "domain/messaging/aggregates/message_router/message_router.py",
    "domain/project/aggregates/project/project.py",
    "domain/project/aggregates/project_skill/project_skill.py",
    "domain/project/aggregates/project_state/project_state.py",
    "domain/scheduling/aggregates/scheduler_definition/scheduler_definition.py",
    "domain/scheduling/aggregates/scheduler_execution/scheduler_execution.py",
    "domain/scheduling/aggregates/scheduler_job/scheduler_job.py",
    "domain/session/aggregates/session/session.py",
    "domain/session/aggregates/session_state/session_state.py",
    "domain/user/aggregates/user/user.py",
    "domain/user/aggregates/user_skill/user_skill.py",
    "domain/user/aggregates/user_state/user_state.py",
    "infrastructure/execution/graph_execution/persistence/sql/mappers/_created_at_value.py",
    "infrastructure/execution/task_execution/persistence/sql/mappers/_created_at_value.py",
    "infrastructure/execution/workflow/persistence/sql/mappers/_created_at_value.py",
    "platform/domain/events/aggregate_deleted_event.py",
    "domain/execution/aggregates/edge_execution/edge_execution.py",
]

for relpath in files:
    fpath = BASE / relpath
    if not fpath.exists():
        print(f"NOT FOUND: {relpath}")
        continue
    content = fpath.read_text(encoding="utf-8")
    original = content

    for name, mod in [("DeletedAt", "deleted_at"), ("UpdatedAt", "updated_at")]:
        # Find the TYPE_CHECKING block as a simple contiguous indented block
        tc_start = content.find("if TYPE_CHECKING:")
        if tc_start < 0:
            continue
        
        # Find the end of the TYPE_CHECKING block
        # Lines after it that are at same or lesser indentation end the block
        rest = content[tc_start:]
        lines = rest.split("\n")
        tc_lines = []
        in_block = False
        for line in lines:
            if line.startswith("if TYPE_CHECKING:"):
                in_block = True
                tc_lines.append(line)
            elif in_block:
                if line == "" or not line.startswith(" "):
                    break
                tc_lines.append(line)
            else:
                break
        tc_block = "\n".join(tc_lines)
        tc_end = tc_start + len(tc_block)
        
        if name not in tc_block:
            continue
        
        # Check if name is used at runtime
        runtime_content = content[:tc_start] + content[tc_end:]
        if name not in runtime_content:
            continue
        
        # Remove the import line from TYPE_CHECKING
        # Pattern: `    from shell.platform.domain.value_objects.deleted_at import DeletedAt`
        import_pattern = f"    from shell.platform.domain.value_objects.{mod} import {name}"
        if import_pattern in tc_block:
            new_tc = tc_block.replace(import_pattern + "\n", "")
            new_tc = new_tc.replace(import_pattern, "")
        else:
            # Try multi-line form
            multi_pattern = f"    from shell.platform.domain.value_objects.{mod} import ("
            if multi_pattern in tc_block:
                # Remove 3 lines (from... import (, DeletedAt, ))
                lines = tc_block.split("\n")
                new_lines = []
                skip = 0
                for line in lines:
                    if skip > 0:
                        skip -= 1
                        continue
                    if multi_pattern in line:
                        skip = 2  # skip this line and next 2
                        continue
                    new_lines.append(line)
                new_tc = "\n".join(new_lines)
            else:
                continue  # pattern not found in expected form
        
        content = content[:tc_start] + new_tc + content[tc_end:]
        
        # Add import before TYPE_CHECKING block
        import_line = f"from shell.platform.domain.value_objects.{mod} import {name}\n"
        insert_pos = tc_start
        # Try to insert after the last import line before TYPE_CHECKING
        before = content[:tc_start]
        last_import = list(re.finditer(r'^from .*\n', before, re.MULTILINE))
        if last_import:
            insert_pos = last_import[-1].end()
        
        content = content[:insert_pos] + import_line + content[insert_pos:]

    if content != original:
        fpath.write_text(content, encoding="utf-8")
        print(f"Fixed: {relpath}")
    else:
        print(f"SKIPPED: {relpath} (no changes)")

print("Done!")
