#!/usr/bin/env python
"""Fix remaining _update stubs."""

from pathlib import Path

FILES = [
    ("shell/domain/session/aggregates/session/session.py", "Session"),
    ("shell/domain/session/aggregates/session_state/session_state.py", "SessionState"),
    ("shell/domain/execution/aggregates/task_execution/task_execution.py", "TaskExecution"),
    ("shell/domain/execution/aggregates/user_execution/user_execution.py", "UserExecution"),
    ("shell/domain/execution/aggregates/workflow/workflow.py", "Workflow"),
    ("shell/domain/execution/aggregates/node_execution/node_execution.py", "NodeExecution"),
    (
        "shell/domain/execution/aggregates/session_execution/session_execution.py",
        "SessionExecution",
    ),
    ("shell/domain/definition/aggregates/graph_definition/graph_definition.py", "GraphDefinition"),
    ("shell/domain/definition/aggregates/node_definition/node_definition.py", "NodeDefinition"),
]

for path_str, name in FILES:
    fp = Path(path_str)
    content = fp.read_text("utf-8")
    orig = content

    # Add imports
    for imp in ["DeletedAt", "UpdatedAt"]:
        il = f"from shell.platform.domain.value_objects.{imp.lower()} import {imp}"
        if il not in content:
            content = content.replace("if TYPE_CHECKING:", f"{il}\n\nif TYPE_CHECKING:", 1)

    # Replace stubs
    for method in ["_delete", "_update"]:
        stub_self = f'    def {method}(self) -> None:\n        raise NotImplementedError("{method}() not yet implemented")'
        stub_cls = f'    def {method}(cls) -> None:\n        raise NotImplementedError("{method}() not yet implemented")'
        stub = stub_self if stub_self in content else (stub_cls if stub_cls in content else "")
        if stub:
            if method == "_delete":
                real = (
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
            else:
                real = (
                    f"    def _update(self, now: UpdatedAt) -> None:\n"
                    f"        self._updated_at = now\n"
                    f"        self.append_event(\n"
                    f"            {name}UpdatedEvent.now(\n"
                    f"                {name.lower()}_id=self._id,\n"
                    f"                now=now,\n"
                    f"            )\n"
                    f"        )"
                )
            content = content.replace(stub, real, 1)
        elif f"def {method}(" not in content:
            # Add method
            lines = content.split("\n")
            insert_at = len(lines)
            for i, l in enumerate(lines):
                if "@property" in l and i > 5:
                    insert_at = i
                    break
            if method == "_delete":
                real = (
                    f"    def _delete(self, now: DeletedAt) -> None:\n"
                    f"        self._deleted_at = now\n"
                    f"        self._updated_at = UpdatedAt.from_datetime(now.value)\n"
                    f"        self.append_event(\n"
                    f"            {name}DeletedEvent.now(\n"
                    f"                {name.lower()}_id=self._id,\n"
                    f"                now=now,\n"
                    f"            )\n"
                    f"        )\n"
                )
            else:
                real = (
                    f"    def _update(self, now: UpdatedAt) -> None:\n"
                    f"        self._updated_at = now\n"
                    f"        self.append_event(\n"
                    f"            {name}UpdatedEvent.now(\n"
                    f"                {name.lower()}_id=self._id,\n"
                    f"                now=now,\n"
                    f"            )\n"
                    f"        )\n"
                )
            lines.insert(insert_at, real)
            content = "\n".join(lines)

    if content != orig:
        fp.write_text(content, "utf-8")
        print(f"FIXED: {path_str}")

print("\nDone")
