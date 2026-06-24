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
        self._version = 0
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

- Każda metoda modyfikująca stan przestrzega sekwencji:
  1. Guard clause — sprawdzenie warunku wejściowego
  2. Modyfikacja stanu
  3. Bezwarunkowe `append_event()` z odpowiednim `DomainEvent`

```python
def start(self) -> None:
    if self._status is not WorkflowStatus.IDLE:
        raise WorkflowAlreadyStarted(self._id)
    self._status = WorkflowStatus.RUNNING
    self._version += 1
    self.append_event(WorkflowStartedEvent(...))
```

- Event przejścia stanu emitowany bezwarunkowo — nie zależy od opcjonalnych parametrów metody.
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
