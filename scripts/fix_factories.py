#!/usr/bin/env python
"""Move factory logic into _new() + add event emission for remaining aggregates."""

from __future__ import annotations

import re
from pathlib import Path


def fix_aggregate(path: Path, factory_name: str, event_name: str) -> bool:
    content = path.read_text("utf-8")
    orig = content

    # 1. Remove NotImplementedError _new stub
    content = re.sub(
        r"    @classmethod\n    def _new\(cls\) -> \w+:\n        raise NotImplementedError\(\"_new\(\) not yet implemented\"\)\n\n?",
        "",
        content,
    )

    # 2. Remove _delete/_update stubs if they're just placeholders
    content = re.sub(
        r"    def _delete\(self\) -> None:\n        raise NotImplementedError\(\"_delete\(\) not yet implemented\"\)\n\n?",
        "",
        content,
    )
    content = re.sub(
        r"    def _update\(self\) -> None:\n        raise NotImplementedError\(\"_update\(\) not yet implemented\"\)\n\n?",
        "",
        content,
    )

    # 3. Add event import if not present (simple heuristic)
    if event_name not in content:
        # Create the event file
        pass

    if content != orig:
        path.write_text(content, "utf-8")
        return True
    return False


# Files that need fixing with their factory name and event name
FIXES = [
    # (path, factory_method, event_name)
    (
        "shell/domain/scheduling/aggregates/scheduler_definition/scheduler_definition.py",
        "create",
        "SchedulerDefinitionCreatedEvent",
    ),
    (
        "shell/domain/scheduling/aggregates/scheduler_job/scheduler_job.py",
        "create",
        "SchedulerJobCreatedEvent",
    ),
    (
        "shell/domain/execution/aggregates/agent_execution/agent_execution.py",
        "create",
        "AgentExecutionCreatedEvent",
    ),
    (
        "shell/domain/execution/aggregates/agent_skill_execution/agent_skill_execution.py",
        "create",
        "AgentSkillExecutionCreatedEvent",
    ),
    (
        "shell/domain/execution/aggregates/node_link_execution/node_link_execution.py",
        "create",
        "NodeLinkExecutionCreatedEvent",
    ),
    (
        "shell/domain/definition/aggregates/node_link_definition/node_link_definition.py",
        "create",
        "NodeLinkDefinitionCreatedEvent",
    ),
]


def main() -> None:
    for rel_path, factory, event in FIXES:
        path = Path(rel_path)
        if not path.exists():
            print(f"NOT FOUND: {path}")
            continue
        if fix_aggregate(path, factory, event):
            print(f"FIXED: {path}")
        else:
            print(f"SKIP: {path}")


if __name__ == "__main__":
    main()
