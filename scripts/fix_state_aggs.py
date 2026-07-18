#!/usr/bin/env python
"""Fix state aggregates and remaining event issues."""
from pathlib import Path
import re

state_agg_fixes = [
    {
        "path": "shell/domain/execution/aggregates/session_execution_state/session_execution_state.py",
        "event_name": "SessionExecutionStateCreatedEvent",
        "event_import": "from shell.domain.execution.aggregates.session_execution_state.events.session_execution_state_created_event import SessionExecutionStateCreatedEvent",
    },
    {
        "path": "shell/domain/execution/aggregates/task_execution_state/task_execution_state.py",
        "event_name": "TaskExecutionStateCreatedEvent",
        "event_import": "from shell.domain.execution.aggregates.task_execution_state.events.task_execution_state_created_event import TaskExecutionStateCreatedEvent",
    },
    {
        "path": "shell/domain/execution/aggregates/user_execution_state/user_execution_state.py",
        "event_name": "UserExecutionStateCreatedEvent",
        "event_import": "from shell.domain.execution.aggregates.user_execution_state.events.user_execution_state_created_event import UserExecutionStateCreatedEvent",
    },
]

for f in state_agg_fixes:
    p = Path(f["path"])
    content = p.read_text("utf-8")
    orig = content

    # Add event import
    content = content.replace(
        "from shell.platform.domain.base.aggregate_root import AggregateRoot",
        f"from shell.platform.domain.base.aggregate_root import AggregateRoot\n{f['event_import']}",
    )

    # Remove stubs
    content = re.sub(r"    def _(?:new|delete|update)\(self\) -> None:\n        raise NotImplementedError\(\"_[a-z]+\(\) not yet implemented\"\)\n?", "", content)
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Rename create to _new
    content = re.sub(r"    def create\(", "    def _new(", content)

    # Change return cls( to instance = cls( in _new
    content = re.sub(
        r"(def _new\([^)]*\)[^:]*:\n(?:        .*\n)*?)return cls\(",
        lambda m: m.group(1) + "instance = cls(",
        content,
    )

    # Add event emission
    content = re.sub(
        r"(        \))(?=\n    @classmethod)",
        lambda m: m.group(0) + f"\n        instance.append_event(\n            {f['event_name']}.now(\n                {p.parent.name.lower()}_id=instance.id,\n                now=now,\n            )\n        )\n        return instance",
        content,
    )

    # Add public create back
    param_match = re.search(r"def _new\(([^)]*)\)", content)
    if param_match:
        param_str = param_match.group(1)
        params = [x.strip().split(":")[0].split("=")[0].strip() for x in param_str.split(",")]
        params = [x for x in params if x and x not in ("cls", "*", "")]
        call_args = ", ".join(f"{p}={p}" for p in params)
        agg_name = p.parent.name.title().replace("_", "")
        wrapper = f"""    @classmethod
    def create({param_str}) -> {agg_name}:
        return cls._new({call_args})
"""

        content = re.sub(
            r"    @classmethod\n    def restore\(",
            wrapper + "    @classmethod\n    def restore(",
            content,
        )

    if content != orig:
        p.write_text(content, "utf-8")
        print(f"FIXED: {f['path']}")
    else:
        print(f"SKIP: {f['path']}")

print("Done")
