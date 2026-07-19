#!/usr/bin/env python
"""Final comprehensive fix for remaining aggregates."""

from __future__ import annotations

import re
from pathlib import Path

FIXES: list[dict] = [
    {
        "path": "shell/domain/execution/aggregates/node_link_execution/node_link_execution.py",
        "factory": "create",
        "agg_name": "NodeLinkExecution",
        "id_type": "NodeLinkExecutionId",
        "event_name": "NodeLinkExecutionCreatedEvent",
        "event_import": "shell.domain.execution.aggregates.node_link_execution.events.node_link_execution_created_event",
        "has_timestamps": False,
    },
    {
        "path": "shell/domain/definition/aggregates/node_link_definition/node_link_definition.py",
        "factory": "create",
        "agg_name": "NodeLinkDefinition",
        "id_type": "NodeLinkDefinitionId",
        "event_name": "NodeLinkDefinitionCreatedEvent",
        "event_import": "shell.domain.definition.aggregates.node_link_definition.events.node_link_definition_created_event",
        "has_timestamps": False,
    },
    {
        "path": "shell/domain/definition/aggregates/runner_config/runner_config.py",
        "factory": "new",
        "agg_name": "RunnerConfig",
        "id_type": "RunnerConfigId",
        "event_name": "RunnerConfigCreatedEvent",
        "event_import": "shell.domain.definition.aggregates.runner_config.events.runner_config_created_event",
        "has_timestamps": True,
    },
    {
        "path": "shell/domain/scheduling/aggregates/scheduler_job/scheduler_job.py",
        "factory": "create",
        "agg_name": "SchedulerJob",
        "id_type": "SchedulerExecutionId",
        "event_name": "SchedulerJobCreatedEvent",
        "event_import": "shell.domain.scheduling.aggregates.scheduler_job.events.scheduler_job_created_event",
        "has_timestamps": True,
    },
]

for fix in FIXES:
    p = Path(fix["path"])
    if not p.exists():
        print(f"NOT FOUND: {p}")
        continue

    content = p.read_text("utf-8")
    orig = content
    agg = fix["agg_name"]
    factory = fix["factory"]
    event_name = fix["event_name"]
    event_import = fix["event_import"]

    # Create event file
    event_dir = p.parent / "events"
    event_dir.mkdir(exist_ok=True)
    event_file = event_dir / f"{agg.lower()}_created_event.py"
    id_module = (
        f"shell.domain.{re.search(r'shell/domain/(.+?)/', str(p)).group(1).replace('/', '.')}.aggregates.{agg.lower().replace('_', '')}.value_objects.{fix['id_type']}"
        if not fix.get("id_module")
        else fix["id_module"]
    )
    # Simplified - just write a reasonable event file
    event_content = f'''from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class {event_name}(DomainEvent):
    {agg.lower()}_id: object

    @classmethod
    def now(cls, {agg.lower()}_id: object, now: CreatedAt) -> "{event_name}":
        return cls(occurred_at=now, {agg.lower()}_id={agg.lower()}_id)
'''
    event_file.write_text(event_content, "utf-8")
    print(f"  EVENT: {event_file}")

    # Remove stubs
    for stub in ["_new", "_delete", "_update"]:
        content = re.sub(
            rf"    (?:@classmethod\n)?    def {stub}\(.*?\):\n        raise NotImplementedError\(\".*?\"\)\n?",
            "",
            content,
        )
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Add event import
    import_line = f"from {event_import} import {event_name}"
    if import_line not in content:
        lines = content.split("\n")
        insert_after = 0
        for i, l in enumerate(lines):
            if l.startswith("from shell.") and "import" in l and "TYPE_CHECKING" not in l:
                insert_after = i
        lines.insert(insert_after + 1, import_line)
        content = "\n".join(lines)

    # Rename factory to _new
    content = content.replace(f"    def {factory}(", f"    def _new(")

    # Add event in _new body
    if "append_event" not in content:
        content = re.sub(
            r"(    @classmethod\n    def _new\([^)]*\)[^:]*:\n(?:        .*\n)*?)return cls\(",
            lambda m: m.group(1) + "instance = cls(",
            content,
        )
        event_block = (
            f"        instance.append_event(\n"
            f"            {event_name}.now(\n"
            f"                {agg.lower()}_id=instance.id,\n"
            f"                now=now,\n"
            f"            )\n"
            f"        )\n"
            f"        return instance"
        )
        content = re.sub(
            r"(        \))(?=\n    @classmethod)",
            lambda m: m.group(0) + f"\n{event_block}",
            content,
        )

    # Add public wrapper
    if f"    def {factory}(" not in content:
        param_match = re.search(r"def _new\(([^)]*)\)", content)
        if param_match:
            param_str = param_match.group(1)
            param_names = []
            for p_part in param_str.split(","):
                p_part = p_part.strip()
                if p_part and p_part not in ("cls", "*,", "*", ""):
                    p_name = p_part.split(":")[0].split("=")[0].strip()
                    if p_name:
                        param_names.append(p_name)
            # Remove cls if first
            if param_names and param_names[0] == "cls":
                param_names = param_names[1:]

            call_args = ", ".join(f"{p}={p}" for p in param_names)
            wrapper = (
                f"\n    @classmethod\n"
                f"    def {factory}(cls{', *,' if '*' not in param_str else ''} {param_str.replace('cls, ', '') if param_str.startswith('cls,') else param_str}) -> {agg}:\n"
                f"        return cls._new({call_args})\n"
            )
            content = content.replace(
                "    @classmethod\n    def restore(",
                wrapper + "\n    @classmethod\n    def restore(",
            )

    if content != orig:
        p.write_text(content, "utf-8")
        print(f"  AGG: {p}")
    else:
        print(f"  SKIP: {p}")

print("\nDone - 5 files processed")
