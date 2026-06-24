# Aggregate Domain Method Pattern

> Reguły sekwencji metody domenowej na Aggregate Root.

## Definicja

- Każda metoda domenowa na agregacie, która modyfikuje stan, przestrzega niezmiennej sekwencji trzech kroków.

## Sekwencja

1. **Guard clause** — sprawdzenie warunku wejściowego (invariant).
2. **Mutacja stanu** — zmiana pól agregatu.
3. **Bezwarunkowe `append_event()`** — rejestracja faktu biznesowego.

```python
def start(self) -> None:
    # 1. Guard clause
    if self._status is not WorkflowStatus.IDLE:
        raise WorkflowAlreadyStarted(self._id)

    # 2. Mutacja stanu
    self._status = WorkflowStatus.RUNNING
    self._version += 1

    # 3. Event (bezwarunkowo)
    self.append_event(WorkflowStartedEvent(
        workflow_id=self._id,
        started_by=self._owner_id,
        started_at=Clock.now(),
    ))
```

## Zasady

- **Guard clause zawsze pierwszy** — nie ma sensu mutować stanu jeśli invariant jest naruszony.
- **Mutacja przed eventem** — event rejestruje fakt po zmianie stanu.
- **Event bezwarunkowo** — jeśli metoda reprezentuje przejście stanu, event musi być zawsze emitowany. Nie uzależniaj emisji od parametrów.

```python
# Dobrze
def complete(self, result: Result) -> None:
    if self._status is not WorkflowStatus.RUNNING:
        raise WorkflowNotRunning(self._id)
    self._status = WorkflowStatus.COMPLETED
    self._result = result
    self.append_event(WorkflowCompletedEvent(self._id, result))

# Źle — warunkowa emisja eventu
def complete(self, result: Result, emit_event: bool = True) -> None:
    ...
    if emit_event:
        self.append_event(...)
```

## Proste gettery

- Metody które nie modyfikują stanu nie wymagają guard clauses ani eventów.
- Po prostu zwracają wartość.

```python
def can_start(self) -> bool:
    return self._status is WorkflowStatus.IDLE and bool(self._nodes)
```
