"""Typed configuration slices with explicit ownership boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.platform.infrastructure.configuration.shell_config import EventsConfig


@dataclass(frozen=True, slots=True)
class DeploymentConfig:
    """Values owned by the deployment and service composition root."""

    profile: str
    database_url: str


@dataclass(frozen=True, slots=True)
class PlatformRuntimeConfig:
    """Neutral technical settings shared by platform adapters and workers."""

    log_level: str
    events: EventsConfig


@dataclass(frozen=True, slots=True)
class AuthConfig:
    """Authentication inputs passed to auth adapters without exposing secrets."""

    api_key: str


@dataclass(frozen=True, slots=True)
class ServiceConfig:
    """Settings used only by a service or its own workers."""

    max_step: int
    max_parallel: int
    seed_dev_data: bool
    reset_db: bool
