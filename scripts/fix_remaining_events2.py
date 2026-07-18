#!/usr/bin/env python
"""Fix remaining _new methods with DOTALL regex."""
import re
from pathlib import Path

FILES = [
    "shell/domain/definition/aggregates/node_link_definition/node_link_definition.py",
    "shell/domain/definition/aggregates/runner_config/runner_config.py",
    "shell/domain/scheduling/aggregates/scheduler_job/scheduler_job.py",
    "shell/domain/execution/aggregates/session_execution_state/session_execution_state.py",
    "shell/domain/execution/aggregates/task_execution_state/task_execution_state.py",
    "shell/domain/execution/aggregates/user_execution_state/user_execution_state.py",
]

for path_str in FILES:
    p = Path(path_str)
    content = p.read_text("utf-8")
    orig = content

    if "append_event" in content:
        print(f"SKIP (has event): {path_str}")
        continue

    # Find _new method with DOTALL
    # Pattern: from @classmethod to the first return cls( or return instance
    new_match = re.search(
        r"(    @classmethod\n    def _new\(.*?\) -> \w+:\n(?:        .*\n)*?)return (?:instance|cls)\(",
        content,
        re.DOTALL,
    )
    if not new_match:
        print(f"NO _new found: {path_str}")
        continue

    prefix = new_match.group(1)
    old_full = new_match.group(0)

    # Extract agg name from path
    agg_dir = p.parent.name
    agg_name = agg_dir[0].upper() + agg_dir[1:]  # capitalize first
    # Convert snake_case to PascalCase
    agg_name = "".join(word.capitalize() for word in agg_dir.split("_"))
    event_name = f"{agg_name}CreatedEvent"

    # Build new content
    event_block = (
        f"        instance.append_event(\n"
        f"            {event_name}.now(\n"
        f"                {agg_name.lower()}_id=instance.id,\n"
        f"                now=now,\n"
        f"            )\n"
        f"        )\n"
        f"        return instance"
    )

    new_full = prefix + "instance = cls("
    content = content.replace(old_full, new_full)

    # Add event block + return instance after the closing paren of cls()
    content = content.replace(
        "        )\n\n    @classmethod",
        f"        )\n{event_block}\n\n    @classmethod",
        1,
    )

    if content != orig:
        p.write_text(content, "utf-8")
        print(f"FIXED: {path_str}")
    else:
        print(f"NOCHANGE: {path_str}")

print("\nDone")
