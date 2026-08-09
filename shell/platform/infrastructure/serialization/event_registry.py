"""Central event registry for outbox/inbox deserialization.

Auto-generated. Run .opencode/tools/regenerate_registry.py to rebuild.
"""

from __future__ import annotations

from shell.application.definition.graph_definition.integration_events.graph_definition_created_integration_event import (
    GraphDefinitionCreatedIntegrationEvent,
)
from shell.application.definition.graph_definition.integration_events.graph_definition_deleted_integration_event import (
    GraphDefinitionDeletedIntegrationEvent,
)
from shell.application.definition.graph_definition.integration_events.graph_definition_updated_integration_event import (
    GraphDefinitionUpdatedIntegrationEvent,
)
from shell.application.definition.graph_definition_embedding.integration_events.graph_definition_embedding_created_integration_event import (
    GraphDefinitionEmbeddingCreatedIntegrationEvent,
)
from shell.application.definition.graph_definition_embedding.integration_events.graph_definition_embedding_deleted_integration_event import (
    GraphDefinitionEmbeddingDeletedIntegrationEvent,
)
from shell.application.definition.graph_definition_embedding.integration_events.graph_definition_embedding_updated_integration_event import (
    GraphDefinitionEmbeddingUpdatedIntegrationEvent,
)
from shell.application.definition.node_definition.integration_events.node_definition_created_integration_event import (
    NodeDefinitionCreatedIntegrationEvent,
)
from shell.application.definition.node_definition.integration_events.node_definition_deleted_integration_event import (
    NodeDefinitionDeletedIntegrationEvent,
)
from shell.application.definition.node_definition.integration_events.node_definition_updated_integration_event import (
    NodeDefinitionUpdatedIntegrationEvent,
)
from shell.application.definition.node_link_definition.integration_events.node_link_definition_created_integration_event import (
    NodeLinkDefinitionCreatedIntegrationEvent,
)
from shell.application.definition.node_link_definition.integration_events.node_link_definition_deleted_integration_event import (
    NodeLinkDefinitionDeletedIntegrationEvent,
)
from shell.application.definition.node_link_definition.integration_events.node_link_definition_updated_integration_event import (
    NodeLinkDefinitionUpdatedIntegrationEvent,
)
from shell.application.definition.runner_config.integration_events.runner_config_created_integration_event import (
    RunnerConfigCreatedIntegrationEvent,
)
from shell.application.definition.runner_config.integration_events.runner_config_deleted_integration_event import (
    RunnerConfigDeletedIntegrationEvent,
)
from shell.application.definition.runner_config.integration_events.runner_config_updated_integration_event import (
    RunnerConfigUpdatedIntegrationEvent,
)
from shell.application.execution.agent_config_execution.integration_events.agent_config_execution_deleted_integration_event import (
    AgentConfigExecutionDeletedIntegrationEvent,
)
from shell.application.execution.agent_config_execution.integration_events.agent_config_execution_updated_integration_event import (
    AgentConfigExecutionUpdatedIntegrationEvent,
)
from shell.application.execution.agent_config_execution.integration_events.agent_config_updated_integration_event import (
    AgentConfigUpdatedIntegrationEvent,
)
from shell.application.execution.agent_execution.integration_events.agent_execution_created_integration_event import (
    AgentExecutionCreatedIntegrationEvent,
)
from shell.application.execution.agent_execution.integration_events.agent_execution_deleted_integration_event import (
    AgentExecutionDeletedIntegrationEvent,
)
from shell.application.execution.agent_execution.integration_events.agent_execution_updated_integration_event import (
    AgentExecutionUpdatedIntegrationEvent,
)
from shell.application.execution.agent_skill_execution.integration_events.agent_skill_execution_created_integration_event import (
    AgentSkillExecutionCreatedIntegrationEvent,
)
from shell.application.execution.agent_skill_execution.integration_events.agent_skill_execution_deleted_integration_event import (
    AgentSkillExecutionDeletedIntegrationEvent,
)
from shell.application.execution.agent_skill_execution.integration_events.agent_skill_execution_updated_integration_event import (
    AgentSkillExecutionUpdatedIntegrationEvent,
)
from shell.application.execution.edge_execution.integration_events.edge_execution_created_integration_event import (
    EdgeExecutionCreatedIntegrationEvent,
)
from shell.application.execution.edge_execution.integration_events.edge_execution_deleted_integration_event import (
    EdgeExecutionDeletedIntegrationEvent,
)
from shell.application.execution.edge_execution.integration_events.edge_execution_updated_integration_event import (
    EdgeExecutionUpdatedIntegrationEvent,
)
from shell.application.execution.edge_link_execution.integration_events.edge_link_execution_created_integration_event import (
    EdgeLinkExecutionCreatedIntegrationEvent,
)
from shell.application.execution.edge_link_execution.integration_events.edge_link_execution_deleted_integration_event import (
    EdgeLinkExecutionDeletedIntegrationEvent,
)
from shell.application.execution.edge_link_execution.integration_events.edge_link_execution_updated_integration_event import (
    EdgeLinkExecutionUpdatedIntegrationEvent,
)
from shell.application.execution.graph_execution.integration_events.graph_execution_created_integration_event import (
    GraphExecutionCreatedIntegrationEvent,
)
from shell.application.execution.graph_execution.integration_events.graph_execution_deleted_integration_event import (
    GraphExecutionDeletedIntegrationEvent,
)
from shell.application.execution.graph_execution.integration_events.graph_execution_updated_integration_event import (
    GraphExecutionUpdatedIntegrationEvent,
)
from shell.application.execution.graph_execution_state.integration_events.graph_execution_state_changed_integration_event import (
    GraphExecutionStateChangedIntegrationEvent,
)
from shell.application.execution.graph_execution_state.integration_events.graph_execution_state_deleted_integration_event import (
    GraphExecutionStateDeletedIntegrationEvent,
)
from shell.application.execution.graph_execution_state.integration_events.graph_execution_state_updated_integration_event import (
    GraphExecutionStateUpdatedIntegrationEvent,
)
from shell.application.execution.node_execution.integration_events.node_execution_created_integration_event import (
    NodeExecutionCreatedIntegrationEvent,
)
from shell.application.execution.node_execution.integration_events.node_execution_deleted_integration_event import (
    NodeExecutionDeletedIntegrationEvent,
)
from shell.application.execution.node_execution.integration_events.node_execution_updated_integration_event import (
    NodeExecutionUpdatedIntegrationEvent,
)
from shell.application.execution.node_execution_state.integration_events.node_execution_state_changed_integration_event import (
    NodeExecutionStateChangedIntegrationEvent,
)
from shell.application.execution.node_execution_state.integration_events.node_execution_state_deleted_integration_event import (
    NodeExecutionStateDeletedIntegrationEvent,
)
from shell.application.execution.node_execution_state.integration_events.node_execution_state_updated_integration_event import (
    NodeExecutionStateUpdatedIntegrationEvent,
)
from shell.application.execution.node_link_execution.integration_events.node_link_execution_created_integration_event import (
    NodeLinkExecutionCreatedIntegrationEvent,
)
from shell.application.execution.node_link_execution.integration_events.node_link_execution_deleted_integration_event import (
    NodeLinkExecutionDeletedIntegrationEvent,
)
from shell.application.execution.node_link_execution.integration_events.node_link_execution_updated_integration_event import (
    NodeLinkExecutionUpdatedIntegrationEvent,
)
from shell.application.execution.session_execution.integration_events.session_execution_created_integration_event import (
    SessionExecutionCreatedIntegrationEvent,
)
from shell.application.execution.session_execution.integration_events.session_execution_deleted_integration_event import (
    SessionExecutionDeletedIntegrationEvent,
)
from shell.application.execution.session_execution.integration_events.session_execution_updated_integration_event import (
    SessionExecutionUpdatedIntegrationEvent,
)
from shell.application.execution.session_execution_state.integration_events.session_execution_state_created_integration_event import (
    SessionExecutionStateCreatedIntegrationEvent,
)
from shell.application.execution.session_execution_state.integration_events.session_execution_state_deleted_integration_event import (
    SessionExecutionStateDeletedIntegrationEvent,
)
from shell.application.execution.session_execution_state.integration_events.session_execution_state_updated_integration_event import (
    SessionExecutionStateUpdatedIntegrationEvent,
)
from shell.application.execution.task_execution.integration_events.task_execution_created_integration_event import (
    TaskExecutionCreatedIntegrationEvent,
)
from shell.application.execution.task_execution.integration_events.task_execution_deleted_integration_event import (
    TaskExecutionDeletedIntegrationEvent,
)
from shell.application.execution.task_execution.integration_events.task_execution_updated_integration_event import (
    TaskExecutionUpdatedIntegrationEvent,
)
from shell.application.execution.task_execution_state.integration_events.task_execution_state_created_integration_event import (
    TaskExecutionStateCreatedIntegrationEvent,
)
from shell.application.execution.task_execution_state.integration_events.task_execution_state_deleted_integration_event import (
    TaskExecutionStateDeletedIntegrationEvent,
)
from shell.application.execution.task_execution_state.integration_events.task_execution_state_updated_integration_event import (
    TaskExecutionStateUpdatedIntegrationEvent,
)
from shell.application.execution.user_execution.integration_events.user_execution_created_integration_event import (
    UserExecutionCreatedIntegrationEvent,
)
from shell.application.execution.user_execution.integration_events.user_execution_deleted_integration_event import (
    UserExecutionDeletedIntegrationEvent,
)
from shell.application.execution.user_execution.integration_events.user_execution_updated_integration_event import (
    UserExecutionUpdatedIntegrationEvent,
)
from shell.application.execution.user_execution_state.integration_events.user_execution_state_created_integration_event import (
    UserExecutionStateCreatedIntegrationEvent,
)
from shell.application.execution.user_execution_state.integration_events.user_execution_state_deleted_integration_event import (
    UserExecutionStateDeletedIntegrationEvent,
)
from shell.application.execution.user_execution_state.integration_events.user_execution_state_updated_integration_event import (
    UserExecutionStateUpdatedIntegrationEvent,
)
from shell.application.execution.workflow.integration_events.workflow_created_integration_event import (
    WorkflowCreatedIntegrationEvent,
)
from shell.application.execution.workflow.integration_events.workflow_deleted_integration_event import (
    WorkflowDeletedIntegrationEvent,
)
from shell.application.execution.workflow.integration_events.workflow_updated_integration_event import (
    WorkflowUpdatedIntegrationEvent,
)
from shell.application.execution.workflow_state.integration_events.workflow_state_changed_integration_event import (
    WorkflowStateChangedIntegrationEvent,
)
from shell.application.execution.workflow_state.integration_events.workflow_state_deleted_integration_event import (
    WorkflowStateDeletedIntegrationEvent,
)
from shell.application.execution.workflow_state.integration_events.workflow_state_updated_integration_event import (
    WorkflowStateUpdatedIntegrationEvent,
)
from shell.application.messaging.message_router.integration_events.message_router_created_integration_event import (
    MessageRouterCreatedIntegrationEvent,
)
from shell.application.messaging.message_router.integration_events.message_router_deleted_integration_event import (
    MessageRouterDeletedIntegrationEvent,
)
from shell.application.messaging.message_router.integration_events.message_router_updated_integration_event import (
    MessageRouterUpdatedIntegrationEvent,
)
from shell.application.project.project.integration_events.project_created_integration_event import (
    ProjectCreatedIntegrationEvent,
)
from shell.application.project.project.integration_events.project_deleted_integration_event import (
    ProjectDeletedIntegrationEvent,
)
from shell.application.project.project.integration_events.project_updated_integration_event import (
    ProjectUpdatedIntegrationEvent,
)
from shell.application.project.project_skill.integration_events.project_skill_created_integration_event import (
    ProjectSkillCreatedIntegrationEvent,
)
from shell.application.project.project_skill.integration_events.project_skill_deleted_integration_event import (
    ProjectSkillDeletedIntegrationEvent,
)
from shell.application.project.project_skill.integration_events.project_skill_updated_integration_event import (
    ProjectSkillUpdatedIntegrationEvent,
)
from shell.application.project.project_state.integration_events.project_state_changed_integration_event import (
    ProjectStateChangedIntegrationEvent,
)
from shell.application.project.project_state.integration_events.project_state_deleted_integration_event import (
    ProjectStateDeletedIntegrationEvent,
)
from shell.application.project.project_state.integration_events.project_state_updated_integration_event import (
    ProjectStateUpdatedIntegrationEvent,
)
from shell.application.scheduling.scheduler_definition.integration_events.scheduler_definition_created_integration_event import (
    SchedulerDefinitionCreatedIntegrationEvent,
)
from shell.application.scheduling.scheduler_definition.integration_events.scheduler_definition_deleted_integration_event import (
    SchedulerDefinitionDeletedIntegrationEvent,
)
from shell.application.scheduling.scheduler_definition.integration_events.scheduler_definition_updated_integration_event import (
    SchedulerDefinitionUpdatedIntegrationEvent,
)
from shell.application.scheduling.scheduler_execution.integration_events.scheduler_execution_completed_integration_event import (
    SchedulerExecutionCompletedIntegrationEvent,
)
from shell.application.scheduling.scheduler_execution.integration_events.scheduler_execution_deleted_integration_event import (
    SchedulerExecutionDeletedIntegrationEvent,
)
from shell.application.scheduling.scheduler_execution.integration_events.scheduler_execution_failed_integration_event import (
    SchedulerExecutionFailedIntegrationEvent,
)
from shell.application.scheduling.scheduler_execution.integration_events.scheduler_execution_skipped_integration_event import (
    SchedulerExecutionSkippedIntegrationEvent,
)
from shell.application.scheduling.scheduler_execution.integration_events.scheduler_execution_started_integration_event import (
    SchedulerExecutionStartedIntegrationEvent,
)
from shell.application.scheduling.scheduler_execution.integration_events.scheduler_execution_updated_integration_event import (
    SchedulerExecutionUpdatedIntegrationEvent,
)
from shell.application.scheduling.scheduler_job.integration_events.scheduler_job_created_integration_event import (
    SchedulerJobCreatedIntegrationEvent,
)
from shell.application.scheduling.scheduler_job.integration_events.scheduler_job_deleted_integration_event import (
    SchedulerJobDeletedIntegrationEvent,
)
from shell.application.scheduling.scheduler_job.integration_events.scheduler_job_updated_integration_event import (
    SchedulerJobUpdatedIntegrationEvent,
)
from shell.application.session.session.integration_events.session_closed_integration_event import (
    SessionClosedIntegrationEvent,
)
from shell.application.session.session.integration_events.session_deleted_integration_event import (
    SessionDeletedIntegrationEvent,
)
from shell.application.session.session.integration_events.session_opened_integration_event import (
    SessionOpenedIntegrationEvent,
)
from shell.application.session.session.integration_events.session_updated_integration_event import (
    SessionUpdatedIntegrationEvent,
)
from shell.application.session.session_state.integration_events.session_state_changed_integration_event import (
    SessionStateChangedIntegrationEvent,
)
from shell.application.session.session_state.integration_events.session_state_deleted_integration_event import (
    SessionStateDeletedIntegrationEvent,
)
from shell.application.session.session_state.integration_events.session_state_updated_integration_event import (
    SessionStateUpdatedIntegrationEvent,
)
from shell.application.user.user.integration_events.user_created_integration_event import (
    UserCreatedIntegrationEvent,
)
from shell.application.user.user.integration_events.user_deleted_integration_event import (
    UserDeletedIntegrationEvent,
)
from shell.application.user.user.integration_events.user_updated_integration_event import (
    UserUpdatedIntegrationEvent,
)
from shell.application.user.user_skill.integration_events.user_skill_created_integration_event import (
    UserSkillCreatedIntegrationEvent,
)
from shell.application.user.user_skill.integration_events.user_skill_deleted_integration_event import (
    UserSkillDeletedIntegrationEvent,
)
from shell.application.user.user_skill.integration_events.user_skill_updated_integration_event import (
    UserSkillUpdatedIntegrationEvent,
)
from shell.application.user.user_state.integration_events.user_state_changed_integration_event import (
    UserStateChangedIntegrationEvent,
)
from shell.application.user.user_state.integration_events.user_state_deleted_integration_event import (
    UserStateDeletedIntegrationEvent,
)
from shell.application.user.user_state.integration_events.user_state_updated_integration_event import (
    UserStateUpdatedIntegrationEvent,
)
from shell.domain.definition.aggregates.graph_definition.events.graph_definition_created_event import (
    GraphDefinitionCreatedEvent,
)
from shell.domain.definition.aggregates.graph_definition.events.graph_definition_deleted_event import (
    GraphDefinitionDeletedEvent,
)
from shell.domain.definition.aggregates.graph_definition.events.graph_definition_updated_event import (
    GraphDefinitionUpdatedEvent,
)
from shell.domain.definition.aggregates.graph_definition_embedding.events.graph_definition_embedding_created_event import (
    GraphDefinitionEmbeddingCreatedEvent,
)
from shell.domain.definition.aggregates.graph_definition_embedding.events.graph_definition_embedding_deleted_event import (
    GraphDefinitionEmbeddingDeletedEvent,
)
from shell.domain.definition.aggregates.graph_definition_embedding.events.graph_definition_embedding_updated_event import (
    GraphDefinitionEmbeddingUpdatedEvent,
)
from shell.domain.definition.aggregates.node_definition.events.node_definition_created_event import (
    NodeDefinitionCreatedEvent,
)
from shell.domain.definition.aggregates.node_definition.events.node_definition_deleted_event import (
    NodeDefinitionDeletedEvent,
)
from shell.domain.definition.aggregates.node_definition.events.node_definition_updated_event import (
    NodeDefinitionUpdatedEvent,
)
from shell.domain.definition.aggregates.node_link_definition.events.node_link_definition_created_event import (
    NodeLinkDefinitionCreatedEvent,
)
from shell.domain.definition.aggregates.node_link_definition.events.node_link_definition_deleted_event import (
    NodeLinkDefinitionDeletedEvent,
)
from shell.domain.definition.aggregates.node_link_definition.events.node_link_definition_updated_event import (
    NodeLinkDefinitionUpdatedEvent,
)
from shell.domain.definition.aggregates.runner_config.events.runner_config_created_event import (
    RunnerConfigCreatedEvent,
)
from shell.domain.definition.aggregates.runner_config.events.runner_config_deleted_event import (
    RunnerConfigDeletedEvent,
)
from shell.domain.definition.aggregates.runner_config.events.runner_config_updated_event import (
    RunnerConfigUpdatedEvent,
)
from shell.domain.execution.aggregates.agent_config_execution.events.agent_config_execution_deleted_event import (
    AgentConfigExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.agent_config_execution.events.agent_config_execution_updated_event import (
    AgentConfigExecutionUpdatedEvent,
)
from shell.domain.execution.aggregates.agent_config_execution.events.agent_config_updated_event import (
    AgentConfigUpdatedEvent,
)
from shell.domain.execution.aggregates.agent_execution.events.agent_execution_created_event import (
    AgentExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.agent_execution.events.agent_execution_deleted_event import (
    AgentExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.agent_execution.events.agent_execution_updated_event import (
    AgentExecutionUpdatedEvent,
)
from shell.domain.execution.aggregates.agent_skill_execution.events.agent_skill_execution_created_event import (
    AgentSkillExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.agent_skill_execution.events.agent_skill_execution_deleted_event import (
    AgentSkillExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.agent_skill_execution.events.agent_skill_execution_updated_event import (
    AgentSkillExecutionUpdatedEvent,
)
from shell.domain.execution.aggregates.edge_execution.events.edge_execution_created_event import (
    EdgeExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.edge_execution.events.edge_execution_deleted_event import (
    EdgeExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.edge_execution.events.edge_execution_updated_event import (
    EdgeExecutionUpdatedEvent,
)
from shell.domain.execution.aggregates.edge_link_execution.events.edge_link_execution_created_event import (
    EdgeLinkExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.edge_link_execution.events.edge_link_execution_deleted_event import (
    EdgeLinkExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.edge_link_execution.events.edge_link_execution_updated_event import (
    EdgeLinkExecutionUpdatedEvent,
)
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_created_event import (
    GraphExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_deleted_event import (
    GraphExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_updated_event import (
    GraphExecutionUpdatedEvent,
)
from shell.domain.execution.aggregates.graph_execution_state.events.graph_execution_state_changed_event import (
    GraphExecutionStateChangedEvent,
)
from shell.domain.execution.aggregates.graph_execution_state.events.graph_execution_state_deleted_event import (
    GraphExecutionStateDeletedEvent,
)
from shell.domain.execution.aggregates.graph_execution_state.events.graph_execution_state_updated_event import (
    GraphExecutionStateUpdatedEvent,
)
from shell.domain.execution.aggregates.node_execution.events.node_execution_created_event import (
    NodeExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.node_execution.events.node_execution_deleted_event import (
    NodeExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.node_execution.events.node_execution_updated_event import (
    NodeExecutionUpdatedEvent,
)
from shell.domain.execution.aggregates.node_execution_state.events.node_execution_state_changed_event import (
    NodeExecutionStateChangedEvent,
)
from shell.domain.execution.aggregates.node_execution_state.events.node_execution_state_deleted_event import (
    NodeExecutionStateDeletedEvent,
)
from shell.domain.execution.aggregates.node_execution_state.events.node_execution_state_updated_event import (
    NodeExecutionStateUpdatedEvent,
)
from shell.domain.execution.aggregates.node_link_execution.events.node_link_execution_created_event import (
    NodeLinkExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.node_link_execution.events.node_link_execution_deleted_event import (
    NodeLinkExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.node_link_execution.events.node_link_execution_updated_event import (
    NodeLinkExecutionUpdatedEvent,
)
from shell.domain.execution.aggregates.session_execution.events.session_execution_created_event import (
    SessionExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.session_execution.events.session_execution_deleted_event import (
    SessionExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.session_execution.events.session_execution_updated_event import (
    SessionExecutionUpdatedEvent,
)
from shell.domain.execution.aggregates.session_execution_state.events.session_execution_state_created_event import (
    SessionExecutionStateCreatedEvent,
)
from shell.domain.execution.aggregates.session_execution_state.events.session_execution_state_deleted_event import (
    SessionExecutionStateDeletedEvent,
)
from shell.domain.execution.aggregates.session_execution_state.events.session_execution_state_updated_event import (
    SessionExecutionStateUpdatedEvent,
)
from shell.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
    TaskExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.task_execution.events.task_execution_deleted_event import (
    TaskExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.task_execution.events.task_execution_updated_event import (
    TaskExecutionUpdatedEvent,
)
from shell.domain.execution.aggregates.task_execution_state.events.task_execution_state_created_event import (
    TaskExecutionStateCreatedEvent,
)
from shell.domain.execution.aggregates.task_execution_state.events.task_execution_state_deleted_event import (
    TaskExecutionStateDeletedEvent,
)
from shell.domain.execution.aggregates.task_execution_state.events.task_execution_state_updated_event import (
    TaskExecutionStateUpdatedEvent,
)
from shell.domain.execution.aggregates.user_execution.events.user_execution_created_event import (
    UserExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.user_execution.events.user_execution_deleted_event import (
    UserExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.user_execution.events.user_execution_updated_event import (
    UserExecutionUpdatedEvent,
)
from shell.domain.execution.aggregates.user_execution_state.events.user_execution_state_created_event import (
    UserExecutionStateCreatedEvent,
)
from shell.domain.execution.aggregates.user_execution_state.events.user_execution_state_deleted_event import (
    UserExecutionStateDeletedEvent,
)
from shell.domain.execution.aggregates.user_execution_state.events.user_execution_state_updated_event import (
    UserExecutionStateUpdatedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_created_event import (
    WorkflowCreatedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_deleted_event import (
    WorkflowDeletedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_updated_event import (
    WorkflowUpdatedEvent,
)
from shell.domain.execution.aggregates.workflow_state.events.workflow_state_changed_event import (
    WorkflowStateChangedEvent,
)
from shell.domain.execution.aggregates.workflow_state.events.workflow_state_deleted_event import (
    WorkflowStateDeletedEvent,
)
from shell.domain.execution.aggregates.workflow_state.events.workflow_state_updated_event import (
    WorkflowStateUpdatedEvent,
)
from shell.domain.messaging.aggregates.message_router.events.message_router_created_event import (
    MessageRouterCreatedEvent,
)
from shell.domain.messaging.aggregates.message_router.events.message_router_deleted_event import (
    MessageRouterDeletedEvent,
)
from shell.domain.messaging.aggregates.message_router.events.message_router_updated_event import (
    MessageRouterUpdatedEvent,
)
from shell.domain.project.aggregates.project.events.project_created_event import ProjectCreatedEvent
from shell.domain.project.aggregates.project.events.project_deleted_event import ProjectDeletedEvent
from shell.domain.project.aggregates.project.events.project_updated_event import ProjectUpdatedEvent
from shell.domain.project.aggregates.project_skill.events.project_skill_created_event import (
    ProjectSkillCreatedEvent,
)
from shell.domain.project.aggregates.project_skill.events.project_skill_deleted_event import (
    ProjectSkillDeletedEvent,
)
from shell.domain.project.aggregates.project_skill.events.project_skill_updated_event import (
    ProjectSkillUpdatedEvent,
)
from shell.domain.project.aggregates.project_state.events.project_state_changed_event import (
    ProjectStateChangedEvent,
)
from shell.domain.project.aggregates.project_state.events.project_state_deleted_event import (
    ProjectStateDeletedEvent,
)
from shell.domain.project.aggregates.project_state.events.project_state_updated_event import (
    ProjectStateUpdatedEvent,
)
from shell.domain.scheduling.aggregates.scheduler_definition.events.scheduler_definition_created_event import (
    SchedulerDefinitionCreatedEvent,
)
from shell.domain.scheduling.aggregates.scheduler_definition.events.scheduler_definition_deleted_event import (
    SchedulerDefinitionDeletedEvent,
)
from shell.domain.scheduling.aggregates.scheduler_definition.events.scheduler_definition_updated_event import (
    SchedulerDefinitionUpdatedEvent,
)
from shell.domain.scheduling.aggregates.scheduler_execution.events.scheduler_execution_completed_event import (
    SchedulerExecutionCompletedEvent,
)
from shell.domain.scheduling.aggregates.scheduler_execution.events.scheduler_execution_deleted_event import (
    SchedulerExecutionDeletedEvent,
)
from shell.domain.scheduling.aggregates.scheduler_execution.events.scheduler_execution_failed_event import (
    SchedulerExecutionFailedEvent,
)
from shell.domain.scheduling.aggregates.scheduler_execution.events.scheduler_execution_skipped_event import (
    SchedulerExecutionSkippedEvent,
)
from shell.domain.scheduling.aggregates.scheduler_execution.events.scheduler_execution_started_event import (
    SchedulerExecutionStartedEvent,
)
from shell.domain.scheduling.aggregates.scheduler_execution.events.scheduler_execution_updated_event import (
    SchedulerExecutionUpdatedEvent,
)
from shell.domain.scheduling.aggregates.scheduler_job.events.scheduler_job_created_event import (
    SchedulerJobCreatedEvent,
)
from shell.domain.scheduling.aggregates.scheduler_job.events.scheduler_job_deleted_event import (
    SchedulerJobDeletedEvent,
)
from shell.domain.scheduling.aggregates.scheduler_job.events.scheduler_job_updated_event import (
    SchedulerJobUpdatedEvent,
)
from shell.domain.session.aggregates.session.events.session_closed_event import SessionClosedEvent
from shell.domain.session.aggregates.session.events.session_deleted_event import SessionDeletedEvent
from shell.domain.session.aggregates.session.events.session_opened_event import SessionOpenedEvent
from shell.domain.session.aggregates.session.events.session_updated_event import SessionUpdatedEvent
from shell.domain.session.aggregates.session_state.events.session_state_changed_event import (
    SessionStateChangedEvent,
)
from shell.domain.session.aggregates.session_state.events.session_state_deleted_event import (
    SessionStateDeletedEvent,
)
from shell.domain.session.aggregates.session_state.events.session_state_updated_event import (
    SessionStateUpdatedEvent,
)
from shell.domain.user.aggregates.user.events.user_created_event import UserCreatedEvent
from shell.domain.user.aggregates.user.events.user_deleted_event import UserDeletedEvent
from shell.domain.user.aggregates.user.events.user_updated_event import UserUpdatedEvent
from shell.domain.user.aggregates.user_skill.events.user_skill_created_event import (
    UserSkillCreatedEvent,
)
from shell.domain.user.aggregates.user_skill.events.user_skill_deleted_event import (
    UserSkillDeletedEvent,
)
from shell.domain.user.aggregates.user_skill.events.user_skill_updated_event import (
    UserSkillUpdatedEvent,
)
from shell.domain.user.aggregates.user_state.events.user_state_changed_event import (
    UserStateChangedEvent,
)
from shell.domain.user.aggregates.user_state.events.user_state_deleted_event import (
    UserStateDeletedEvent,
)
from shell.domain.user.aggregates.user_state.events.user_state_updated_event import (
    UserStateUpdatedEvent,
)


def build_event_registry() -> dict[str, type]:
    """Build registry mapping class names to event types for deserialization."""
    events: list[type] = [
        AgentConfigExecutionDeletedEvent,
        AgentConfigExecutionDeletedIntegrationEvent,
        AgentConfigExecutionUpdatedEvent,
        AgentConfigExecutionUpdatedIntegrationEvent,
        AgentConfigUpdatedEvent,
        AgentConfigUpdatedIntegrationEvent,
        AgentExecutionCreatedEvent,
        AgentExecutionCreatedIntegrationEvent,
        AgentExecutionDeletedEvent,
        AgentExecutionDeletedIntegrationEvent,
        AgentExecutionUpdatedEvent,
        AgentExecutionUpdatedIntegrationEvent,
        AgentSkillExecutionCreatedEvent,
        AgentSkillExecutionCreatedIntegrationEvent,
        AgentSkillExecutionDeletedEvent,
        AgentSkillExecutionDeletedIntegrationEvent,
        AgentSkillExecutionUpdatedEvent,
        AgentSkillExecutionUpdatedIntegrationEvent,
        EdgeExecutionCreatedEvent,
        EdgeExecutionCreatedIntegrationEvent,
        EdgeExecutionDeletedEvent,
        EdgeExecutionDeletedIntegrationEvent,
        EdgeExecutionUpdatedEvent,
        EdgeExecutionUpdatedIntegrationEvent,
        EdgeLinkExecutionCreatedEvent,
        EdgeLinkExecutionCreatedIntegrationEvent,
        EdgeLinkExecutionDeletedEvent,
        EdgeLinkExecutionDeletedIntegrationEvent,
        EdgeLinkExecutionUpdatedEvent,
        EdgeLinkExecutionUpdatedIntegrationEvent,
        GraphDefinitionCreatedEvent,
        GraphDefinitionCreatedIntegrationEvent,
        GraphDefinitionDeletedEvent,
        GraphDefinitionDeletedIntegrationEvent,
        GraphDefinitionEmbeddingCreatedEvent,
        GraphDefinitionEmbeddingCreatedIntegrationEvent,
        GraphDefinitionEmbeddingDeletedEvent,
        GraphDefinitionEmbeddingDeletedIntegrationEvent,
        GraphDefinitionEmbeddingUpdatedEvent,
        GraphDefinitionEmbeddingUpdatedIntegrationEvent,
        GraphDefinitionUpdatedEvent,
        GraphDefinitionUpdatedIntegrationEvent,
        GraphExecutionCreatedEvent,
        GraphExecutionCreatedIntegrationEvent,
        GraphExecutionDeletedEvent,
        GraphExecutionDeletedIntegrationEvent,
        GraphExecutionStateChangedEvent,
        GraphExecutionStateChangedIntegrationEvent,
        GraphExecutionStateDeletedEvent,
        GraphExecutionStateDeletedIntegrationEvent,
        GraphExecutionStateUpdatedEvent,
        GraphExecutionStateUpdatedIntegrationEvent,
        GraphExecutionUpdatedEvent,
        GraphExecutionUpdatedIntegrationEvent,
        MessageRouterCreatedEvent,
        MessageRouterCreatedIntegrationEvent,
        MessageRouterDeletedEvent,
        MessageRouterDeletedIntegrationEvent,
        MessageRouterUpdatedEvent,
        MessageRouterUpdatedIntegrationEvent,
        NodeDefinitionCreatedEvent,
        NodeDefinitionCreatedIntegrationEvent,
        NodeDefinitionDeletedEvent,
        NodeDefinitionDeletedIntegrationEvent,
        NodeDefinitionUpdatedEvent,
        NodeDefinitionUpdatedIntegrationEvent,
        NodeExecutionCreatedEvent,
        NodeExecutionCreatedIntegrationEvent,
        NodeExecutionDeletedEvent,
        NodeExecutionDeletedIntegrationEvent,
        NodeExecutionStateChangedEvent,
        NodeExecutionStateChangedIntegrationEvent,
        NodeExecutionStateDeletedEvent,
        NodeExecutionStateDeletedIntegrationEvent,
        NodeExecutionStateUpdatedEvent,
        NodeExecutionStateUpdatedIntegrationEvent,
        NodeExecutionUpdatedEvent,
        NodeExecutionUpdatedIntegrationEvent,
        NodeLinkDefinitionCreatedEvent,
        NodeLinkDefinitionCreatedIntegrationEvent,
        NodeLinkDefinitionDeletedEvent,
        NodeLinkDefinitionDeletedIntegrationEvent,
        NodeLinkDefinitionUpdatedEvent,
        NodeLinkDefinitionUpdatedIntegrationEvent,
        NodeLinkExecutionCreatedEvent,
        NodeLinkExecutionCreatedIntegrationEvent,
        NodeLinkExecutionDeletedEvent,
        NodeLinkExecutionDeletedIntegrationEvent,
        NodeLinkExecutionUpdatedEvent,
        NodeLinkExecutionUpdatedIntegrationEvent,
        ProjectCreatedEvent,
        ProjectCreatedIntegrationEvent,
        ProjectDeletedEvent,
        ProjectDeletedIntegrationEvent,
        ProjectSkillCreatedEvent,
        ProjectSkillCreatedIntegrationEvent,
        ProjectSkillDeletedEvent,
        ProjectSkillDeletedIntegrationEvent,
        ProjectSkillUpdatedEvent,
        ProjectSkillUpdatedIntegrationEvent,
        ProjectStateChangedEvent,
        ProjectStateChangedIntegrationEvent,
        ProjectStateDeletedEvent,
        ProjectStateDeletedIntegrationEvent,
        ProjectStateUpdatedEvent,
        ProjectStateUpdatedIntegrationEvent,
        ProjectUpdatedEvent,
        ProjectUpdatedIntegrationEvent,
        RunnerConfigCreatedEvent,
        RunnerConfigCreatedIntegrationEvent,
        RunnerConfigDeletedEvent,
        RunnerConfigDeletedIntegrationEvent,
        RunnerConfigUpdatedEvent,
        RunnerConfigUpdatedIntegrationEvent,
        SchedulerDefinitionCreatedEvent,
        SchedulerDefinitionCreatedIntegrationEvent,
        SchedulerDefinitionDeletedEvent,
        SchedulerDefinitionDeletedIntegrationEvent,
        SchedulerDefinitionUpdatedEvent,
        SchedulerDefinitionUpdatedIntegrationEvent,
        SchedulerExecutionCompletedEvent,
        SchedulerExecutionCompletedIntegrationEvent,
        SchedulerExecutionDeletedEvent,
        SchedulerExecutionDeletedIntegrationEvent,
        SchedulerExecutionFailedEvent,
        SchedulerExecutionFailedIntegrationEvent,
        SchedulerExecutionSkippedEvent,
        SchedulerExecutionSkippedIntegrationEvent,
        SchedulerExecutionStartedEvent,
        SchedulerExecutionStartedIntegrationEvent,
        SchedulerExecutionUpdatedEvent,
        SchedulerExecutionUpdatedIntegrationEvent,
        SchedulerJobCreatedEvent,
        SchedulerJobCreatedIntegrationEvent,
        SchedulerJobDeletedEvent,
        SchedulerJobDeletedIntegrationEvent,
        SchedulerJobUpdatedEvent,
        SchedulerJobUpdatedIntegrationEvent,
        SessionClosedEvent,
        SessionClosedIntegrationEvent,
        SessionDeletedEvent,
        SessionDeletedIntegrationEvent,
        SessionExecutionCreatedEvent,
        SessionExecutionCreatedIntegrationEvent,
        SessionExecutionDeletedEvent,
        SessionExecutionDeletedIntegrationEvent,
        SessionExecutionStateCreatedEvent,
        SessionExecutionStateCreatedIntegrationEvent,
        SessionExecutionStateDeletedEvent,
        SessionExecutionStateDeletedIntegrationEvent,
        SessionExecutionStateUpdatedEvent,
        SessionExecutionStateUpdatedIntegrationEvent,
        SessionExecutionUpdatedEvent,
        SessionExecutionUpdatedIntegrationEvent,
        SessionOpenedEvent,
        SessionOpenedIntegrationEvent,
        SessionStateChangedEvent,
        SessionStateChangedIntegrationEvent,
        SessionStateDeletedEvent,
        SessionStateDeletedIntegrationEvent,
        SessionStateUpdatedEvent,
        SessionStateUpdatedIntegrationEvent,
        SessionUpdatedEvent,
        SessionUpdatedIntegrationEvent,
        TaskExecutionCreatedEvent,
        TaskExecutionCreatedIntegrationEvent,
        TaskExecutionDeletedEvent,
        TaskExecutionDeletedIntegrationEvent,
        TaskExecutionStateCreatedEvent,
        TaskExecutionStateCreatedIntegrationEvent,
        TaskExecutionStateDeletedEvent,
        TaskExecutionStateDeletedIntegrationEvent,
        TaskExecutionStateUpdatedEvent,
        TaskExecutionStateUpdatedIntegrationEvent,
        TaskExecutionUpdatedEvent,
        TaskExecutionUpdatedIntegrationEvent,
        UserCreatedEvent,
        UserCreatedIntegrationEvent,
        UserDeletedEvent,
        UserDeletedIntegrationEvent,
        UserExecutionCreatedEvent,
        UserExecutionCreatedIntegrationEvent,
        UserExecutionDeletedEvent,
        UserExecutionDeletedIntegrationEvent,
        UserExecutionStateCreatedEvent,
        UserExecutionStateCreatedIntegrationEvent,
        UserExecutionStateDeletedEvent,
        UserExecutionStateDeletedIntegrationEvent,
        UserExecutionStateUpdatedEvent,
        UserExecutionStateUpdatedIntegrationEvent,
        UserExecutionUpdatedEvent,
        UserExecutionUpdatedIntegrationEvent,
        UserSkillCreatedEvent,
        UserSkillCreatedIntegrationEvent,
        UserSkillDeletedEvent,
        UserSkillDeletedIntegrationEvent,
        UserSkillUpdatedEvent,
        UserSkillUpdatedIntegrationEvent,
        UserStateChangedEvent,
        UserStateChangedIntegrationEvent,
        UserStateDeletedEvent,
        UserStateDeletedIntegrationEvent,
        UserStateUpdatedEvent,
        UserStateUpdatedIntegrationEvent,
        UserUpdatedEvent,
        UserUpdatedIntegrationEvent,
        WorkflowCreatedEvent,
        WorkflowCreatedIntegrationEvent,
        WorkflowDeletedEvent,
        WorkflowDeletedIntegrationEvent,
        WorkflowStateChangedEvent,
        WorkflowStateChangedIntegrationEvent,
        WorkflowStateDeletedEvent,
        WorkflowStateDeletedIntegrationEvent,
        WorkflowStateUpdatedEvent,
        WorkflowStateUpdatedIntegrationEvent,
        WorkflowUpdatedEvent,
        WorkflowUpdatedIntegrationEvent,
    ]

    return {event.__name__: event for event in events}
