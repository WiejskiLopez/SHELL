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

- Agregat bazuje na tożsamości ID; `@dataclass` (równość strukturalna) pozostaje poza agregatem.
- Obowiązkowo `__slots__` ze wszystkimi polami; `_id` pozostaje dziedziczony z `AggregateRoot`.
- `__eq__` i `__hash__` bazują wyłącznie na ID; stan pozostaje poza porównaniem.
- **Primitive Obsession**: wszystkie pola agregatu są ValueObject, Entity lub ID; typy `str`, `int`, `bool`, `dict`, `list` pozostają poza agregate.

```python
class Workflow(AggregateRoot[WorkflowId]):
    __slots__ = ('_name', '_status', '_nodes')

    def __init__(self, workflow_id: WorkflowId, name: WorkflowName, ...) -> None:
        super().__init__(workflow_id)
        self._name = name
        self._status = WorkflowStatus.IDLE
        self._nodes: list[Node] = []
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

- Każda metoda domenowa na agregacie, która modyfikuje stan, przestrzega sekwencji:
  1. **Guard clause** — sprawdzenie warunku wejściowego (invariant), fail-fast.
  2. **Mutacja stanu** — zmiana pól agregatu.
  3. **`append_event()`** — rejestracja faktu biznesowego dla przejść stanu.

Metody reprezentujące przejście stanu emitują event bezwarunkowo. Istnieją też
metody guard + mutacja bez emisji eventu (np. `User.enable()`/`disable()`,
maszyna stanów `NodeExecution`) — komplet takich metod jest jawnie katalogowany
w testach architektury (`_KNOWN_NO_EVENT_EMIT` w
`test_domain_structure__test_mutating_methods_emit_events.py`).

```python
def start(self) -> None:
    # 1. Guard clause — zawsze pierwszy, fail-fast
    if self._status is not WorkflowStatus.IDLE:
        raise WorkflowAlreadyStarted(self._id)

    # 2. Mutacja stanu
    self._status = WorkflowStatus.RUNNING

    # 3. Event bezwarunkowo
    self.append_event(WorkflowStartedEvent(
        workflow_id=self._id,
        started_by=self._owner_id,
        started_at=Clock.now(),
    ))
```

### Zasady sekwencji

- **Guard clause zawsze pierwszy** — mutacja stanu zachodzi po potwierdzeniu invariantu.
- **Mutacja przed eventem** — event rejestruje fakt po zmianie stanu.
- **Event bezwarunkowo dla przejść stanu** — metoda reprezentująca przejście stanu emituje event zawsze; emisja niezależna od parametrów.

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

- Guard clauses i eventy dotyczą metod modyfikujących stan; metody odczytowe wykonują wyłącznie odczyt.
- Metody odczytowe po prostu zwracają wartość.

```python
def can_start(self) -> bool:
    return self._status is WorkflowStatus.IDLE and bool(self._nodes)
```

### Eventy

- `append_event()` dodaje event do wewnętrznej listy; handler wyciąga przez `pull_events()`.

## Wersjonowanie

- Agregat domenowy nie trzyma pola `_version` — optymistyczne blokowanie jest
  realizowane na poziomie ORM przez `VersionedMixin` (kolumna `version` +
  `__mapper_args__["version_id_col"]` w modelu SQL, patrz
  `sqlalchemy-persistence.md`).

## Encje dziecięce

- Modyfikowane wyłącznie przez metody agregatu.
- Zapis i odczyt encji prowadzi repozytorium agregatu root (bez własnego repozytorium).
- Mają lokalną tożsamość tylko w kontekście agregatu.

## Lokalizacja

- `shell/<service>/domain/<bc>/aggregates/<nazwa>/<nazwa>.py`
- Folder agregatu zawiera plik agregatu oraz podfoldery per rodzaj artefaktu
  (`entities/`, `events/`, `exceptions/`, `repositories/`, a tam, gdzie są VO —
  `value_objects/`).
- Współdzielone VO (np. `UserId`, `UserEmail`, `UserStatus`) żyją na poziomie BC
  w `shell/<service>/domain/<bc>/value_objects/`; VO typowe dla jednego agregatu
  mogą żyć w jego podfolderze `value_objects/`.

## Bezpieczeństwo

- Importy tylko z `shell.<service>.domain.*` i biblioteka standardowa.
- Brak importów ORM, frameworków, `shell.*.infrastructure.*`, `shell.*.application.*`.
