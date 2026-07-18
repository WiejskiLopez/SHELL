#!/usr/bin/env python
"""Fix RunnerConfig and state aggregates."""
import re
from pathlib import Path

def fix_file(path, event_name, agg_name, event_import):
    content = path.read_text("utf-8")
    orig = content

    for stub in ["_new", "_delete", "_update"]:
        content = re.sub(
            rf"    (?:@classmethod\n)?    def {stub}\(.*?\) -> .*?:\n        raise NotImplementedError\(\".*?\"\)\n",
            "", content, flags=re.DOTALL
        )
    content = re.sub(r"\n{3,}", "\n\n", content)

    if event_import not in content:
        lines = content.split("\n")
        insert_at = 0
        for i, l in enumerate(lines):
            if l.startswith("from shell.") and "TYPE_CHECKING" not in l:
                insert_at = i + 1
        lines.insert(insert_at, event_import)
        content = "\n".join(lines)

    if "def new(" in content and "def _new(" not in content:
        content = content.replace("def new(", "def _new(")

    if "_new" in content and "append_event" not in content:
        content = re.sub(
            r"(    @classmethod\n    def _new\([^)]*\)[^:]*:\n(?:        .*\n)*?)return cls\(",
            lambda m: m.group(1) + "instance = cls(",
            content,
        )
        event_call = (
            f"        instance.append_event(\n"
            f"            {event_name}.now(\n"
            f"                {agg_name.lower()}_id=instance.id,\n"
            f"                now=now,\n"
            f"            )\n"
            f"        )\n        return instance"
        )
        content = re.sub(
            r"(        \))(?=\n    @classmethod)",
            lambda m: m.group(0) + f"\n{event_call}",
            content,
        )

    if content != orig:
        path.write_text(content, "utf-8")
        return True
    return False

# RunnerConfig
p = Path("shell/domain/definition/aggregates/runner_config/runner_config.py")
if fix_file(p, "RunnerConfigCreatedEvent", "RunnerConfig",
            "from shell.domain.definition.aggregates.runner_config.events.runner_config_created_event import RunnerConfigCreatedEvent"):
    print("FIXED: RunnerConfig")

# State aggregates
for path_str, agg_name in [
    ("shell/domain/execution/aggregates/session_execution_state/session_execution_state.py", "SessionExecutionState"),
    ("shell/domain/execution/aggregates/task_execution_state/task_execution_state.py", "TaskExecutionState"),
    ("shell/domain/execution/aggregates/user_execution_state/user_execution_state.py", "UserExecutionState"),
]:
    p = Path(path_str)
    if not p.exists():
        continue
    # State aggregates need their event too
    if fix_file(p, f"{agg_name}CreatedEvent", agg_name,
                f"from shell.domain.execution.aggregates.{agg_name.lower()}.events.{agg_name.lower()}_created_event import {agg_name}CreatedEvent"):
        print(f"FIXED: {agg_name}")
    else:
        print(f"SKIP: {agg_name}")

print("\nDone")
