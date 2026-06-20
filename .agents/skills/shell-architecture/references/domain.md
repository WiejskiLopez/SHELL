# Warstwa domenowa

Reguły budowy klocków domenowych. Warstwa `domain/` jest sercem systemu — czysty Python, bez zależności zewnętrznych.

## Entity

- Dziedziczy po `Entity[TId]` z `domain/entities/base/entity.py`
- Tożsamość oparta na `id` — `__eq__` i `__hash__` tylko po identyfikatorze
- Stan mutowalny, ale identyfikator (`_id`) niemutowalny po konstrukcji — prywatny atrybut, publiczny property `id`
- Każdy Entity ma dedykowany Value Object jako ID (np. `TaskExecutionId`)
- Nigdy nie używaj `@dataclass` dla Entity — stracisz identity-based equality

```python
class TaskExecution(AggregateRoot[TaskExecutionId]):
    __slots__ = ("_name", "_version", "_body", ...)   # bez _id — dziedziczony

    @property
    def name(self) -> TaskExecutionName:
        return self._name

    def rename(self, new_name: TaskExecutionName) -> None:
        self._name = new_name
```

### Child Entity (wewnątrz agregatu, bez własnej tożsamości globalnej)
- Nie dziedziczy po `Entity[TId]`
- Może być `@dataclass(slots=True)` jeśli nie potrzebuje identity-based equality
- Istnieje tylko w kontekście swojego Aggregate Root
- Tworzona wyłącznie przez metody Aggregate Root (lub w mapperze przy deserializacji z persystencji)

## Aggregate Root

- Dziedziczy po `AggregateRoot[TId]` z `domain/entities/base/aggregate_root.py`
- Prywatny bufor zdarzeń: `append_event()` i `pull_events()`
- Granica transakcji — cały zapis jednego AR to jedna transakcja
- Tylko Aggregate Root emituje zdarzenia domenowe
- Każda metoda modyfikująca stan woła `append_event()` z odpowiednim DomainEvent

### Enkapsulacja stanu (KRYTYCZNE)

Aggregate Root i Entity **nigdy** nie udostępniają:
- publicznych setterów dla stanu domenowego (`@status.setter`, `@version.setter`)
- mutowalnych referencji do kolekcji wewnętrznych

```python
# POPRAWNIE — zwróć kopię
@property
def parallel_groups(self) -> dict[str, ParallelGroup]:
    return dict(self._parallel_groups)

# POPRAWNIE — zwróć niemutowalną kolekcję
@property
def graph_node_executions(self) -> tuple[GraphNodeExecution, ...]:
    return tuple(self._graph_node_executions)

# ŹLE — zwraca oryginalny obiekt; caller mutuje stan agregatu
# @property
# def state_output(self) -> dict[str, Any]:
#     return self._state_output
```

Pamiętaj o kopii płytkiej wartości: jeśli property zwraca `dict[str, list[str]]`, `dict(...)` kopiuje tylko klucze — listy pozostają współdzielone. Wtedy:

```python
return {k: list(v) for k, v in self._waiting_nodes.items()}
```

Mutacja stanu odbywa się wyłącznie przez metody domenowe (`start_at()`, `advance_to()`, `archive()`). Repozytorium używa metody domenowej do inkrementacji wersji, nigdy bezpośredniego przypisania.

## Value Object

- `@dataclass(frozen=True, slots=True)`
- Walidacja w `__post_init__`
- Obowiązkowa metoda `__str__`
- Brak tożsamości — dwa VO z tymi samymi wartościami są wymienne
- Typy ID: każda klasa z kompletem `@dataclass(frozen=True, slots=True)`, `__post_init__` (walidacja non-empty), `__str__`, `@classmethod generate()`

## Domain Event

- Niezmienne dataclasses w `domain/events/events/`
- Każdy event w osobnym pliku
- Nazwa pliku: snake_case z sufiksem `_event` (`task_execution_created_event.py`)
- Klasa: PascalCase z sufiksem `Event` (`TaskExecutionCreatedEvent`)
- Część opisowa: przeszłość dokonana (`Created`, `Completed`, `Failed`)
- Eventy są faktami — zawierają tylko dane które się wydarzyły, nie instrukcje

### Emisja zdarzeń — bezwarunkowa dla przejść stanu

Jeśli metoda domenowa realizuje przejście stanu agregatu (np. `idle → running`, `running → done`), **emituj event przejścia bezwarunkowo**. Nie uzależniaj emisji od obecności optionala w parametrach:

```python
# POPRAWNIE — event przejścia stanu zawsze emitowany
def finish(self, *, now, task_execution_id=None) -> None:
    self._status = Status.done()
    self.append_event(WorkflowCompletedEvent.now(self.id, task_execution_id, now=now))

# ŹLE — warunkowa emisja; konsument eventów nie dostanie powiadomienia
# def finish(self, *, now, task_execution_id=None) -> None:
#     self._status = Status.done()
#     if task_execution_id is not None:
#         self.append_event(WorkflowCompletedEvent.now(...))
```

Warunkowanie emisji eventu stanu od parametru powoduje, że sagi/event-handlery subskrybujące ten event nigdy nie zostaną obudzone — obserwowany deadlock całego potoku.

### Event schema — backward compatibility

`from_payload()` obsługuje brakujące pola przez `.get()` z domyślną wartością. Nigdy `payload["field"]` — zawsze `payload.get("field", default)`. Każda zmiana schematu = inkrementacja `schema_version` + obsługa starego formatu.

## Domain Service

- W `domain/services/` — operacje które nie pasują do żadnej encji lub VO
- Stateless
- Pracują wyłącznie na obiektach domenowych
- Przykłady: `EnvelopeLifecycleService`, `GraphNodeExecutionNavigator`, `GraphGraphNodeExecutionPolicy`

## Domain Exception

- W `domain/exceptions/` — osobna klasa dla każdego przypadku
- Dziedziczą po bazowej `DomainError` z `_base.py`
- Niosą kontekst domenowy (ID encji, nieprawidłowa wartość)

## Repository Port (Domain)

- Interface (Protocol) w `domain/repositories/`
- Operacje nazywane językiem domeny: `save()`, `get_by_id()`, `next_version()`, `find_latest_by_*()`
- Nigdy nie ujawniają detali persystencji (SQL, ORM, kolekcje)
- Metody przyjmują/zwracają wyłącznie obiekty domenowe
- Metoda lookupowa zwracająca kolekcję powinna mieć deterministyczną kolejność (determinizm zapewnia warstwa infra; port może to tylko założyć)
