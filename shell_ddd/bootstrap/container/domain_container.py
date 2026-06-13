"""Kontener dla serwisów domenowych, strategii wykonania i polityk."""
from __future__ import annotations

from dependency_injector import containers, providers

from shell_ddd.application.strategies.node_execution_strategy import get_strategy
from shell_ddd.domain.services.compensation_handler import NoOpCompensationHandler
from shell_ddd.domain.services.node_execution_policy import FailFastPolicy
from shell_ddd.domain.services.node_navigator import LinearNodeNavigator


class DomainContainer(containers.DeclarativeContainer):
    """Kontener dla serwisów domenowych, strategii i polityk."""

    node_navigator_factory = providers.Singleton(LinearNodeNavigator)
    node_execution_policy_factory = providers.Singleton(FailFastPolicy)
    compensation_handler_factory = providers.Singleton(NoOpCompensationHandler)

    strategy = providers.Object(get_strategy("agent"))