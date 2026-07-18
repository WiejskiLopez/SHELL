#!/usr/bin/env python
"""Fix remaining _new methods - handles CRLF line endings."""
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
    content = p.read_text("utf-8")  # uses platform native \r\n
    orig = content

    if "append_event" in content:
        print(f"SKIP: {path_str} (has event)")
        continue

    # Normalize line endings for regex
    content_norm = content.replace("\r\n", "\n")
    orig_norm = content_norm

    # Find _new method with flexible indentation
    new_match = re.search(
        r"(\s*@classmethod\n\s*def _new\(.*?\)\s*->\s*\w+:\n(?:        .*\n)*?)(?:return (?:instance|cls)\()",
        content_norm,
        re.DOTALL,
    )
    if not new_match:
        print(f"NO _new: {path_str}")
        continue

    prefix = new_match.group(1)
    old_full = new_match.group(0)

    # Extract aggregate name from dir
    agg_dir = p.parent.name
    agg_name = "".join(word.capitalize() for word in agg_dir.split("_"))
    event_name = f"{agg_name}CreatedEvent"

    # Replace with instance creation
    new_full = prefix + "instance = cls("
    content_norm = content_norm.replace(old_full, new_full, 1)

    # Add event block + return instance
    event_block = (
        f"        instance.append_event(\n"
        f"            {event_name}.now(\n"
        f"                {agg_name.lower()}_id=instance.id,\n"
        f"                now=now,\n"
        f"            )\n"
        f"        )\n"
        f"        return instance"
    )
    content_norm = content_norm.replace(
        "        )\n\n    @classmethod",
        f"        )\n{event_block}\n\n    @classmethod",
        1,
    )

    if content_norm != orig_norm:
        # Convert back to CRLF if original had it
        content_norm = content_norm.replace("\n", "\r\n")
        # Remove trailing CRLF
        content_norm = content_norm.rstrip("\r\n")
        p.write_text(content_norm, "utf-8")
        print(f"FIXED: {path_str}")
    else:
        print(f"NOCHANGE: {path_str}")

print("\nDone")
