#!/usr/bin/env python
"""Fix _new NotImplementedError stubs: rename create/new to _new, add message."""
import re
from pathlib import Path

FILES = [
    ("shell/domain/user/aggregates/user/user.py", "User"),
    ("shell/domain/user/aggregates/user_skill/user_skill.py", "UserSkill"),
    ("shell/domain/user/aggregates/user_state/user_state.py", "UserState"),
    ("shell/domain/session/aggregates/session/session.py", "Session"),
    ("shell/domain/session/aggregates/session_state/session_state.py", "SessionState"),
    ("shell/domain/project/aggregates/project/project.py", "Project"),
    ("shell/domain/project/aggregates/project_skill/project_skill.py", "ProjectSkill"),
    ("shell/domain/project/aggregates/project_state/project_state.py", "ProjectState"),
    ("shell/domain/execution/aggregates/agent_config_execution/agent_config_execution.py", "AgentConfigExecution"),
    ("shell/domain/execution/aggregates/agent_execution/agent_execution.py", "AgentExecution"),
    ("shell/domain/execution/aggregates/agent_skill_execution/agent_skill_execution.py", "AgentSkillExecution"),
    ("shell/domain/execution/aggregates/edge_execution/edge_execution.py", "EdgeExecution"),
    ("shell/domain/execution/aggregates/edge_link_execution/edge_link_execution.py", "EdgeLinkExecution"),
    ("shell/domain/execution/aggregates/graph_execution/graph_execution.py", "GraphExecution"),
    ("shell/domain/execution/aggregates/graph_execution_state/graph_execution_state.py", "GraphExecutionState"),
    ("shell/domain/execution/aggregates/node_execution/node_execution.py", "NodeExecution"),
    ("shell/domain/execution/aggregates/node_execution_state/node_execution_state.py", "NodeExecutionState"),
    ("shell/domain/execution/aggregates/session_execution/session_execution.py", "SessionExecution"),
    ("shell/domain/execution/aggregates/task_execution/task_execution.py", "TaskExecution"),
    ("shell/domain/execution/aggregates/user_execution/user_execution.py", "UserExecution"),
    ("shell/domain/execution/aggregates/workflow/workflow.py", "Workflow"),
    ("shell/domain/execution/aggregates/workflow_state/workflow_state.py", "WorkflowState"),
    ("shell/domain/definition/aggregates/graph_definition/graph_definition.py", "GraphDefinition"),
    ("shell/domain/definition/aggregates/graph_definition_embedding/graph_definition_embedding.py", "GraphDefinitionEmbedding"),
    ("shell/domain/definition/aggregates/node_definition/node_definition.py", "NodeDefinition"),
]

for path_str, name in FILES:
    fp = Path(path_str)
    content = fp.read_text("utf-8")
    orig = content

    # Check for NotImplementedError _new stub
    stub_pattern = r"    @classmethod\n    def _new\(cls\) -> \w+:\n        raise NotImplementedError\(\"_new\(\) not yet implemented\"\)"
    if not re.search(stub_pattern, content):
        continue

    # Find existing factory method (new or create)
    factory_name = None
    for fn in ["new", "create", "open", "initialize"]:
        if re.search(rf"    @classmethod\n    def {fn}\(", content):
            factory_name = fn
            break

    if not factory_name:
        continue

    # Remove the stub
    content = re.sub(stub_pattern, "", content)

    # Rename factory to _new (keeping its body), add public wrapper
    # First, capture the factory body
    factory_match = re.search(
        rf"(    @classmethod\n    def {factory_name}\([^)]*\)[^:]*:\n(?:        .*\n)*?)(?:\n    @|\Z)",
        content,
        re.DOTALL,
    )
    if factory_match:
        factory_body = factory_match.group(1)

        # Replace the factory with _new version
        new_factory = factory_body.replace(f"def {factory_name}(", "def _new(", 1)
        content = content.replace(factory_body, new_factory, 1)

        # Add public wrapper that calls _new
        wrapper = factory_body.replace(f"def {factory_name}(", f"def {factory_name}(", 1)
        content = content.replace(
            "    @classmethod\n    def restore(",
            f"{wrapper}\n    @classmethod\n    def restore(",
        )

    if content != orig:
        fp.write_text(content, "utf-8")
        print(f"FIXED: {path_str}")

print("\nDone")
