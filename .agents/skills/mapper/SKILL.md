---
name: mapper
description: Zasady projektowania mapperów w architekturze hexagonalnej — konwersja między warstwami (domain ↔ model ORM, domain ↔ DTO), symetryczność mapowania, round-trip testing. Używaj gdy implementujesz nowy mapper dla agregatu, refaktoryzujesz istniejący, albo potrzebujesz mapowania między warstwami.
---

# Mapper Pattern w Enterprise DDD

## 1. Odpowiedzialność Mappera

Mapper odpowiada za **konwersję między warstwami architektury**:

- **Domain → ORM Model** (zapis do bazy)
- **ORM Model → Domain** (odczyt z bazy)
- **Domain → DTO** (output dla klienta)
- **Command/DTO → Domain** (input od klienta)

Mapper nie zawiera logiki biznesowej — tylko mapowanie pól.

```python
# shell/infrastructure/execution/mappers/execution_mapper.py
class ExecutionMapper:
    """Mapuje Execution (domain) ↔ ExecutionModel (ORM)."""

    def to_model(self, domain: Execution) -> ExecutionModel:
        return ExecutionModel(
            id=str(domain.id),
            graph_id=str(domain.graph_id),
            status=domain.status.value,
            version=domain.version.value,
            created_at=domain.created_at.value,
            updated_at=domain.updated_at.value if domain.updated_at else None,
        )

    def to_domain(self, model: ExecutionModel) -> Execution:
        return Execution.restore(
            id=ExecutionId(model.id),
            graph_id=GraphId(model.graph_id),
            status=ExecutionStatus(model.status),
            version=Version(model.version),
            created_at=Timestamp.from_datetime(model.created_at),
            updated_at=Timestamp.from_datetime(model.updated_at) if model.updated_at else None,
        )
```

## 2. Symetryczność Mapowania (Round-trip)

Mapper musi być **symetryczny**: `to_domain(to_model(domain)) == domain` dla wszystkich pól.

```python
# Test round-trip — obowiązkowy dla każdego mappera
class TestExecutionMapper:
    def test_round_trip(self, execution_factory: ExecutionFactory) -> None:
        # Given
        original = execution_factory.create(...)

        # When
        model = self.mapper.to_model(original)
        result = self.mapper.to_domain(model)

        # Then
        assert result.id == original.id
        assert result.status == original.status
        assert result.version == original.version
        assert result.graph_id == original.graph_id
        # Uwaga: events nie są mapowane — należą do warstwy aplikacyjnej
```

## 3. Mapper dla Agregatów z Encjami Dziecięcymi

Gdy agregat zawiera encje dziecięce, mapper mapuje cały graf obiektów.

```python
class ExecutionMapper:
    def to_model(self, domain: Execution) -> ExecutionModel:
        return ExecutionModel(
            id=str(domain.id),
            graph_id=str(domain.graph_id),
            status=domain.status.value,
            tasks=[self._task_to_model(t) for t in domain.tasks],
        )

    def to_domain(self, model: ExecutionModel) -> Execution:
        return Execution.restore(
            id=ExecutionId(model.id),
            graph_id=GraphId(model.graph_id),
            status=ExecutionStatus(model.status),
            tasks=[self._task_to_domain(t) for t in model.tasks],
        )

    def _task_to_model(self, task: ScheduledTask) -> TaskExecutionModel:
        return TaskExecutionModel(
            id=str(task.id),
            execution_id=str(task.execution_id),
            name=task.name.value,
        )

    def _task_to_domain(self, model: TaskExecutionModel) -> ScheduledTask:
        return ScheduledTask.restore(
            id=TaskExecutionId(model.id),
            execution_id=ExecutionId(model.execution_id),
            name=TaskExecutionName(model.name),
        )
```

## 4. Mapper a Factory — Różnice

| Aspekt | Mapper | Factory |
|--------|--------|---------|
| Cel | Konwersja między warstwami | Tworzenie nowych obiektów |
| Walidacja | Nie (zakłada poprawne dane) | Tak (biznesowa) |
| Używa `restore()` | Tak (do odczytu) | Tak (do rekonstrukcji) |
| Zależności | Tylko typy proste + VO | Domain Services, inne fabryki |
| Lokalizacja | Infrastruktura | Domeny |

## 5. Mapper dla DTO — Domain → DTO

Mapowanie z domeny na DTO dla warstwy prezentacji/API.

```python
# shell/application/execution/mappers/execution_dto_mapper.py
class ExecutionDTOMapper:
    def to_dto(self, domain: Execution) -> ExecutionDTO:
        return ExecutionDTO(
            id=str(domain.id),
            graph_id=str(domain.graph_id),
            status=domain.status.value,
            tasks=[self._task_to_dto(t) for t in domain.tasks],
            created_at=domain.created_at.value.isoformat(),
        )

    def _task_to_dto(self, task: ScheduledTask) -> TaskExecutionDTO:
        return TaskExecutionDTO(
            id=str(task.id),
            name=task.name.value,
        )
```

## 6. Command → Domain Mapper

Mapowanie z komendy (aplikacja) na agregat lub parametry do factory.

```python
class CreateExecutionMapper:
    def to_domain_params(self, cmd: CreateExecutionCommand) -> dict:
        return {
            "graph_id": GraphId(cmd.graph_id),
            "config": ExecutionConfig(
                max_retries=cmd.max_retries,
                timeout_seconds=cmd.timeout_seconds,
            ),
        }
```

## 7. Lokalizacja

```
# Mapper ORM (infrastructure)
shell/infrastructure/<bc>/mappers/<aggregate>_mapper.py

# Mapper DTO (application)
shell/application/<bc>/mappers/<aggregate>_dto_mapper.py

# Mapper Command (application)
shell/application/<bc>/mappers/<command>_mapper.py
```

## 8. Mapper a Typy Generyczne

Dla prostych mapowań można użyć generycznego interfejsu.

```python
from typing import Generic, TypeVar

TDomain = TypeVar("TDomain")
TModel = TypeVar("TModel")

class Mapper(ABC, Generic[TDomain, TModel]):
    @abstractmethod
    def to_model(self, domain: TDomain) -> TModel: ...
    @abstractmethod
    def to_domain(self, model: TModel) -> TDomain: ...

class ExecutionMapper(Mapper[Execution, ExecutionModel]):
    ...
```

## 9. Podsumowanie — Checklista

Tworząc mapper:
- [ ] Odwzorowuje wszystkie pola (domain ↔ model / DTO)
- [ ] Symetryczny — round-trip test przechodzi
- [ ] Nie zawiera logiki biznesowej
- [ ] Używa `restore()` na agregacie do odczytu
- [ ] Mapuje cały graf obiektów (agregat + encje dziecięce)
- [ ] Lokalizacja: infrastruktura (ORM) lub aplikacja (DTO)
- [ ] Round-trip test w testach jednostkowych
- [ ] Osobny mapper dla ORM i DTO
- [ ] Brak zależności między mapperami różnych warstw
