"""Tabela kroków pilota sagi project_provision."""

from __future__ import annotations

from shell.platform.process.saga.steps import StepDefinition, StepRegistry
from shell.project_service.application.project.project_provision.commands.release_workspace_command import (
    ReleaseWorkspaceCommand,
)

PROJECT_PROVISION_STEPS = StepRegistry(
    steps=(
        StepDefinition(
            name="provision_workspace",
            target_service="project",
            compensation_command=ReleaseWorkspaceCommand,
            compensate_on_failure=True,
        ),
    )
)
