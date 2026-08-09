"""Compatibility exports for the canonical Pure-DI composition root."""

from __future__ import annotations

from shell.platform.bootstrap.container.command_factories import Commands
from shell.platform.bootstrap.container.query_factories import Queries
from shell.platform.bootstrap.container.root import Container, CoreContainer

__all__ = ["Commands", "Container", "CoreContainer", "Queries"]
