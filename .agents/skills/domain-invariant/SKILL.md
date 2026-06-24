---
name: domain-invariant
description: Wzorce implementacji invariantów biznesowych w DDD — reguły które muszą być zawsze spełnione, defensive checks, guard clauses, Rule Objects, walidacja między polami, invariants przy tworzeniu i modyfikacji. Używaj gdy projektujesz reguły biznesowe w agregatach/encjach/VO, albo refaktoryzujesz rozproszoną walidację.
---

# Domain Invariant / Business Rule w Enterprise DDD

## 1. Czym jest Invariant

**Invariant** to reguła biznesowa, która **zawsze musi być spełniona** — bez żadnego okna czasowego. Jeśli invariant jest naruszony, system jest w niepoprawnym stanie.

Przykłady:
- `Execution.status` nie może być `COMPLETED` i `FAILED` jednocześnie
- `OrderItem.quantity` musi być > 0
- `Payment.amount` nie może przekraczać `Order.total`
- `DateRange.end` musi być >= `DateRange.start`

## 2. Gdzie Umieszczać Invarianty

| Miejsce | Rodzaj invariantu | Przykład |
|---------|------------------|----------|
| `VO.__post_init__()` | Wewnętrzna spójność VO | `Version >= 1` |
| `Entity` / `Aggregate` metoda | Reguła stanu | `can't cancel completed execution` |
| `Aggregate` factory method | Reguła tworzenia | `graph must be active` |
| `Domain Service` | Reguła międzyagregatowa | `total items <= credit limit` |

## 3. Guard Clause — Fail-fast

Każda metoda modyfikująca stan agregatu zaczyna się od guard clauses — sprawdzenia invariantów przed zmianą.

```python
class Execution(AggregateRoot):
    def start(self) -> None:
        # Guard clauses — fail-fast
        if self._status != ExecutionStatus.PENDING:
            raise InvalidStateError(
                f"Cannot start execution in state {self._status}"
            )
        if not self._tasks:
            raise NoTasksError("Cannot start execution without tasks")

        # Business logic
        self._status = ExecutionStatus.RUNNING
        self._started_at = Timestamp.now()
        self._record_event(ExecutionStartedEvent(
            aggregate_id=self._id,
            task_count=len(self._tasks),
        ))

    def complete(self) -> None:
        if self._status != ExecutionStatus.RUNNING:
            raise InvalidStateError(
                f"Cannot complete execution in state {self._status}"
            )
        if any(t.is_pending for t in self._tasks):
            raise PendingTasksError("Cannot complete with pending tasks")

        self._status = ExecutionStatus.COMPLETED
        self._completed_at = Timestamp.now()
        self._record_event(ExecutionCompletedEvent(aggregate_id=self._id))
```

## 4. Rule Object — Osobna Klasa dla Złożonej Reguły

Gdy reguła jest złożona lub używana w wielu miejscach — wyodrębnij ją do osobnej klasy (Rule Object).

```python
# shell/domain/execution/rules/can_complete_execution_rule.py
class CanCompleteExecutionRule:
    """Rule Object — hermetyzuje złożoną regułę biznesową."""

    def is_satisfied(self, execution: Execution) -> bool:
        return (
            execution.status == ExecutionStatus.RUNNING
            and not any(t.is_pending for t in execution.tasks)
            and not any(t.is_failed for t in execution.tasks)
            and execution.started_at is not None
        )

    def check(self, execution: Execution) -> None:
        if not self.is_satisfied(execution):
            failures = []
            if execution.status != ExecutionStatus.RUNNING:
                failures.append(f"status is {execution.status}, expected RUNNING")
            if any(t.is_pending for t in execution.tasks):
                failures.append("has pending tasks")
            if any(t.is_failed for t in execution.tasks):
                failures.append("has failed tasks")
            raise RuleViolationError(f"Cannot complete execution: {'; '.join(failures)}")


# Użycie w agregacie
class Execution(AggregateRoot):
    def complete(self) -> None:
        CanCompleteExecutionRule().check(self)
        self._status = ExecutionStatus.COMPLETED
        ...
```

## 5. Invariant Method — Sprawdzenie Przed Modyfikacją

Agregat może mieć metodę `_assert_invariants()` wywoływaną przed każdą modyfikacją.

```python
class Order(AggregateRoot):
    def add_item(self, product: Product, quantity: int) -> None:
        self._assert_can_modify()
        self._assert_item_not_duplicate(product.id)
        self._items.append(OrderItem(product.id, quantity))
        self._assert_total_not_exceeded()

    def _assert_can_modify(self) -> None:
        if self._status != OrderStatus.DRAFT:
            raise FrozenOrderError("Cannot modify submitted order")

    def _assert_item_not_duplicate(self, product_id: ProductId) -> None:
        if any(item.product_id == product_id for item in self._items):
            raise DuplicateItemError(f"Product {product_id} already in order")

    def _assert_total_not_exceeded(self) -> None:
        if self.total > self._credit_limit:
            raise CreditLimitExceededError(
                f"Order total {self.total} exceeds limit {self._credit_limit}"
            )
```

## 6. Walidacja Przy Tworzeniu (Factory)

Invarianty przy tworzeniu agregatu — sprawdzane w factory method.

```python
class ExecutionFactory:
    def create_from_graph(self, graph: Graph, config: ExecutionConfig) -> Execution:
        # Invarianty tworzenia
        if not graph.tasks:
            raise CannotCreateExecutionError("Graph has no tasks")
        if graph.status != GraphStatus.ACTIVE:
            raise CannotCreateExecutionError("Graph is not active")
        if config.max_retries < 0:
            raise InvalidConfigError("max_retries cannot be negative")

        execution = Execution(
            id=ExecutionId.generate(),
            graph_id=graph.id,
            tasks=self._schedule_tasks(graph.tasks, config),
            status=ExecutionStatus.PENDING,
            created_at=Timestamp.now(),
            config=config,
        )
        execution._record_event(ExecutionCreatedEvent(
            aggregate_id=execution.id,
            graph_id=execution.graph_id,
            task_count=len(execution.tasks),
        ))
        return execution
```

## 7. Wyjątki Domenowe dla Invariantów

Każdy naruszony invariant rzuca **dedykowany wyjątek domenowy** — nie ogólny `ValueError` czy `RuntimeError`.

```python
# shell/domain/platform/exceptions.py
class DomainError(Exception):
    """Base dla wszystkich błędów domenowych."""

class InvalidStateError(DomainError):
    """Operacja niedozwolona w bieżącym stanie."""

class RuleViolationError(DomainError):
    """Naruszenie reguły biznesowej."""

class InvariantViolationError(DomainError):
    """Naruszenie invariantu agregatu."""

# shell/domain/execution/exceptions.py
class ExecutionNotFoundError(DomainError): ...
class CannotCreateExecutionError(DomainError): ...
class NoTasksError(DomainError): ...
class PendingTasksError(DomainError): ...
```

## 8. Lokalizacja

```
# Rule Objects
shell/domain/<bc>/rules/<nazwa_reguly>_rule.py

# Wyjątki domenowe
shell/domain/<bc>/exceptions.py
shell/domain/platform/exceptions.py

# Invarianty w agregatach
shell/domain/<bc>/aggregates/<agregat>.py  # _assert_* methods
```

## 9. Podsumowanie — Checklista

Implementując invarianty:
- [ ] Guard clauses na początku każdej metody modyfikującej
- [ ] Dedykowane wyjątki domenowe dla każdego naruszenia
- [ ] Rule Object dla złożonych reguł używanych w wielu miejscach
- [ ] `_assert_invariants()` dla spójności między polami
- [ ] Factory sprawdza invarianty przy tworzeniu
- [ ] VO waliduje w `__post_init__()`
- [ ] Brak ogólnych wyjątków (`ValueError`, `RuntimeError`) — tylko domenowe
- [ ] Testy dla każdego invariantu (pozytywne i negatywne)
