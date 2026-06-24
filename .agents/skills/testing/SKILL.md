---
name: testing
description: Strategia testowania w architekturze hexagonalnej DDD — piramida testów dla CQRS, testowanie jednostkowe domeny w izolacji, testy integracyjne z bazą, testy architektury, testy end-to-end. Używaj gdy piszesz testy dla nowej funkcjonalności, refaktoryzujesz testy, albo potrzebujesz strategii pokrycia.
---

# Testing Strategy w Enterprise DDD

## 1. Piramida Testów dla DDD/CQRS

```
        ╱╲
       ╱ E2E ╲           ← kilka kluczowych scenariuszy
      ╱────────╲
     ╱ Integrac. ╲       ← testy z bazą, API, adapterami
    ╱──────────────╲
   ╱ Unit (Domain)   ╲    ← większość testów — domain w isolation
  ╱────────────────────╲
 ╱ Arch + Static Check  ╲  ← importy, warstwy, typy
╱────────────────────────╲
```

| Poziom | Cel | Prędkość | Ilość |
|--------|-----|----------|-------|
| Arch | Reguły architektoniczne | Błyskawiczne | Kilka |
| Unit | Logika domenowa w isolation | Bardzo szybkie | Większość |
| Integracja | Adaptery + baza + API | Wolne | Kilkanaście |
| E2E | Kluczowe ścieżki | Bardzo wolne | Kilka |

## 2. Testy Jednostkowe Domeny (Domain Tests)

Testują czystą logikę domenową — agregaty, encje, VO, Domain Services, Specyfikacje. **Bez infrastruktury**.

```python
class TestExecution:
    """Testy jednostkowe agregatu Execution — czysta domena, brak mocków."""

    def test_start_sets_status_to_running(self, execution_factory: ExecutionFactory) -> None:
        execution = execution_factory.create_pending()
        execution.start()
        assert execution.status == ExecutionStatus.RUNNING

    def test_start_emits_execution_started_event(self, execution_factory: ExecutionFactory) -> None:
        execution = execution_factory.create_pending()
        execution.start()
        events = execution.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], ExecutionStartedEvent)

    def test_complete_sets_status_to_completed(self, execution_factory: ExecutionFactory) -> None:
        execution = execution_factory.create_running()
        execution.complete()
        assert execution.status == ExecutionStatus.COMPLETED

    def test_cancel_raises_when_already_completed(self, execution_factory: ExecutionFactory) -> None:
        execution = execution_factory.create_completed()
        with pytest.raises(InvalidStateError):
            execution.cancel()
```

## 3. Testy Domain Services

Domain Service testowany z prawdziwymi agregatami i VO (bez mocków). Jeśli service ma porty — używamy prostych fake'ów.

```python
class TestPricingService:
    def test_calculate_total_applies_discount(self) -> None:
        service = PricingService()
        items = [OrderItem(price=Money(100, "USD"), quantity=2)]
        discount = Discount(rate=Decimal("0.1"))
        result = service.calculate_total(items, discount)
        assert result == Money(180, "USD")

    def test_calculate_total_no_discount(self) -> None:
        service = PricingService()
        items = [OrderItem(price=Money(100, "USD"), quantity=2)]
        result = service.calculate_total(items, Discount.none())
        assert result == Money(200, "USD")
```

## 4. Testy Handlerów (Application Layer)

Handler testowany z **InMemory** implementacjami repozytoriów — isolacja od bazy danych.

```python
class TestCreateExecutionHandler:
    async def test_create_execution_success(self) -> None:
        # Given
        graph_repo = InMemoryGraphRepository()
        execution_repo = InMemoryExecutionRepository()
        uow = InMemoryUnitOfWork()
        factory = ExecutionFactory(...)
        handler = CreateExecutionHandler(factory, graph_repo, execution_repo, uow)
        graph = GraphFactory.create_active()
        await graph_repo.add(graph)

        # When
        cmd = CreateExecutionCommand(graph_id=str(graph.id))
        await handler.handle(cmd)

        # Then
        executions = await execution_repo.find(AnySpecification())
        assert len(executions) == 1
        assert executions[0].status == ExecutionStatus.PENDING
```

## 5. Testy Integracyjne (Infrastructure)

Testują adaptery z prawdziwą bazą danych (SQLite w pamięci lub testowy PostgreSQL).

```python
@pytest.mark.integration
class TestSqlExecutionRepository:
    @pytest.fixture
    async def repository(self, db_session: AsyncSession) -> SqlExecutionRepository:
        mapper = ExecutionMapper()
        return SqlExecutionRepository(db_session, mapper)

    async def test_add_and_get(self, repository: SqlExecutionRepository, execution: Execution) -> None:
        await repository.add(execution)
        await repository.session.flush()
        result = await repository.get(execution.id)
        assert result.id == execution.id
        assert result.status == execution.status

    async def test_get_raises_not_found(self, repository: SqlExecutionRepository) -> None:
        with pytest.raises(ExecutionNotFoundError):
            await repository.get(ExecutionId.generate())

    async def test_update(self, repository: SqlExecutionRepository, execution: Execution) -> None:
        await repository.add(execution)
        await repository.session.flush()
        execution.start()
        await repository.update(execution)
        await repository.session.flush()
        result = await repository.get(execution.id)
        assert result.status == ExecutionStatus.RUNNING
```

## 6. Testy Architektury

Weryfikują reguły architektoniczne — importy między warstwami, konwencje nazewnicze, obecność wymaganych elementów.

```python
# tests/architecture/test_layer_imports.py
class TestLayerImports:
    def test_domain_does_not_import_infrastructure(self) -> None:
        violations = []
        for module in find_python_modules("shell/domain"):
            imports = extract_imports(module)
            if any("shell.infrastructure" in i for i in imports):
                violations.append(module)
        assert not violations, f"Domain imports infrastructure: {violations}"

    def test_application_does_not_import_infrastructure(self) -> None:
        violations = []
        for module in find_python_modules("shell/application"):
            imports = extract_imports(module)
            if any("shell.infrastructure" in i for i in imports):
                violations.append(module)
        assert not violations, f"Application imports infrastructure: {violations}"

    def test_every_aggregate_has_factory(self) -> None:
        aggregates = find_aggregate_directories()
        for agg in aggregates:
            factory_path = f"shell/domain/{agg}/factories"
            assert exists(factory_path), f"Missing factory for aggregate {agg}"

    def test_every_repository_has_in_memory_impl(self) -> None:
        repos = find_repository_ports()
        for repo in repos:
            in_memory = repo.replace("repositories/", "repositories/in_memory_")
            assert exists(in_memory), f"Missing InMemory for {repo}"
```

## 7. Testy Mapperów (Round-trip)

Każdy mapper ma test round-trip — verify that `to_domain(to_model(x)) == x`.

```python
class TestExecutionMapper:
    def test_round_trip(self, execution: Execution) -> None:
        model = self.mapper.to_model(execution)
        result = self.mapper.to_domain(model)
        assert result.id == execution.id
        assert result.status == execution.status
        assert result.version == execution.version
        assert result.graph_id == execution.graph_id
        # events nie są mapowane
        assert result.pull_events() == []

    def test_nullable_fields(self, execution: Execution) -> None:
        execution_without_dates = Execution.restore(
            id=execution.id,
            graph_id=execution.graph_id,
            status=execution.status,
            version=execution.version,
            created_at=execution.created_at,
            updated_at=None,
        )
        model = self.mapper.to_model(execution_without_dates)
        assert model.updated_at is None
```

## 8. Testy Specyfikacji

```python
class TestActiveExecutionSpecification:
    def test_running_is_active(self, running_execution: Execution) -> None:
        spec = ActiveExecutionSpecification()
        assert spec.is_satisfied_by(running_execution)

    def test_completed_is_not_active(self, completed_execution: Execution) -> None:
        spec = ActiveExecutionSpecification()
        assert not spec.is_satisfied_by(completed_execution)

    def test_composition(self, running_execution: Execution) -> None:
        active = ActiveExecutionSpecification()
        timeout = TimeoutExecutionSpecification(Duration.hours(1))
        composed = active & timeout
        assert composed.is_satisfied_by(running_execution)
```

## 9. Testy E2E

Kluczowe ścieżki — pełny przepływ przez wszystkie warstwy.

```python
@pytest.mark.e2e
class TestCreateAndCompleteExecution:
    async def test_full_flow(self, async_client: AsyncClient) -> None:
        # Create graph
        graph_resp = await async_client.post("/api/graphs", json={"name": "test"})
        graph_id = graph_resp.json()["id"]

        # Create execution
        exec_resp = await async_client.post(
            f"/api/graphs/{graph_id}/executions",
        )
        execution_id = exec_resp.json()["id"]
        assert exec_resp.json()["status"] == "PENDING"

        # Start execution
        start_resp = await async_client.post(
            f"/api/executions/{execution_id}/start",
        )
        assert start_resp.json()["status"] == "RUNNING"

        # Complete execution
        complete_resp = await async_client.post(
            f"/api/executions/{execution_id}/complete",
        )
        assert complete_resp.json()["status"] == "COMPLETED"

        # Verify final state
        get_resp = await async_client.get(f"/api/executions/{execution_id}")
        assert get_resp.json()["status"] == "COMPLETED"
```

## 10. Konwencje Nazewnicze w Testach

```
tests/
├── architecture/           # Testy architektury
│   └── test_layer_imports.py
├── domain/                  # Testy jednostkowe domeny
│   └── execution/
│       ├── test_execution.py
│       ├── test_execution_factory.py
│       ├── test_execution_service.py
│       └── value_objects/
│           └── test_task_execution_name.py
├── application/             # Testy handlerów
│   └── execution/
│       ├── test_create_execution_handler.py
│       └── test_complete_execution_handler.py
├── infrastructure/          # Testy integracyjne
│   └── execution/
│       ├── test_sql_execution_repository.py
│       └── test_execution_mapper.py
└── e2e/                     # Testy end-to-end
    └── test_execution_flow.py
```

## 11. Fixture Strategy

- **Domain fixtures**: `tests/domain/conftest.py` — factory methods dla agregatów
- **Infrastructure fixtures**: `tests/infrastructure/conftest.py` — db_session, mapper
- **Application fixtures**: `tests/application/conftest.py` — handler + InMemory repos
- **E2E fixtures**: `tests/e2e/conftest.py` — async_client, baza testowa

## 12. Podsumowanie — Checklista

Pisząc testy:
- [ ] Domain testy — czysta domena, bez mocków
- [ ] Handler testy — z InMemory repozytoriami
- [ ] Mapper round-trip test — dla każdego mappera
- [ ] Specyfikacje — testy dla każdej reguły
- [ ] Architektura — testy warstw, importów, konwencji
- [ ] Integracyjne — z prawdziwą bazą (oznaczone `@pytest.mark.integration`)
- [ ] E2E — tylko kluczowe ścieżki (oznaczone `@pytest.mark.e2e`)
- [ ] Fixtures — scentralizowane w conftest.py
- [ ] Nazewnictwo zgodne z konwencją
- [ ] test_ przed nazwą funkcji i pliku
