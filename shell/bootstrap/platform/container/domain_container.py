"""Kontener dla serwisów domenowych, strategii wykonania i polityk."""

from __future__ import annotations

from dependency_injector import containers, providers
from shell.application.execution.strategies.graph_node_execution_strategy import get_strategy
from shell.domain.execution.services.graph_node_execution_navigator import (
    TransitionBasedGraphNodeExecutionNavigator,
)
from shell.domain.execution.services.graph_node_execution_policy import (
    FailFastGraphNodeExecutionPolicy,
)
from shell.infrastructure.execution.default_implementations.sub_graph_defaults import (
    DefaultSubGraphDiscovery,
    DefaultSubGraphObserver,
    FullAccessSubGraphSecurity,
    LatestVersionStrategy,
    PermissiveSubGraphGovernance,
)


class DomainContainer(containers.DeclarativeContainer):
    """Kontener dla serwisów domenowych, strategii i polityk."""

    infra = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()

    node_navigator_factory = providers.Singleton(TransitionBasedGraphNodeExecutionNavigator)
    graph_node_execution_policy_factory = providers.Singleton(FailFastGraphNodeExecutionPolicy)

    strategy = providers.Object(get_strategy("agent"))

    # ── Sub-graph extension points (defaults, can be overridden) ──────────
    sub_graph_governance_factory = providers.Singleton(PermissiveSubGraphGovernance)
    sub_graph_security_factory = providers.Singleton(FullAccessSubGraphSecurity)
    sub_graph_observer_factory = providers.Singleton(DefaultSubGraphObserver)
    sub_graph_versioning_factory = providers.Singleton(
        LatestVersionStrategy,
        unit_of_work_factory=buses.unit_of_work_factory,
    )
    sub_graph_discovery_factory = providers.Singleton(
        DefaultSubGraphDiscovery,
        unit_of_work_factory=buses.unit_of_work_factory,
    )

    # ── Sub-graph extension points (kept for handler wiring) ──────────────
