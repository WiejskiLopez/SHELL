#!/usr/bin/env python
"""Final fix: rename create() to _new(), add event emission, add public wrapper."""
import re
from pathlib import Path

FIXES = [
    # (path, factory_name, event_name, aggregate_name, id_type, id_module)
    ("shell/domain/scheduling/aggregates/scheduler_job/scheduler_job.py", "create", "SchedulerJobCreatedEvent", "SchedulerJob", "SchedulerExecutionId", "shell.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id"),
    ("shell/domain/execution/aggregates/agent_execution/agent_execution.py", "create", "AgentExecutionCreatedEvent", "AgentExecution", "AgentExecutionId", "shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id"),
    ("shell/domain/execution/aggregates/agent_skill_execution/agent_skill_execution.py", "create", "AgentSkillExecutionCreatedEvent", "AgentSkillExecution", "AgentSkillExecutionId", "shell.domain.execution.aggregates.agent_skill_execution.value_objects.agent_skill_execution_id"),
    ("shell/domain/execution/aggregates/node_link_execution/node_link_execution.py", "create", "NodeLinkExecutionCreatedEvent", "NodeLinkExecution", "NodeLinkExecutionId", "shell.domain.execution.aggregates.node_link_execution.value_objects.node_link_execution_id"),
    ("shell/domain/definition/aggregates/node_link_definition/node_link_definition.py", "create", "NodeLinkDefinitionCreatedEvent", "NodeLinkDefinition", "NodeLinkDefinitionId", "shell.domain.definition.aggregates.node_link_definition.value_objects.node_link_definition_id"),
    ("shell/domain/execution/aggregates/runner_config/runner_config.py", "new", "RunnerConfigCreatedEvent", "RunnerConfig", "RunnerConfigId", "shell.domain.definition.aggregates.runner_config.value_objects.runner_config_id"),
]

def fix_event_file(path, name, id_type, id_module):
    if not path.exists():
        return False
    content = f'''from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from {id_module} import {id_type}
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class {name}CreatedEvent(DomainEvent):
    {name.lower()}_id: {id_type}

    @classmethod
    def now(cls, {name.lower()}_id: {id_type}, now: CreatedAt) -> "{name}CreatedEvent":
        return cls(occurred_at=now, {name.lower()}_id={name.lower()}_id)
'''
    path.write_text(content, "utf-8")
    print(f"  EVENT: {path}")
    return True

def fix_aggregate(path, factory, event_name, agg_name):
    content = path.read_text("utf-8")
    orig = content

    # Remove _new/_delete/_update NotImplementedError stubs
    for stub in ["_new", "_delete", "_update"]:
        content = re.sub(
            rf"    (?:@classmethod\n)?    def {stub}\(.*?\) -> .*?:\n        raise NotImplementedError\(\".*?\"\)\n",
            "",
            content,
            flags=re.DOTALL,
        )
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Rename factory → _new
    content = re.sub(rf"    @classmethod\n    def {factory}\(", "    @classmethod\n    def _new(", content)

    # Add event import if not present
    event_import = f"from shell.domain.{path.relative_to(Path('shell/domain')).parent.as_posix().replace('/', '.')}.events.{agg_name.lower()}_created_event import {event_name}"
    event_import = event_import.replace("\\", "/")
    if event_import not in content:
        lines = content.split("\n")
        insert_at = 0
        for i, l in enumerate(lines):
            if l.startswith("from shell.") and "TYPE_CHECKING" not in l:
                insert_at = i + 1
        lines.insert(insert_at, event_import)
        content = "\n".join(lines)

    # Add append_event call in _new body
    name = agg_name
    event_call = (
        f"        instance.append_event(\n"
        f"            {event_name}.now(\n"
        f"                {name.lower()}_id=instance.id,\n"
        f"                now=now,\n"
        f"            )\n"
        f"        )"
    )

    # Change return cls( to instance = cls(
    content = re.sub(
        r"(    @classmethod\n    def _new\([^)]*\)[^:]*:\n(?:        .*\n)*?)return cls\(",
        lambda m: m.group(1) + "instance = cls(",
        content,
    )

    # Add event call + return instance before the next method
    content = re.sub(
        r"(        \))",
        lambda m: m.group(0) + f"\n{event_call}\n        return instance" if "instance = cls(" in content[m.start()-100:m.start()] else m.group(0),
        content,
    )

    # Add back public factory
    params_match = re.search(r"def _new\(([^)]*)\)", content)
    if params_match and f"{factory}(" not in content:
        param_str = params_match.group(1)
        # Extract just param names
        param_names = []
        for p in param_str.split(","):
            p = p.strip()
            if "=" in p:
                param_names.append(p.split("=")[0].strip())
            elif p and p not in ("cls", "*,", "*"):
                param_names.append(p.split(":")[0].strip())
        # Filter to real params
        param_names = [p for p in param_names if p and p not in ("cls", "*", "")]
        
        # Build public wrapper
        if param_names and param_names[0] == "cls":
            param_names = param_names[1:]  # remove cls
        call_args = ", ".join(f"{p}={p}" for p in param_names)
        decorator = "    @classmethod\n"
        wrapper = (
            f"\n{decorator}"
            f"    def {factory}(cls, {param_str}) -> {agg_name}:\n"
            f"        return cls._new({call_args})\n"
        )
        content = content.replace(
            "    @classmethod\n    def restore(",
            f"{wrapper}\n    @classmethod\n    def restore(",
        )

    if content != orig:
        path.write_text(content, "utf-8")
        print(f"  AGGREGATE: {path}")
        return True
    return False

for agg_path, factory, event_name, agg_name, id_type, id_module in FIXES:
    p = Path(agg_path)
    if not p.exists():
        print(f"NOT FOUND: {p}")
        continue
    print(f"\n=== {agg_name} ===")
    # Fix event file
    event_path = p.parent / "events" / f"{agg_name.lower()}_created_event.py"
    fix_event_file(event_path, agg_name, id_type, id_module)
    # Fix aggregate
    fix_aggregate(p, factory, event_name, agg_name)

print("\nDone")
