# Validation Layers Pattern

> Reguły trójwarstwowej walidacji we wszystkich bounded contextach.

## Definicja

- Walidacja odbywa się na trzech niezależnych poziomach, każdy z własną odpowiedzialnością.
- Każdy poziom ma własne błędy i własny moment wykonania.

## Warstwa 1: API (strukturalna)

- Framework: Pydantic (lub inny walidator wejścia).
- Sprawdza: typy, formaty, zakresy, wymagane pola.
- Błąd: HTTP 422 (Unprocessable Entity).

```python
class StartWorkflowRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    owner_id: uuid.UUID
    nodes: list[NodeConfig] = Field(..., min_length=1)
```

## Warstwa 2: Application (koordynacyjna)

- Handler / walidator aplikacyjny.
- Sprawdza: autoryzację, stan systemu, dostęp do zasobów, poprawność跨-polową komendy.
- Błąd: dedykowany wyjątek aplikacyjny.

```python
class StartWorkflowValidator:
    async def validate(self, command: StartWorkflowCommand) -> None:
        if not await self._auth_service.has_permission(command.owner_id, 'workflow:create'):
            raise UnauthorizedWorkflowCreate(command.owner_id)
        if await self._quota_service.is_over_limit(command.owner_id):
            raise WorkflowQuotaExceeded(command.owner_id)
```

## Warstwa 3: Domain (biznesowa)

- VO (`__post_init__`) i Aggregate (guard clauses).
- Sprawdza: invariants biznesowe, reguły procesu, konsystencję stanu.
- Błąd: dedykowany wyjątek domenowy (`DomainError`).

```python
@dataclass(frozen=True, slots=True)
class WorkflowName(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError('Workflow name cannot be empty')
        if len(self.value) > 100:
            raise ValueError('Workflow name too long')
```

```python
def start(self) -> None:
    if self._status is not WorkflowStatus.IDLE:
        raise WorkflowAlreadyStarted(self._id)
    ...
```

## Komenda z walidacją

- Command może mieć metodę `validate()` wołaną przez handler przed delegacją do domeny.

```python
@dataclass(frozen=True)
class StartWorkflowCommand:
    name: str
    owner_id: str
    nodes: list[NodeConfigDto]

    def validate(self) -> None:
        if not self.name.strip():
            raise InvalidCommand('name', 'Workflow name cannot be empty')
        if not self.nodes:
            raise InvalidCommand('nodes', 'At least one node required')
```

## Podsumowanie

| Warstwa | Co waliduje | Narzędzie | Błąd |
|---------|-------------|-----------|------|
| API | Typy, formaty, zakresy | Pydantic | HTTP 422 |
| Application | Autoryzacja, quota,跨-polowa | Validator | Wyjątek aplikacyjny |
| Domain | Invarianty biznesowe | VO / Aggregate | DomainError |
