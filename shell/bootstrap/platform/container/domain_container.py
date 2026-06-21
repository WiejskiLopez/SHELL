"""Kontener dla serwisów domenowych, strategii wykonania i polityk."""

from __future__ import annotations

from dependency_injector import containers, providers
from shell.application.execution.strategies.graph_node_execution_strategy import get_strategy
from shell.domain.execution.aggregates.workflow.services.compensation_handler import NoOpCompensationHandler
from shell.domain.execution.services.graph_node_execution_navigator import (
    TransitionBasedGraphNodeExecutionNavigator,
)
from shell.domain.execution.services.graph_node_execution_policy import (
    FailFastGraphNodeExecutionPolicy,
)
from shell.domain.execution.services.sub_graph_execution_service import SubGraphExecutionService
from shell.infrastructure.platform.default_implementations.sub_graph_defaults import (
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
    compensation_handler_factory = providers.Singleton(NoOpCompensationHandler)

    strategy = providers.Object(get_strategy("agent"))

    # ── Sub-graph extension points (defaults, can be overridden) ──────────
    sub_graph_governance_factory = providers.Singleton(PermissiveSubGraphGovernance)
    sub_graph_security_factory = providers.Singleton(FullAccessSubGraphSecurity)
    sub_graph_observer_factory = providers.Singleton(DefaultSubGraphObserver)
    sub_graph_versioning_factory = providers.Singleton(
        LatestVersionStrategy,
        uow_factory=buses.uow_factory,
    )
    sub_graph_discovery_factory = providers.Singleton(
        DefaultSubGraphDiscovery,
        uow_factory=buses.uow_factory,
    )

    # ── Sub-graph execution service (used by PlannerResultHandler) ────────
    sub_graph_execution_service_factory = providers.Singleton(
        SubGraphExecutionService,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        logger=infra.stdlib_logger,
        definition_provider=infra.definition_provider_factory,
        governance=sub_graph_governance_factory,
        security=sub_graph_security_factory,
        versioning=sub_graph_versioning_factory,
        observer=sub_graph_observer_factory,
    )


