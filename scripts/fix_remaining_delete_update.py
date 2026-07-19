#!/usr/bin/env python
"""Fix remaining _delete/_update issues in all aggregates."""

from pathlib import Path
import re

files = {
    "shell/domain/session/aggregates/session_state/session_state.py": "SessionState",
    "shell/domain/execution/aggregates/agent_skill_execution/agent_skill_execution.py": "AgentSkillExecution",
    "shell/domain/execution/aggregates/graph_execution/graph_execution.py": "GraphExecution",
    "shell/domain/execution/aggregates/graph_execution_state/graph_execution_state.py": "GraphExecutionState",
    "shell/domain/execution/aggregates/node_execution_state/node_execution_state.py": "NodeExecutionState",
    "shell/domain/execution/aggregates/session_execution/session_execution.py": "SessionExecution",
    "shell/domain/execution/aggregates/session_execution_state/session_execution_state.py": "SessionExecutionState",
    "shell/domain/execution/aggregates/task_execution_state/task_execution_state.py": "TaskExecutionState",
    "shell/domain/execution/aggregates/user_execution_state/user_execution_state.py": "UserExecutionState",
    "shell/domain/execution/aggregates/workflow/workflow.py": "Workflow",
    "shell/domain/execution/aggregates/workflow_state/workflow_state.py": "WorkflowState",
    "shell/domain/definition/aggregates/graph_definition_embedding/graph_definition_embedding.py": "GraphDefinitionEmbedding",
    "shell/domain/definition/aggregates/node_definition/node_definition.py": "NodeDefinition",
    "shell/domain/definition/aggregates/graph_definition/graph_definition.py": "GraphDefinition",
}


def ensure_import(content, imp):
    if imp in content:
        return content
    return content.replace(
        "if TYPE_CHECKING:",
        f"{imp}\n\nif TYPE_CHECKING:",
        1,
    )


for path_str, name in files.items():
    fp = Path(path_str)
    content = fp.read_text("utf-8")
    orig = content

    content = ensure_import(
        content, "from shell.platform.domain.value_objects.deleted_at import DeletedAt"
    )
    content = ensure_import(
        content, "from shell.platform.domain.value_objects.updated_at import UpdatedAt"
    )

    # Replace NotImplementedError _delete stub
    stub_delete = f'    def _delete(self) -> None:\n        raise NotImplementedError("_delete() not yet implemented")'
    stub_update = f'    def _update(self) -> None:\n        raise NotImplementedError("_update() not yet implemented")'

    real_delete = (
        f"    def _delete(self, now: DeletedAt) -> None:\n"
        f"        self._deleted_at = now\n"
        f"        self._updated_at = UpdatedAt.from_datetime(now.value)\n"
        f"        self.append_event(\n"
        f"            {name}DeletedEvent.now(\n"
        f"                {name.lower()}_id=self._id,\n"
        f"                now=now,\n"
        f"            )\n"
        f"        )"
    )
    real_update = (
        f"    def _update(self, now: UpdatedAt) -> None:\n"
        f"        self._updated_at = now\n"
        f"        self.append_event(\n"
        f"            {name}UpdatedEvent.now(\n"
        f"                {name.lower()}_id=self._id,\n"
        f"                now=now,\n"
        f"            )\n"
        f"        )"
    )

    if stub_delete in content:
        content = content.replace(stub_delete, real_delete, 1)
    elif f"def _delete(" not in content:
        lines = content.split("\n")
        insert_at = len(lines)
        for i, l in enumerate(lines):
            if "@property" in l and i > 5:
                insert_at = i
                break
        lines.insert(insert_at, real_delete + "\n")
        content = "\n".join(lines)

    if stub_update in content:
        content = content.replace(stub_update, real_update, 1)
    elif f"def _update(" not in content:
        lines = content.split("\n")
        insert_at = len(lines)
        for i, l in enumerate(lines):
            if "@property" in l and i > 5:
                insert_at = i
                break
        lines.insert(insert_at, real_update + "\n")
        content = "\n".join(lines)

    if content != orig:
        fp.write_text(content, "utf-8")
        print(f"FIXED: {path_str}")

print("\nDone")
