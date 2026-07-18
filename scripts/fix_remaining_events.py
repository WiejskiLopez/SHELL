#!/usr/bin/env python
"""Fix remaining _new methods: add now param + created_at + event emission."""
import re
from pathlib import Path

FILES = [
    ("shell/domain/definition/aggregates/node_link_definition/node_link_definition.py",
     ["id_", "graph_definition_id", "node_definition_id"], "NodeLinkDefinition"),
    ("shell/domain/definition/aggregates/runner_config/runner_config.py",
     ["id_", "now"], "RunnerConfig"),
    ("shell/domain/scheduling/aggregates/scheduler_job/scheduler_job.py",
     ["id_", "scheduler_definition_id", "name", "job_type", "interval_seconds", "batch_size", "config", "now", "enabled"], "SchedulerJob"),
    ("shell/domain/execution/aggregates/session_execution_state/session_execution_state.py",
     [], "SessionExecutionState"),
    ("shell/domain/execution/aggregates/task_execution_state/task_execution_state.py",
     [], "TaskExecutionState"),
    ("shell/domain/execution/aggregates/user_execution_state/user_execution_state.py",
     [], "UserExecutionState"),
]

for path_str, params, agg_name in FILES:
    p = Path(path_str)
    content = p.read_text("utf-8")
    orig = content
    event_name = f"{agg_name}CreatedEvent"

    # Check if _new has event already
    if "append_event" in content:
        print(f"SKIP (has event): {path_str}")
        continue

    # Find _new method
    new_match = re.search(r"(    @classmethod\n    def _new\([^)]*\)[^:]*:\n(?:        .*\n)*?)(return instance|return cls)\(", content)
    if not new_match:
        print(f"NO _new found: {path_str}")
        continue

    prefix = new_match.group(1)
    is_instance = new_match.group(2) == "return instance"

    # Change return to instance creation if needed
    if not is_instance:
        content = content.replace(new_match.group(0), prefix + "instance = cls(")

    # Add created_at=now to the cls() call
    # Find the constructor inside _new
    if "created_at=now" not in content.split("def _new")[1].split("\n    @")[0] if "def _new" in content else "":
        # Add before closing paren
        content = content.replace(
            "        )\n\n    @classmethod",
            "            created_at=now,\n        )\n\n    @classmethod",
            1,
        )

    # Add append_event call
    content = content.replace(
        "        )\n\n    @classmethod",
        f"""        )\n        instance.append_event(\n            {event_name}.now(\n                {agg_name.lower()}_id=instance.id,\n                now=now,\n            )\n        )\n        return instance\n\n    @classmethod""",
        1,
    )

    if content != orig:
        p.write_text(content, "utf-8")
        print(f"FIXED: {path_str}")
    else:
        print(f"NOCHANGE: {path_str}")

print("\nDone")
