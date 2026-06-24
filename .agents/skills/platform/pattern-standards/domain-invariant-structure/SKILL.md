# Domain Invariant / Rule Object Structure

> Reguły struktury dla invariantów domenowych i Rule Object we wszystkich bounded contextach.

## Definicja

- Invariant to reguła biznesowa, która zawsze musi być spełniona — bez żadnego okna czasowego.
- Guard clauses na początku każdej metody modyfikującej agregat.

## Guard clauses

- Każda metoda modyfikująca stan agregatu zaczyna się od guard clauses — sprawdzenia invariantów przed zmianą.
- Fail-fast — nie ma sensu kontynuować jeśli invariant jest naruszony.

```python
def start(self) -> None:
    if self._status is not WorkflowStatus.IDLE:
        raise WorkflowAlreadyStarted(self._id)
    if not self._nodes:
        raise WorkflowHasNoNodes(self._id)
    self._status = WorkflowStatus.RUNNING
    self._version += 1
    self.append_event(WorkflowStartedEvent(...))
```

## Dedykowane wyjątki

- Każdy naruszony invariant rzuca dedykowany wyjątek domenowy — nie ogólny `ValueError` czy `RuntimeError`.

```python
class WorkflowAlreadyStarted(DomainError):
    def __init__(self, workflow_id: WorkflowId) -> None:
        self.workflow_id = workflow_id
        super().__init__(f'Workflow {workflow_id} already started')

class WorkflowHasNoNodes(DomainError):
    def __init__(self, workflow_id: WorkflowId) -> None:
        self.workflow_id = workflow_id
        super().__init__(f'Workflow {workflow_id} has no nodes')
```

## Rule Object

- Gdy reguła jest złożona lub używana w wielu miejscach — wyodrębniaj ją do osobnej klasy (Rule Object).
- Rule Object implementuje `is_satisfied()` i `check()`.

```python
class WorkflowCanStartRule:
    def __init__(self, workflow: Workflow) -> None:
        self._workflow = workflow

    def is_satisfied(self) -> bool:
        return self._workflow.status is WorkflowStatus.IDLE and bool(self._workflow.nodes)

    def check(self) -> None:
        if not self.is_satisfied():
            if self._workflow.status is not WorkflowStatus.IDLE:
                raise WorkflowAlreadyStarted(self._workflow.id)
            if not self._workflow.nodes:
                raise WorkflowHasNoNodes(self._workflow.id)
```

## Miejsca walidacji

| Miejsce | Co waliduje |
|---------|-------------|
| `VO.__post_init__()` | Wewnętrzna spójność VO |
| `Entity/Aggregate` metoda | Reguła stanu (guard clause) |
| `Aggregate` factory method | Reguła tworzenia |
| `Domain Service` | Reguła międzyagregatowa |

## _assert_invariants()

- Agregat może mieć metodę `_assert_invariants()` wołaną przed każdą modyfikacją.

```python
def _assert_invariants(self) -> None:
    WorkflowCanStartRule(self._workflow).check()
```

## Lokalizacja

- Guard clauses: w agregacie (`_assert_*` metody)
- Rule Objects: `shell/domain/<bc>/rules/<nazwa_reguly>_rule.py`
- Wyjątki: `shell/domain/<bc>/exceptions.py`
