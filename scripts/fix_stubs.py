#!/usr/bin/env python
"""Add remaining _delete/_update stubs + fix SchedulerJob updated_at."""
from pathlib import Path

for path_str in [
    "shell/domain/scheduling/aggregates/scheduler_definition/scheduler_definition.py",
    "shell/domain/execution/aggregates/agent_skill_execution/agent_skill_execution.py",
    "shell/domain/execution/aggregates/session_execution_state/session_execution_state.py",
    "shell/domain/execution/aggregates/task_execution_state/task_execution_state.py",
    "shell/domain/execution/aggregates/user_execution_state/user_execution_state.py",
    "shell/domain/definition/aggregates/node_link_definition/node_link_definition.py",
    "shell/domain/definition/aggregates/runner_config/runner_config.py",
]:
    fp = Path(path_str)
    content = fp.read_text("utf-8")
    orig = content

    for method in ("_delete", "_update"):
        if f"def {method}(" not in content:
            lines = content.split("\n")
            insert_at = len(lines) - 1
            for i, line in enumerate(lines):
                if "@property" in line and i > 5:
                    insert_at = i
                    break
            stub = f"    def {method}(self) -> None:\n        raise NotImplementedError(\"{method}() not yet implemented\")\n"
            lines.insert(insert_at, stub)
            content = "\n".join(lines)

    if content != orig:
        fp.write_text(content, "utf-8")
        print(f"FIXED: {path_str}")

# Fix SchedulerJob
fp = Path("shell/domain/scheduling/aggregates/scheduler_job/scheduler_job.py")
content = fp.read_text("utf-8")
if "updated_at=Timestamp.from_datetime(now.value)" in content:
    content = content.replace("updated_at=Timestamp.from_datetime(now.value)", "")
    fp.write_text(content, "utf-8")
    print("FIXED SchedulerJob: removed updated_at from _new")

print("\nDone")
