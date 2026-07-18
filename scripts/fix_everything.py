#!/usr/bin/env python
"""Fix all 6 remaining aggregates: add events to _new."""
import re
from pathlib import Path

FILES = [
    ("shell/domain/definition/aggregates/node_link_definition/node_link_definition.py", "NodeLinkDefinition", "node_link_definition"),
    ("shell/domain/definition/aggregates/runner_config/runner_config.py", "RunnerConfig", "runner_config"),
    ("shell/domain/scheduling/aggregates/scheduler_job/scheduler_job.py", "SchedulerJob", "scheduler_job"),
    ("shell/domain/execution/aggregates/session_execution_state/session_execution_state.py", "SessionExecutionState", "session_execution_state"),
    ("shell/domain/execution/aggregates/task_execution_state/task_execution_state.py", "TaskExecutionState", "task_execution_state"),
    ("shell/domain/execution/aggregates/user_execution_state/user_execution_state.py", "UserExecutionState", "user_execution_state"),
]

for path_str, agg_name, agg_dir in FILES:
    p = Path(path_str)
    content = p.read_text("utf-8")
    orig = content

    # Build event import
    # path like: shell/domain/definition/aggregates/node_link_definition/node_link_definition.py
    # We need: shell.domain.definition.aggregates.node_link_definition.events.node_link_definition_created_event
    parts = path_str.replace("shell/domain/", "").replace("\\", "/").split("/")
    # parts = ['definition', 'aggregates', 'node_link_definition', 'node_link_definition.py']
    event_module = "shell.domain." + parts[0] + ".aggregates." + parts[2] + ".events." + agg_dir + "_created_event"
    event_import = "from " + event_module + " import " + agg_name + "CreatedEvent"

    # 1. Move CreatedAt out of TYPE_CHECKING, add event import
    content = content.replace(
        "if TYPE_CHECKING:",
        "from shell.platform.domain.value_objects.created_at import CreatedAt\n" + event_import + "\n\nif TYPE_CHECKING:",
        1,
    )

    # 2. Rename factory to _new
    for factory in ("create", "new"):
        pattern = "    @classmethod\n    def " + factory + "("
        if pattern in content:
            content = content.replace(pattern, "    @classmethod\n    def _new(", 1)

    # 3. Transform _new body
    idx = content.find("def _new(")
    if idx < 0:
        continue

    # Find where _new body ends (next @classmethod or @property)
    rest = content[idx:]
    end_match = re.search(r"\n    @(?:classmethod|property)", rest)
    end = idx + (end_match.start() if end_match else len(rest))

    new_body = content[idx:end]

    # Change return cls( to instance = cls(
    if "return cls(" in new_body:
        before_cls = new_body.split("return cls(")[0]
        after_cls = new_body.split("return cls(")[1]
        # Find matching paren - simple approach
        new_new_body = before_cls + "instance = cls(" + after_cls

        # Add event emission + return instance before the next method
        event_block = (
            "        instance.append_event(\n"
            "            " + agg_name + "CreatedEvent.now(\n"
            "                " + agg_name.lower() + "_id=instance.id,\n"
            "                now=now,\n"
            "            )\n"
            "        )\n"
            "        return instance"
        )

        # Find the closing ) of cls() - it's at the end of new_body
        if new_new_body.endswith("\n"):
            new_new_body = new_new_body[:-1]
        last_paren = new_new_body.rfind(")")
        if last_paren > 0:
            new_new_body = new_new_body[:last_paren+1] + "\n" + event_block + new_new_body[last_paren+1:]

        content = content[:idx] + new_new_body + content[end:]

    # 4. Add public create/new wrapper
    factory_names = ["create", "new"]
    has_public = any("    def " + fn + "(" in content for fn in factory_names)
    if not has_public:
        sig_match = re.search(r"def _new\(([^)]+)\)", content)
        if sig_match:
            sig = sig_match.group(1)
            params = [p.strip() for p in sig.split(",")]
            param_names = []
            for p in params:
                name = p.split(":")[0].split("=")[0].strip()
                if name and name not in ("cls", "*", ""):
                    param_names.append(name)
            call_args = ", ".join(n + "=" + n for n in param_names)
            wrapper = (
                "    @classmethod\n"
                "    def create(" + sig + ") -> " + agg_name + ":\n"
                "        return cls._new(" + call_args + ")\n"
                "\n"
            )
            content = content.replace(
                "    @classmethod\n    def restore(",
                wrapper + "    @classmethod\n    def restore(",
            )

    if content != orig:
        p.write_text(content, "utf-8")
        print("FIXED:", path_str)

print("\nDone")
