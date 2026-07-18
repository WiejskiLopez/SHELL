#!/usr/bin/env python
"""Fix import paths in all aggregate files."""
from pathlib import Path

# Wrong prefixes
prefixes = ["execution.", "definition.", "scheduling.", "session.", "user.", "project.", "messaging."]
# Wrong event names
event_renames = {
    "agentexecution": "agent_execution",
    "agentskillexecution": "agent_skill_execution",
    "agentconfigexecution": "agent_config_execution",
    "runnerconfig": "runner_config",
    "nodeexecution": "node_execution",
    "nodelinkexecution": "node_link_execution",
    "nodelinkdefinition": "node_link_definition",
    "graphexecution": "graph_execution",
    "graphdefinition": "graph_definition",
    "sessionexecution": "session_execution",
    "userexecution": "user_execution",
    "taskexecution": "task_execution",
    "schedulerdefinition": "scheduler_definition",
    "schedulerexecution": "scheduler_execution",
    "schedulerjob": "scheduler_job",
    "projectskill": "project_skill",
    "projectstate": "project_state",
    "messagerouter": "message_router",
    "workflowstate": "workflow_state",
    "nodeexecutionstate": "node_execution_state",
    "sessionexecutionstate": "session_execution_state",
    "taskexecutionstate": "task_execution_state",
    "userexecutionstate": "user_execution_state",
    "graphexecutionstate": "graph_execution_state",
    "userstate": "user_state",
    "userskill": "user_skill",
    "edgelinkexecution": "edge_link_execution",
    "edgeexecution": "edge_execution",
    "sessionstate": "session_state",
    "nodedefinition": "node_definition",
    "graphdefinitionembedding": "graph_definition_embedding",
}

count = 0
for f in sorted(Path("shell/domain").rglob("**/aggregates/**/*.py")):
    if any(p in f.parts for p in ("events", "exceptions", "value_objects", "repositories", "__init__")):
        continue
    c = f.read_text("utf-8")
    orig = c

    for prefix in prefixes:
        c = c.replace(f"from {prefix}", f"from shell.domain.{prefix}")

    for old, new in event_renames.items():
        c = c.replace(f"events.{old}_created_event", f"events.{new}_created_event")
        c = c.replace(f"events.{old}_deleted_event", f"events.{new}_deleted_event")
        c = c.replace(f"events.{old}_updated_event", f"events.{new}_updated_event")

    if c != orig:
        f.write_text(c, encoding="utf-8")
        count += 1

print(f"Fixed {count} files")
