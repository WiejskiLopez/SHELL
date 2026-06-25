---
name: aggregate-structure
description: Reguły struktury Aggregate Root — dziedziczenie po AggregateRoot[TId], __slots__, metody domenowe z sekwencją guard-mutacja-event, brak publicznych setterów.
---

# Aggregate Structure

> Reguły struktury klasy Aggregate Root we wszystkich bounded contextach.

## Dziedziczenie

- Każdy agregat dziedziczy po `AggregateRoot[TId]` z platformy.
- `TId` to konkretny Value Object identyfikatora agregatu.

```python
class Workflow(AggregateRoot[WorkflowId]):
    ...
```

## Klasa

- **Nie używać `@dataclass`** dla agregatu — tożsamość to nie równość strukturalna.
- Obowiązkowo `__slots__` ze wszystkimi polami. Nie powtarzać `_id` (dziedziczony z `AggregateRoot`).
- `__eq__` i `__hash__` bazują wyłącznie na ID — nigdy na stanie.

```python
class Workflow(AggregateRoot[WorkflowId]):
    __slots__ = ('_name', '_status', '_nodes', '_version')

    def __init__(self, workflow_id: WorkflowId, name: WorkflowName, ...) -> None:
        super().__init__(workflow_id)
        self._name = name
        self._status = WorkflowStatus.IDLE
        self._nodes: list[Node] = []
        self._version = Version.initial()
```

## Stan

- Stan agregatu jest modyfikowalny **wyłącznie przez metody domenowe**.
- Żadnych publicznych setterów. Żadnych mutowalnych referencji przez property.
- Property zwracające kolekcje zwracają kopie (płytkie lub głębokie).

```python
@property
def nodes(self) -> tuple[Node, ...]:
    return tuple(self._nodes)

@property
def status(self) -> WorkflowStatus:
    return self._status
```

## Metody domenowe

- Każda metoda domenowa na agregacie, która modyfikuje stan, przestrzega niezmiennej sekwencji trzech kroków:

  1. **Guard clause** — sprawdzenie warunku wejściowego (invariant).
  2. **Mutacja stanu** — zmiana pól agregatu.
  3. **Bezwarunkowe `append_event()`** — rejestracja faktu biznesowego.

```python
def start(self) -> None:
    # 1. Guard clause — zawsze pierwszy, fail-fast
    if self._status is not WorkflowStatus.IDLE:
        raise WorkflowAlreadyStarted(self._id)

    # 2. Mutacja stanu
    self._status = WorkflowStatus.RUNNING
    self._version = self._version.next()

    # 3. Event bezwarunkowo
    self.append_event(WorkflowStartedEvent(
        workflow_id=self._id,
        started_by=self._owner_id,
        started_at=Clock.now(),
    ))
```

### Zasady sekwencji

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

### Proste gettery

- Metody które nie modyfikują stanu nie wymagają guard clauses ani eventów.
- Po prostu zwracają wartość.

```python
def can_start(self) -> bool:
    return self._status is WorkflowStatus.IDLE and bool(self._nodes)
```

### Eventy

- `append_event()` dodaje event do wewnętrznej listy; handler wyciąga przez `pull_events()`.

## Wersjonowanie

- Każdy agregat trzyma `_version` inkrementowany przy każdym zapisie.
- Wykorzystywany do optymistycznego blokowania przy zapisie do bazy.

## Encje dziecięce

- Modyfikowane wyłącznie przez metody agregatu.
- Nie mają własnego repozytorium — zapisywane i odczytywane przez repozytorium agregatu.
- Mają lokalną tożsamość tylko w kontekście agregatu.

## Lokalizacja

- `shell/domain/<bc>/aggregates/<nazwa>/<nazwa>.py`
- W folderze agregatu znajduje się wyłącznie plik agregatu.
- Wszystkie VO (w tym ID) należą do podfolderu `value_objects/` w BC.

## Bezpieczeństwo

- Importy tylko z `shell.domain.*`, biblioteka standardowa, zewnętrzne biblioteki dozwolone w domenie.
- Brak importów ORM, frameworków, `shell.infrastructure.*`, `shell.application.*`.
