---
name: validation
description: Zasady walidacji w architekturze hexagonalnej CQRS — walidacja strukturalna na granicy API (Pydantic), walidacja biznesowa w domenie, walidacja komend w aplikacji, reguły walidacji krzyżowej. Używaj gdy projektujesz walidację wejściową, definiujesz reguły dla komend, albo rozdzielasz walidację między warstwy.
---

# Validation w Enterprise DDD

## 1. Trzy Poziomy Walidacji

```
Warstwa API (Pydantic)    → strukturalna: typy, formaty, zakresy
Warstwa Aplikacji (Handler) → koordynacyjna: autoryzacja, stan systemu
Warstwa Domeny (Agregat/VO)  → biznesowa: invarianty, reguły, proces
```

## 2. Walidacja Strukturalna — API (Pydantic)

Na granicy API — walidacja typów, formatów, zakresów. Używamy Pydantic.

```python
# shell/framework/api/requests/create_execution_request.py
from pydantic import BaseModel, Field

class CreateExecutionRequest(BaseModel):
    graph_id: str = Field(..., min_length=1, pattern=r"^[a-f0-9\-]{36}$")
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout_seconds: int = Field(default=3600, ge=60, le=86400)
    tags: list[str] | None = None

    model_config = {"frozen": True}
```

## 3. Walidacja Komend — Application Layer

Komenda może mieć własną walidację — cross-field, zależności między polami.

```python
# shell/application/execution/commands/create_execution_command.py
@dataclass(frozen=True)
class CreateExecutionCommand:
    graph_id: str
    max_retries: int = 3
    timeout_seconds: int = 3600
    schedule_type: str = "immediate"
    cron_expression: str | None = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.graph_id and len(self.graph_id) != 36:
            errors.append("graph_id must be a valid UUID")
        if self.max_retries < 0 or self.max_retries > 10:
            errors.append("max_retries must be between 0 and 10")
        if self.schedule_type == "cron" and not self.cron_expression:
            errors.append("cron_expression required when schedule_type=cron")
        if self.schedule_type == "cron" and self.cron_expression:
            # Podstawowa walidacja CRON
            parts = self.cron_expression.split()
            if len(parts) != 5:
                errors.append("cron_expression must have 5 fields")
        return errors
```

## 4. Walidacja w Handlerze

Handler wywołuje walidację komendy przed przekazaniem do domeny.

```python
class CreateExecutionHandler:
    async def handle(self, command: CreateExecutionCommand) -> None:
        # 1. Walidacja komendy
        errors = command.validate()
        if errors:
            raise CommandValidationError(errors)

        # 2. Autoryzacja
        self._auth.assert_can_create(command.user_id)

        # 3. Delegacja do domeny
        async with self._unit_of_work:
            graph = await self.graph_repository.get(GraphId(command.graph_id))
            execution = self.factory.create_from_graph(graph)
            await self.repository.add(execution)
            self._unit_of_work.stage_events(execution.pull_events())
```

## 5. Walidacja Biznesowa — Domain (VO/Agregat)

Walidacja biznesowa w VO (`__post_init__`) i agregacie (guard clauses).

```python
# VO — walidacja w __post_init__
@dataclass(frozen=True, slots=True)
class TaskExecutionName(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("TaskExecutionName cannot be empty")
        if len(self.value) > 255:
            raise ValueError("TaskExecutionName cannot exceed 255 characters")

# Agregat — guard clauses
class Execution(AggregateRoot):
    def start(self) -> None:
        if self._status != ExecutionStatus.PENDING:
            raise InvalidStateError(f"Cannot start in state {self._status}")
        if not self._tasks:
            raise NoTasksError("Cannot start execution without tasks")
        self._status = ExecutionStatus.RUNNING
        ...
```

## 6. Specyfikacja jako Narzędzie Walidacji

Dla złożonych reguł biznesowych — Specification Pattern.

```python
class CanStartExecutionSpecification(Specification[Execution]):
    def is_satisfied_by(self, execution: Execution) -> bool:
        return (
            execution.status == ExecutionStatus.PENDING
            and len(execution.tasks) > 0
            and execution.graph_id is not None
        )

# Użycie w agregacie
class Execution(AggregateRoot):
    def start(self) -> None:
        if not CanStartExecutionSpecification().is_satisfied_by(self):
            raise InvalidStateError("Execution cannot be started")
        ...
```

## 7. Walidacja w Factory

Factory waliduje dane wejściowe przed utworzeniem agregatu.

```python
class ExecutionFactory:
    def create_from_graph(self, graph: Graph, config: ExecutionConfig | None = None) -> Execution:
        cfg = config or ExecutionConfig.default()
        
        # Walidacja biznesowa
        if not graph.tasks:
            raise CannotCreateExecutionError("Graph has no tasks")
        if graph.status != GraphStatus.ACTIVE:
            raise CannotCreateExecutionError("Graph is not active")
        if cfg.max_retries > len(graph.tasks) * 2:
            raise InvalidConfigError("max_retries too high for task count")

        return Execution(
            id=ExecutionId.generate(),
            graph_id=graph.id,
            tasks=self._schedule_tasks(graph.tasks, cfg),
            status=ExecutionStatus.PENDING,
            created_at=Timestamp.now(),
        )
```

## 8. Lokalizacja

```
# Walidacja strukturalna (API)
shell/framework/api/requests/<nazwa>_request.py

# Walidacja komend (aplikacja)
shell/application/<bc>/commands/<command>.py  # validate() method

# Walidacja biznesowa (domena)
shell/domain/<bc>/value_objects/<nazwa>.py     # __post_init__
shell/domain/<bc>/aggregates/<agregat>.py       # guard clauses
shell/domain/<bc>/rules/<nazwa>_rule.py         # Rule Objects
shell/domain/platform/base/specification.py     # Specification base
```

## 9. Podsumowanie — Checklista

Projektując walidację:
- [ ] API (Pydantic) — typy, formaty, zakresy
- [ ] Komenda — cross-field validation
- [ ] Handler — wywołuje walidację + autoryzację
- [ ] VO — `__post_init__` z ValueError
- [ ] Agregat — guard clauses z wyjątkami domenowymi
- [ ] Factory — walidacja przed utworzeniem
- [ ] Rule/Specification — złożone reguły wielokrotnego użytku
- [ ] Każdy poziom ma własne błędy (API → HTTP 422, handler → domenowe)
- [ ] Testy dla każdego poziomu walidacji
