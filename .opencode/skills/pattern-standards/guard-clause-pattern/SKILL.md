---
name: guard-clause-pattern
description: Reguły wzorca Guard Clause — fail-fast, warunki wstępne w metodach domenowych, dedykowane wyjątki, Rule Objects.
---

# Guard Clause Pattern

> Reguły wzorca Guard Clause we wszystkich warstwach domenowych.

## Definicja

- Guard clause to warunek wstępny na początku metody, który sprawdza invariant i przerywa wykonanie jeśli nie jest spełniony.
- Fail-fast — im szybciej błąd zostanie wykryty, tym łatwiej go zdiagnozować.

## Zasada

- Każda metoda modyfikująca stan zaczyna się od guard clauses.
- Warunki sprawdzane od najbardziej szczegółowego do ogólnego.
- Każdy warunek rzuca dedykowany wyjątek domenowy.

```python
def assign_user(self, user_id: UserId) -> None:
    if self._status is not WorkflowStatus.IDLE:
        raise WorkflowAlreadyStarted(self._id)
    if len(self._assigned_users) >= self._max_users:
        raise MaxUsersExceeded(self._id, self._max_users)
    if self._assigned_users.contains(user_id):
        raise UserAlreadyAssigned(self._id, user_id)
    self._assigned_users.add(user_id)
```

## Rule Object

- Gdy warunek jest złożony lub używany w wielu miejscach — wyodrębnij do Rule Object.

```python
class WorkflowCanAssignUserRule:
    def __init__(self, workflow: Workflow, user_id: UserId) -> None:
        self._workflow = workflow
        self._user_id = user_id

    def check(self) -> None:
        if self._workflow.status is not WorkflowStatus.IDLE:
            raise WorkflowAlreadyStarted(self._workflow.id)
        if len(self._workflow.assigned_users) >= self._workflow.max_users:
            raise MaxUsersExceeded(self._workflow.id, self._workflow.max_users)
        if self._user_id in self._workflow.assigned_users:
            raise UserAlreadyAssigned(self._workflow.id, self._user_id)
```

## Miejsca stosowania

| Miejsce | Przykład |
|---------|----------|
| `VO.__post_init__()` | `if not self.value: raise EmailEmptyError()` |
| `Entity` metoda | `if self._status is not WorkflowStatus.ACTIVE: raise ...` |
| `Aggregate` metoda | `if not self._nodes: raise WorkflowHasNoNodes(...)` |
| `Factory` metoda | `if template.is_empty(): raise InvalidTemplate(...)` |
| `Domain Service` | `if not pricing.is_valid(): raise InvalidPricing(...)` |

## Dedykowane wyjątki

- Infantry biznesowe podnoszą dedykowane wyjątki domenowe (`...Error` po `DomainError`).
- Każdy invariant ma swoją klasę wyjątku.

```python
class WorkflowAlreadyStarted(DomainError): ...
class MaxUsersExceeded(DomainError): ...
class UserAlreadyAssigned(DomainError): ...
```
