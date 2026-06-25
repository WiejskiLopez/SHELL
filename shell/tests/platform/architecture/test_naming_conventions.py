from __future__ import annotations

import ast
import re

from _arch_helpers import (
    BASE,
    find_classes,
    has_abbreviation,
    is_frozen_dataclass,
    is_magic,
    iter_py_files,
    parse_file,
    to_snake_case,
)

# ── 1. Classes use PascalCase ─────────────────────────────────────


def test_classes_use_pascal_case() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if node.name[0].islower():
                violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, (
        "All classes must use PascalCase:\n"
        + "\n".join(violations)
    )


# ── 2. Functions/methods use snake_case ──────────────────────────

_ALLOWED_CAPS_METHODS = frozenset({
    "ID", "DTO", "VO", "HTTP", "JSON", "YAML", "XML", "API", "URL", "URI",
    "DB", "SQL", "ORM", "CLI", "GUI", "UID", "UUID", "SHA", "AES", "RSA",
})


def test_methods_use_snake_case() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                if is_magic(name):
                    continue
                if name.startswith("_") and not name.startswith("__"):
                    name = name[1:]
                if name.startswith("__"):
                    continue
                if name in _ALLOWED_CAPS_METHODS:
                    continue
                if name[0].isupper():
                    violations.append(f"{path.relative_to(BASE)}: function {name}")
    assert not violations, (
        "Functions/methods must use snake_case:\n"
        + "\n".join(violations)
    )


# ── 3. File names are snake_case ──────────────────────────────────


def test_file_names_are_snake_case() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        name = path.stem
        if not re.match(r"^[a-z0-9_]+$", name):
            violations.append(f"{path.relative_to(BASE)}")
    assert not violations, (
        "Python file names must be snake_case:\n"
        + "\n".join(violations)
    )


# ── 4. File name matches the main class in the file ───────────────


_KNOWN_FILENAME_MISMATCH: frozenset[str] = frozenset({
    "tests/scheduling/unit/domain/test_scheduler_repositories.py: main class is TestInMemorySchedulerDefinitionRepository (expected test_in_memory_scheduler_definition_repository.py)",
    "tests/platform/unit/application/test_outbox.py: main class is TestInMemoryOutboxStore (expected test_in_memory_outbox_store.py)",
    "tests/platform/unit/domain/test_value_objects_version.py: main class is TestVersion (expected test_version.py)",
    "tests/infrastructure/platform/test_mappers_round_trip.py: main class is TestGraphExecutionMapper (expected test_graph_execution_mapper.py)",
    "tests/execution/unit/application/test_graph_node_execution_result_handler.py: main class is TestGraphNodeExecutionResultHandlerHappyPath (expected test_graph_node_execution_result_handler_happy_path.py)",
    "tests/execution/unit/domain/test_envelope_lifecycle_service.py: main class is TestShouldExpire (expected test_should_expire.py)",
    "tests/execution/unit/domain/test_graph_execution_counters.py: main class is TestLoopCounter (expected test_loop_counter.py)",
    "tests/execution/unit/domain/test_graph_execution_routing_service.py: main class is TestResolveTargetGraphNodeExecution (expected test_resolve_target_graph_node_execution.py)",
    "tests/execution/unit/domain/test_graph_execution_state_input.py: main class is TestGraphExecutionStateInputUpdate (expected test_graph_execution_state_input_update.py)",
    "tests/execution/unit/domain/test_graph_execution_state_output.py: main class is TestGraphExecutionStateOutputUpdate (expected test_graph_execution_state_output_update.py)",
    "tests/execution/unit/domain/test_graph_node_execution_policy.py: main class is TestFailFastGraphNodeExecutionPolicy (expected test_fail_fast_graph_node_execution_policy.py)",
    "tests/execution/unit/domain/test_task_execution_entity.py: main class is TestTaskExecution (expected test_task_execution.py)",
    "tests/execution/unit/domain/test_transition_based_navigator.py: main class is TestTransitionBasedGraphNodeExecutionNavigatorNextAfter (expected test_transition_based_graph_node_execution_navigator_next_after.py)",
    "tests/execution/unit/domain/test_value_objects_task_execution_body.py: main class is TestTaskExecutionBody (expected test_task_execution_body.py)",
    "tests/execution/unit/domain/test_workflow_entity.py: main class is TestWorkflow (expected test_workflow.py)",
    "tests/execution/integration/process/test_subprocess_runner.py: main class is TestSubprocessGraphNodeExecutionProcessRunner (expected test_subprocess_graph_node_execution_process_runner.py)",
    "infrastructure/scheduling/persistence/sql/models/scheduler_definition.py: main class is SchedulerDefinitionModel (expected scheduler_definition_model.py)",
    "infrastructure/scheduling/persistence/sql/models/scheduler_execution.py: main class is SchedulerExecutionModel (expected scheduler_execution_model.py)",
    "infrastructure/platform/default_implementations/sub_graph_defaults.py: main class is DefaultSubGraphObserver (expected default_sub_graph_observer.py)",
    "infrastructure/platform/persistence/sql_alchemy_uow.py: main class is SqlAlchemyUnitOfWork (expected sql_alchemy_unit_of_work.py)",
    "infrastructure/platform/serialization/event_serializer.py: main class is DomainEventSerializer (expected domain_event_serializer.py)",
    "infrastructure/platform/persistence/sql/rag_search/rag_search_strategy.py: main class is InMemoryRagSearchStrategy (expected in_memory_rag_search_strategy.py)",
    "infrastructure/execution/filesystem/envelope_archive_fs.py: main class is FileSystemEnvelopeArchive (expected file_system_envelope_archive.py)",
    "infrastructure/execution/filesystem/task_execution_loader.py: main class is FileSystemTaskLoader (expected file_system_task_loader.py)",
    "infrastructure/execution/process/subprocess_runner.py: main class is SubprocessGraphNodeExecutionProcessRunner (expected subprocess_graph_node_execution_process_runner.py)",
    "infrastructure/execution/persistence/sql/models/envelope.py: main class is EnvelopeModel (expected envelope_model.py)",
    "infrastructure/execution/persistence/sql/models/envelope_event.py: main class is EnvelopeEventModel (expected envelope_event_model.py)",
    "infrastructure/execution/persistence/sql/models/graph_execution.py: main class is GraphExecutionModel (expected graph_execution_model.py)",
    "infrastructure/execution/persistence/sql/models/graph_execution_state_input.py: main class is GraphExecutionStateInputModel (expected graph_execution_state_input_model.py)",
    "infrastructure/execution/persistence/sql/models/graph_execution_state_output.py: main class is GraphExecutionStateOutputModel (expected graph_execution_state_output_model.py)",
    "infrastructure/execution/persistence/sql/models/graph_node_execution.py: main class is GraphNodeExecutionModel (expected graph_node_execution_model.py)",
    "infrastructure/execution/persistence/sql/models/graph_node_execution_result.py: main class is GraphNodeExecutionResultModel (expected graph_node_execution_result_model.py)",
    "infrastructure/execution/persistence/sql/models/graph_node_execution_state.py: main class is GraphNodeExecutionStateModel (expected graph_node_execution_state_model.py)",
    "infrastructure/execution/persistence/sql/models/graph_node_execution_state_input.py: main class is GraphNodeExecutionStateInputModel (expected graph_node_execution_state_input_model.py)",
    "infrastructure/execution/persistence/sql/models/graph_node_execution_state_output.py: main class is GraphNodeExecutionStateOutputModel (expected graph_node_execution_state_output_model.py)",
    "infrastructure/execution/persistence/sql/models/graph_node_transition_execution.py: main class is GraphNodeTransitionExecutionModel (expected graph_node_transition_execution_model.py)",
    "infrastructure/execution/persistence/sql/models/session.py: main class is SessionModel (expected session_model.py)",
    "infrastructure/execution/persistence/sql/models/task_execution.py: main class is TaskExecutionModel (expected task_execution_model.py)",
    "infrastructure/execution/persistence/sql/models/task_execution_state_input.py: main class is TaskExecutionStateInputModel (expected task_execution_state_input_model.py)",
    "infrastructure/execution/persistence/sql/models/task_execution_state_output.py: main class is TaskExecutionStateOutputModel (expected task_execution_state_output_model.py)",
    "infrastructure/execution/persistence/sql/models/workflow.py: main class is WorkflowModel (expected workflow_model.py)",
    "infrastructure/definition/persistence/sql/models/graph_definition.py: main class is GraphDefinitionModel (expected graph_definition_model.py)",
    "infrastructure/definition/persistence/sql/models/graph_node_definition.py: main class is GraphNodeDefinitionModel (expected graph_node_definition_model.py)",
    "infrastructure/definition/persistence/sql/models/graph_node_transition_definition.py: main class is GraphNodeTransitionDefinitionModel (expected graph_node_transition_definition_model.py)",
    "infrastructure/definition/persistence/sql/models/rag_chunk.py: main class is RagChunkModel (expected rag_chunk_model.py)",
    "infrastructure/definition/persistence/sql/models/rag_document.py: main class is RagDocumentModel (expected rag_document_model.py)",
    "infrastructure/definition/persistence/sql/models/runner_config.py: main class is RunnerConfigModel (expected runner_config_model.py)",
    "infrastructure/definition/persistence/sql/services/graph_definition_query_service.py: main class is SqlGraphDefinitionQueryService (expected sql_graph_definition_query_service.py)",
    "infrastructure/platform/persistence/sql/models/audit_event.py: main class is AuditEventModel (expected audit_event_model.py)",
    "infrastructure/platform/persistence/sql/models/inbox_event.py: main class is InboxEventModel (expected inbox_event_model.py)",
    "infrastructure/platform/persistence/sql/models/outbox_event.py: main class is OutboxEventModel (expected outbox_event_model.py)",
    "framework/platform/api/middleware/correlation_id.py: main class is CorrelationIdMiddleware (expected correlation_id_middleware.py)",
    "framework/execution/orchestration/sync_workflow_runner.py: main class is SyncWorkflowResult (expected sync_workflow_result.py)",
    "domain/scheduling/services/dual_layer_dispatcher.py: main class is Inbox (expected inbox.py)",
    "domain/scheduling/services/pending_graph_finder.py: main class is GraphExecutionRepository (expected graph_execution_repository.py)",
    "domain/scheduling/value_objects/ids.py: main class is SchedulerDefinitionId (expected scheduler_definition_id.py)",
    "domain/platform/ports/identity.py: main class is IdGenerator (expected id_generator.py)",
    "domain/platform/ports/log.py: main class is Logger (expected logger.py)",
    "domain/platform/ports/time.py: main class is Clock (expected clock.py)",
    "domain/execution/ports/sub_graph_policy.py: main class is Decision (expected decision.py)",
    "domain/execution/ports/sub_graph_security.py: main class is Scope (expected scope.py)",
    "domain/execution/services/graph_execution_routing_service.py: main class is GraphExcetutionRoutingService (expected graph_excetution_routing_service.py)",
    "domain/execution/services/graph_node_execution_output_interpreter.py: main class is OutputDecision (expected output_decision.py)",
    "domain/execution/value_objects/graph_execution_definition.py: main class is GraphNodeExecutionDefinition (expected graph_node_execution_definition.py)",
    "domain/execution/services/graph_node_execution_navigator/transition_based_navigator.py: main class is TransitionBasedGraphNodeExecutionNavigator (expected transition_based_graph_node_execution_navigator.py)",
    "domain/execution/aggregates/graph_execution/ports/sub_graph_compensation.py: main class is CompensationDecision (expected compensation_decision.py)",
    "domain/definition/services/rag_index_service.py: main class is Embedder (expected embedder.py)",
    "bootstrap/execution/cli/command/command.py: main class is RunnableCommand (expected runnable_command.py)",
    "application/platform/ports/config.py: main class is AppConfig (expected app_config.py)",
    "application/platform/ports/filesystem.py: main class is TaskExecutionLoader (expected task_execution_loader.py)",
    "application/platform/ports/logging.py: main class is Logger (expected logger.py)",
    "application/platform/ports/messaging.py: main class is EventPublisher (expected event_publisher.py)",
    "application/platform/ports/time.py: main class is Clock (expected clock.py)",
    "application/execution/commands/envelope_commands.py: main class is ArchiveEnvelopeCommand (expected archive_envelope_command.py)",
    "application/execution/commands/task_execution_commands.py: main class is ImportTaskExecutionCommand (expected import_task_execution_command.py)",
    "application/execution/dto/envelope.py: main class is EnvelopeDto (expected envelope_dto.py)",
    "application/execution/dto/graph_execution.py: main class is GraphExecutionDto (expected graph_execution_dto.py)",
    "application/execution/dto/graph_node_execution.py: main class is GraphNodeExecutionDto (expected graph_node_execution_dto.py)",
    "application/execution/dto/graph_node_execution_result.py: main class is GraphNodeExecutionResultDto (expected graph_node_execution_result_dto.py)",
    "application/execution/dto/graph_node_execution_state.py: main class is GraphNodeExecutionStateDto (expected graph_node_execution_state_dto.py)",
    "application/execution/dto/graph_node_execution_state_input.py: main class is GraphNodeExecutionStateInputDto (expected graph_node_execution_state_input_dto.py)",
    "application/execution/dto/graph_node_execution_state_output.py: main class is GraphNodeExecutionStateOutputDto (expected graph_node_execution_state_output_dto.py)",
    "application/execution/dto/session.py: main class is SessionDto (expected session_dto.py)",
    "application/execution/dto/task_execution.py: main class is TaskExecutionDto (expected task_execution_dto.py)",
    "application/execution/dto/task_execution_state_input.py: main class is TaskExecutionStateInputDto (expected task_execution_state_input_dto.py)",
    "application/execution/dto/task_execution_state_output.py: main class is TaskExecutionStateOutputDto (expected task_execution_state_output_dto.py)",
    "application/execution/dto/workflow.py: main class is WorkflowDto (expected workflow_dto.py)",
    "application/execution/event_handlers/envelope_routed_handler.py: main class is ArchiveOnDeliveredHandler (expected archive_on_delivered_handler.py)",
    "application/execution/event_handlers/graph_node_execution_requested_handler.py: main class is GraphNodeExecutionWorker (expected graph_node_execution_worker.py)",
    "application/execution/event_handlers/task_execution_created_handler.py: main class is BuildGraphExecutionOnTaskExecutionCreatedEvent (expected build_graph_execution_on_task_execution_created_event.py)",
    "application/execution/queries/envelope_queries.py: main class is GetEnvelopesByWorkflowQuery (expected get_envelopes_by_workflow_query.py)",
    "application/execution/queries/graph_node_execution_queries.py: main class is GetGraphNodeExecutionResultQuery (expected get_graph_node_execution_result_query.py)",
    "application/execution/queries/session_queries.py: main class is GetSessionHistoryQuery (expected get_session_history_query.py)",
    "application/execution/queries/workflow_queries.py: main class is GetWorkflowQuery (expected get_workflow_query.py)",
    "application/execution/strategies/graph_node_execution_strategy/protocol.py: main class is GraphNodeExecutionStrategy (expected graph_node_execution_strategy.py)",
    "application/definition/commands/config_commands.py: main class is BootstrapRunnerConfigCommand (expected bootstrap_runner_config_command.py)",
    "application/definition/commands/rag_commands.py: main class is IndexDocumentCommand (expected index_document_command.py)",
    "application/definition/dto/graph_definition.py: main class is GraphDefinitionDto (expected graph_definition_dto.py)",
    "application/definition/dto/graph_node_definition.py: main class is GraphNodeDefinitionDto (expected graph_node_definition_dto.py)",
    "application/definition/dto/rag_chunk.py: main class is RagChunkDto (expected rag_chunk_dto.py)",
    "application/definition/dto/runner_config.py: main class is RunnerConfigDto (expected runner_config_dto.py)",
    "application/definition/queries/config_queries.py: main class is GetRunnerConfigQuery (expected get_runner_config_query.py)",
    "application/definition/queries/rag_queries.py: main class is SearchSimilarQuery (expected search_similar_query.py)",
})


def test_filename_matches_class_name() -> None:
    violations: list[str] = []
    _SOFT_AREAS = frozenset({"/tests/", "/migrations/versions/", "/config/seed/"})
    for path in iter_py_files(BASE):
        rel = path.relative_to(BASE).as_posix()
        if any(a in rel for a in _SOFT_AREAS):
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        classes = list(find_classes(tree))
        if not classes:
            continue
        main_class = max(classes, key=lambda c: len(c.body))
        if main_class.name.startswith("_"):
            continue
        expected_stem = to_snake_case(main_class.name)
        if path.stem != expected_stem and path.stem != expected_stem.rstrip("_"):
            key = f"{rel}: main class is {main_class.name} (expected {expected_stem}.py)"
            if key not in _KNOWN_FILENAME_MISMATCH:
                violations.append(key)
    assert not violations, (
        "File name should match the main class (PascalCase -> snake_case):\n"
        + "\n".join(violations)
    )


# ── 5. Constants use UPPER_CASE ────────────────────────────────────


def test_constants_use_upper_case() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        rel = path.relative_to(BASE).as_posix()
        if rel.startswith("tests/"):
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if name.startswith("_"):
                            name = name.lstrip("_")
                        if name.isupper():
                            continue
                        if name[0].isupper() and not name.startswith("__"):
                            if isinstance(node.value, (ast.Constant, ast.List, ast.Dict, ast.Set, ast.Tuple)):
                                violations.append(f"{rel}: {target.id}")
    assert not violations, (
        "Module-level constants must use UPPER_CASE:\n"
        + "\n".join(violations)
    )


# ── 6. No abbreviations in names ──────────────────────────────────

_KNOWN_ABBREVIATION_VIOLATIONS: frozenset[str] = frozenset({
    "infrastructure/platform/identity/uuid_id_generator.py: function new_runner_config_id",
    "infrastructure/platform/persistence/sql_alchemy_uow.py: function runner_config_repository",
    "infrastructure/platform/persistence/memory/fake_id_generator.py: function new_runner_config_id",
    "infrastructure/platform/persistence/memory/in_memory_query_services.py: function get_runner_config",
    "infrastructure/platform/persistence/memory/in_memory_unit_of_work.py: function runner_config_repository",
    "infrastructure/definition/persistence/sql/mappers/graph_definition_mapper.py: function graph_definition_model_to_dto",
    "infrastructure/definition/persistence/sql/services/runner_config_query_service.py: function get_runner_config",
    "framework/platform/cli/parser.py: function parse_args",
    "domain/scheduling/aggregates/scheduler_definition/scheduler_definition.py: function trigger_config",
    "domain/scheduling/aggregates/scheduler_definition/scheduler_definition.py: function action_config",
    "domain/scheduling/aggregates/scheduler_job/scheduler_job.py: function config",
    "domain/projekt/aggregates/project/project.py: function repo_url",
    "domain/platform/ports/identity.py: function new_runner_config_id",
    "domain/execution/ports/runner_config_provider.py: function get_runner_config",
    "domain/execution/aggregates/agent_config_execution/agent_config_execution.py: function update_config",
    "domain/execution/aggregates/agent_config_execution/agent_config_execution.py: function config",
    "domain/execution/aggregates/agent_execution/agent_execution.py: function config_snapshot",
    "application/platform/mappers/mappers.py: function task_execution_to_dto",
    "application/platform/mappers/mappers.py: function workflow_to_dto",
    "application/platform/mappers/mappers.py: function envelope_to_dto",
    "application/platform/mappers/mappers.py: function node_result_to_dto",
    "application/platform/mappers/mappers.py: function runner_config_to_dto",
    "application/platform/mappers/mappers.py: function task_execution_input_payload_to_dto",
    "application/platform/mappers/mappers.py: function task_execution_output_payload_to_dto",
    "application/platform/mappers/mappers.py: function graph_node_execution_state_input_to_dto",
    "application/platform/mappers/mappers.py: function graph_node_execution_state_output_to_dto",
    "application/platform/ports/unit_of_work.py: function runner_config_repository",
    "application/definition/ports/queries/runner_config_query_service.py: function get_runner_config",
})


def test_no_abbreviations_in_class_names() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            if has_abbreviation(node.name):
                key = f"{path.relative_to(BASE)}: class {node.name}"
                if key not in _KNOWN_ABBREVIATION_VIOLATIONS:
                    violations.append(key)
    assert not violations, (
        "Class names must not use abbreviations:\n"
        + "\n".join(violations)
    )


def test_no_abbreviations_in_function_names() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE):
        rel = path.relative_to(BASE).as_posix()
        if rel.startswith("tests/"):
            continue
        tree = parse_file(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if is_magic(node.name):
                    continue
                if node.name.startswith("_"):
                    continue
                if has_abbreviation(node.name):
                    key = f"{rel}: function {node.name}"
                    if key not in _KNOWN_ABBREVIATION_VIOLATIONS:
                        violations.append(key)
    assert not violations, (
        "Function/method names in production code must not use abbreviations:\n"
        + "\n".join(violations)
    )


# ── 7. Handler classes end with 'Handler' ─────────────────────────


def test_handler_classes_end_with_handler() -> None:
    violations: list[str] = []
    for handler_dir in [BASE / "application" / "command_handlers",
                        BASE / "application" / "query_handlers",
                        BASE / "application" / "event_handlers"]:
        if not handler_dir.exists():
            continue
        for path in iter_py_files(handler_dir):
            tree = parse_file(path)
            if tree is None:
                continue
            for node in find_classes(tree):
                if not node.name.endswith("Handler"):
                    violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, (
        "Handler classes must end with 'Handler':\n"
        + "\n".join(violations)
    )


# ── 8. Repository port classes end with 'Repository' ──────────────


def test_repository_ports_end_with_repository() -> None:
    violations: list[str] = []
    for repos_dir in (BASE / "domain").rglob("repositories"):
        if not repos_dir.is_dir():
            continue
        for path in iter_py_files(repos_dir):
            tree = parse_file(path)
            if tree is None:
                continue
            for node in find_classes(tree):
                if not node.name.endswith("Repository"):
                    violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, (
        "Repository port classes must end with 'Repository':\n"
        + "\n".join(violations)
    )


# ── 9. Entity classes use suffix naming where applicable ──────────

_ENTITY_SUFFIXES = frozenset({"Entity", "Event", "Dto", "Model", "Adapter", "Mapper", "Service", "Specification"})


def test_domain_entity_no_suffix_overload() -> None:
    violations: list[str] = []
    for path in iter_py_files(BASE / "domain"):
        tree = parse_file(path)
        if tree is None:
            continue
        for node in find_classes(tree):
            # Aggregate root entities should not have "Entity" suffix
            if node.name.endswith("Entity"):
                for base_node in node.bases:
                    if isinstance(base_node, ast.Name) and base_node.id in {"AggregateRoot", "Entity"}:
                        violations.append(f"{path.relative_to(BASE)}: class {node.name}")
    assert not violations, (
        "Direct entity/aggregate classes should not have 'Entity' suffix in their name:\n"
        + "\n".join(violations)
    )
