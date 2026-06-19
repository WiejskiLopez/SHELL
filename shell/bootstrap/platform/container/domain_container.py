"""Kontener dla serwisów domenowych, strategii wykonania i polityk."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.execution.strategies.graph_node_execution_strategy import get_strategy
from shell.domain.execution.services.compensation_handler import NoOpCompensationHandler
from shell.domain.execution.services.graph_node_execution_navigator import TransitionBasedNavigator
from shell.domain.execution.services.graph_node_execution_policy import FailFastPolicy


class DomainContainer(containers.DeclarativeContainer):
    """Kontener dla serwisów domenowych, strategii i polityk."""

    node_navigator_factory = providers.Singleton(TransitionBasedNavigator)
    graph_node_execution_policy_factory = providers.Singleton(FailFastPolicy)
    compensation_handler_factory = providers.Singleton(NoOpCompensationHandler)

    strategy = providers.Object(get_strategy("agent"))
