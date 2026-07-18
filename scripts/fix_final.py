#!/usr/bin/env python
"""Fix event file imports and remaining aggregates."""
from pathlib import Path

# Fix event files
EVENT_FIXES = [
    Path("shell/domain/execution/aggregates/agent_execution/events/agent_execution_created_event.py"),
    Path("shell/domain/execution/aggregates/agent_skill_execution/events/agent_skill_execution_created_event.py"),
    Path("shell/domain/execution/aggregates/node_link_execution/events/node_link_execution_created_event.py"),
    Path("shell/domain/definition/aggregates/node_link_definition/events/node_link_definition_created_event.py"),
    Path("shell/domain/scheduling/aggregates/scheduler_job/events/scheduler_job_created_event.py"),
]

for ef in EVENT_FIXES:
    if ef.exists():
        content = ef.read_text("utf-8")
        # Fix import if it contains bad paths
        if "schedulerjob" in content or "agentexecution" in content or "agentskillexecution" in content or "nodelink" in content.lower():
            print(f"FIXING: {ef}")
            # Simple fix: replace bad paths with correct ones
            content = content.replace("shell.domain.schedulerjob.aggregates.schedulerjob", "shell.domain.scheduling.aggregates.scheduler_job")
            content = content.replace("shell.domain.schedulerdefinition.aggregates.schedulerdefinition", "shell.domain.scheduling.aggregates.scheduler_definition")
            content = content.replace("shell.domain.agentexecution.aggregates.agentexecution", "shell.domain.execution.aggregates.agent_execution")
            content = content.replace("shell.domain.agentskillexecution.aggregates.agentskillexecution", "shell.domain.execution.aggregates.agent_skill_execution")
            content = content.replace("shell.domain.nodelinkexecution.aggregates.nodelinkexecution", "shell.domain.execution.aggregates.node_link_execution")
            content = content.replace("shell.domain.nodelinkdefinition.aggregates.nodelinkdefinition", "shell.domain.definition.aggregates.node_link_definition")
            ef.write_text(content, "utf-8")

# Now fix AgentSkillExecution, NodeLinkExecution, NodeLinkDefinition
import re

AGG_FIXES = [
    ("shell/domain/execution/aggregates/agent_skill_execution/agent_skill_execution.py", "AgentSkillExecution"),
    ("shell/domain/execution/aggregates/node_link_execution/node_link_execution.py", "NodeLinkExecution"),
    ("shell/domain/definition/aggregates/node_link_definition/node_link_definition.py", "NodeLinkDefinition"),
]

for path_str, agg_name in AGG_FIXES:
    p = Path(path_str)
    if not p.exists():
        print(f"NOT FOUND: {p}")
        continue

    content = p.read_text("utf-8")
    orig = content

    event_name = f"{agg_name}CreatedEvent"
    id_type = f"{agg_name}Id"

    # Remove stubs
    for stub in ["_new", "_delete", "_update"]:
        content = re.sub(
            rf"    (?:@classmethod\n)?    def {stub}\(.*?\) -> .*?:\n        raise NotImplementedError\(\".*?\"\)\n",
            "", content, flags=re.DOTALL
        )
    content = re.sub(r"\n{3,}", "\n\n", content)

    # If _new exists without append_event, add it
    if "_new" in content:
        # Check if _new has instance = cls pattern or return cls pattern
        if "append_event" not in content:
            # Add event to _new
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
        p.write_text(content, "utf-8")
        print(f"FIXED AGG: {p}")
    else:
        print(f"SKIP AGG: {p} (no changes)")

print("\nDone")
