---
name: domain-event
description: Zasady projektowania zdarzeń domenowych (Domain Events) — struktura, nazewnictwo, emisja, wersjonowanie, backward compatibility.
Używaj gdy dodajesz nowy event, poprawiasz istniejący, zmieniasz schemat eventu, albo review'ujesz poprawność emisji w agregacie.
---

# Domain Event — zdarzenia domenowe

## Definicja

Domain Event to niemutowalny fakt biznesowy, który wydarzył się w przeszłości. Jest emitowany przez Aggregate Root i konsumowany wewnątrz tego samego Bounded Context.

- Event rozszerza `DomainEvent` (base class z metadanymi: `event_id`, `aggregate_id`, `aggregate_type`, `occurred_at`, `correlation_id`, `causation_id`, `schema_version`)
- `@dataclass(frozen=True)` — niemutowalny
- Jeden event = jeden plik
- Payload zawiera tylko fakty (co się stało), nigdy instrukcje (co ma się stać)

```python
@dataclass(frozen=True, slots=True)
class WorkflowCompletedEvent(DomainEvent):
    workflow_id: WorkflowId

    @classmethod
    def now(cls, workflow_id: WorkflowId, now: datetime) -> WorkflowCompletedEvent:
        return cls(occurred_at=now, workflow_id=workflow_id)

    @classmethod
    def from_payload(cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1) -> Self:
        return cls(occurred_at=occurred_at, schema_version=schema_version, workflow_id=WorkflowId(payload["workflow_id"]))
```

## Obowiązkowe metadane (z base class `DomainEvent`)

| Pole | Typ | Opis |
|------|-----|------|
| `event_id` | UUID / str | Unikalny identyfikator tego wystąpienia eventu |
| `aggregate_id` | str | ID agregatu który wyemitował event |
| `aggregate_type` | str | Typ agregatu (np. `"Workflow"`) |
| `occurred_at` | datetime | Kiedy zdarzenie zaszło (czas domenowy) |
| `correlation_id` | str \| None | ID procesu biznesowego (łączy eventy w jeden łańcuch) |
| `causation_id` | str \| None | ID eventu który bezpośrednio to spowodował |
| `schema_version` | int | Wersja schematu eventu (dla ewolucji) |

## Nazewnictwo

### Klasa eventu

```
<AggregateName><PastVerb>Event
```

- `AggregateName` — pełna, biznesowa nazwa agregatu (np. `Workflow`, `GraphExecution`, `TaskExecution`, `GraphNodeExecution`, `Session`, `SchedulerExecution`)
- `PastVerb` — czas przeszły dokonany, opisujący co się stało (`Created`, `Started`, `Completed`, `Failed`, `Aborted`, `Exhausted`, `Opened`, `Closed`, `Taken`, `Looped`)
- Sufiks `Event` — obowiązkowy

Przykłady:
- `WorkflowStartedEvent`
- `GraphExecutionCompletedEvent`
- `TaskExecutionCreatedEvent`
- `SessionOpenedEvent`
- `GraphNodeTransitionExecutionConditionEvaluatedEvent`

### Plik eventu

```
<aggregate_name>_<past_verb>_event.py
```

- `snake_case` z sufiksem `_event`
- Nazwa pliku odpowiada nazwie klasy

Przykłady:
- `workflow_started_event.py`
- `graph_execution_completed_event.py`
- `task_execution_created_event.py`
- `session_opened_event.py`
- `graph_node_transition_execution_condition_evaluated_event.py`

### Lokalizacja

Event leży w podfolderze `events/` wewnątrz swojego agregatu:

```
aggregates/my_aggregate/
    events/
        __init__.py
        my_aggregate_<verb>_event.py
```

## Emisja zdarzeń — bezwarunkowa dla przejść stanu

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

## Event schema — backward compatibility

`from_payload()` obsługuje brakujące pola przez `.get()` z domyślną wartością. Nigdy `payload["field"]` — zawsze `payload.get("field", default)`. Każda zmiana schematu = inkrementacja `schema_version` + obsługa starego formatu.

### Zasady ewolucji

| Zmiana | Czy bezpieczna | Uwagi |
|--------|---------------|-------|
| Dodanie opcjonalnego pola | Tak | Stary konsument ignoruje |
| Dodanie wymaganego pola | Nie | Złamie starych konsumentów — nowa wersja eventu |
| Usunięcie pola | Nie | Nigdy nie usuwaj; deprecated + ignore |
| Zmiana typu pola | Nie | Nowa wersja eventu |
| Zmiana nazwy pola | Nie dodawaj nowego, deprecated stare | Nowa wersja |
| Zmiana znaczenia pola | Nie | Nowy event (inna nazwa) |

```python
@classmethod
def from_payload(cls, payload: dict) -> "OrderConfirmedEvent":
    version = payload.get("schema_version", 1)
    if version == 1:
        return cls(
            ...,
            confirmed_by=payload.get("confirmed_by"),  # brak w V1 → None
        )
    if version == 2:
        return cls(...)
    raise UnknownSchemaVersion(version)
```

## Konwencje

- Event rozszerza `DomainEvent` z `domain/platform/events/domain_event.py`
- `@dataclass(frozen=True, slots=True)` — absolutnie niemutowalny
- Nazwa w czasie przeszłym dokonanym — opisuje co SIĘ STAŁO, nie co MA SIĘ STAĆ
- Nazwa zawiera nazwę agregatu który emituje event
- Jeden event = jeden plik
- `from_payload()` obsługuje stare wersje schematu
- Payload zawiera tylko fakty, nigdy instrukcje
- `schema_version` inkrementowane przy każdej zmianie struktury
- Metoda `now()` jako factory classmethod przyjmująca `now: datetime`

## Powiązane skille

- `.agents/skills/domain-event-handler/SKILL.md` — obsługa eventów przez handlery aplikacyjne
- `.agents/skills/aggregate-design/SKILL.md` — emisja eventów z agregatu przez `append_event()`
