---
name: domain-event-structure
description: Reguły struktury Domain Event — frozen dataclass, rozszerza DomainEvent, nazwa w czasie przeszłym, backward compatibility.
---

# Domain Event Structure

> Reguły struktury klasy Domain Event we wszystkich bounded contextach.

## Definicja

- Domain Event to niemutowalny fakt biznesowy, który wydarzył się w przeszłości.
- Emitowany przez Aggregate Root i konsumowany wewnątrz tego samego Bounded Context.

## Klasa

- `@dataclass(frozen=True, slots=True, kw_only=True)` — niemutowalny, oszczędny, wymagane nazwane parametry.
- Rozszerza `DomainEvent` (klasa bazowa z metadanymi).

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowStartedEvent(DomainEvent):
    workflow_id: WorkflowId
    started_by: UserId
    started_at: Timestamp
```

## Metadane

- Klasa bazowa dostarcza: `event_id`, `aggregate_id`, `aggregate_name`, `occurred_at`, `schema_version`.
- Metadane envelope (transport, tracing) opisuje `integration-patterns/integration-event` i `shell-specific/tracing-context`.

## ⚠️ Primitive Obsession

Wszystkie pola eventu (poza metadanymi z bazy) muszą być ValueObjectami.

Przyklad pol prymitywnych:
```python
@dataclass
class TaskCreatedEvent(DomainEvent):
    reason: str           # ZŁO: str zamiast Reason
    details: dict         # ZŁO: dict zamiast StateData
    goal: str             # ZŁO: str zamiast Goal
    config: dict[str, object]  # ZŁO: dict zamiast StateData
```

Przyklad pol Value Object:
```python
@dataclass
class TaskCreatedEvent(DomainEvent):
    reason: Reason              # VO
    details: StateData          # VO
    goal: Goal                  # VO
```

## Payload

- Zawiera fakty opisujace zaszle zdarzenie.
- Typy payloadu sa domenowymi Value Objectami i identyfikatorami kontraktu.

```python
# Dobrze (fakt)
WorkflowStartedEvent(workflow_id=..., started_by=..., started_at=...)

# Źle (instrukcja)
WorkflowStartedEvent(send_email_to=..., notify_admin=...)
```

## ⚠️ Antypattern: Nadmiarowe dane w evencie (Event Data Bloat)

Event domenowy ma identyfikować **co się stało i którego agregatu dotyczy** — nie transportować danych, które można dociągnąć serwisem/repozytorium po identyfikatorze agregatu.

### Zasada

- Event niesie TYLKO: `aggregate_id` (identyfikator agregatu którego zmiana dotyczy, odziedziczony z `DomainEvent` lub jawny) + identyfikatory powiązanych agregatów (referencje).
- Wszystkie **pozostałe dane** (property, atrybuty, stany, listy, obiekty wartościowe które nie są identyfikatorem) są **nadmiarowe** — odbiorca eventu może dociągnąć je przez port/repozytorium używając ID agregatu.
- Wyjątek: ID powiązanych agregatów (referencje) — np. `task_execution_id` w `WorkflowStartedEvent`, `user_id` w `SessionOpenedEvent`.

### Przykład (ZŁO — nadmiarowe dane)

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class TaskExecutionCreatedEvent(DomainEvent):
    task_execution_id: TaskExecutionId
    task_execution_name: TaskExecutionName   # NADMIAR — property agregatu
    description: TaskDescription              # NADMIAR — property agregatu
    skills: list[SkillData] | None = None     # NADMIAR — lista do dociągnięcia po ID
```

### Przykład (DOBRZE — tylko identyfikatory)

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class TaskExecutionCreatedEvent(DomainEvent):
    task_execution_id: TaskExecutionId        # ID agregatu — wystarczy
```

### Dlaczego?

1. **Event to fakt, nie DTO** — im lżejszy, tym łatwiej go przechowywać, replikować, walidować.
2. **Unikasz rozjechania się danych** — jeśli event niesie kopię stanu, a stan agregatu się zmieni, kopie w eventach są nieaktualne.
3. **Mniejszy rozmiar w outboxie/kolejce** — embeddingi, plany, listy skilli to zbędny balast.
4. **Czysta semantyka** — `TaskExecutionCreatedEvent(task_execution_id=...)` mówi wszystko: zadanie o tym ID zostało utworzone. Resztę dociągnie ten, kto potrzebuje.

### Kwalifikator

Jeśli pole eventu to ID **innego agregatu** (referencja): **ZOSTAW**.
Jeśli pole eventu to property / atrybut / lista / obiekt wartościowy danego agregatu: **USUŃ** — odbiorca dociągnie przez port.

```python
# DOBRZE — ID powiązanego agregatu
@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowStartedEvent(DomainEvent):
    workflow_id: WorkflowId               # ID własnego agregatu
    task_execution_id: TaskExecutionId    # ID powiązanego agregatu (OK — referencja)

# ŹLE — property własnego agregatu
@dataclass(frozen=True, slots=True, kw_only=True)
class GraphExecutionCreatedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId  # ID własnego agregatu
    goal: Goal                            # NADMIAR — property
    depth: GraphDepth                     # NADMIAR — property
```

## Emisja

- Jeśli metoda domenowa realizuje przejście stanu agregatu, emituj event przejścia bezwarunkowo.
- Nie uzależniaj emisji od obecności optionala w parametrach.

```python
# Dobrze — bezwarunkowo
def start(self, now: OccurredAt) -> None:
    self._status = WorkflowStatus.RUNNING
    self.append_event(WorkflowStartedEvent(workflow_id=self._id, occurred_at=now))

# Źle — warunkowo
def start(self, now: OccurredAt, emit_event: bool = True) -> None:
    self._status = WorkflowStatus.RUNNING
    if emit_event:
        self.append_event(WorkflowStartedEvent(workflow_id=self._id, occurred_at=now))
```

## Serializacja

- Serializacja/deserializacja eventów NIE jest robiona przez `from_payload()` na klasie eventu.
- Obsługuje ją `DomainEventSerializer` → `EventDeserializer` w `shell/platform/infrastructure/serialization/`.
- `to_payload(event)` — serializuje pola dataclass (pomija metadane envelope; szczegoly w `integration-patterns/integration-event`).
- `from_payload(event_cls, occurred_at, payload, schema_version)` — rekonstruuje event z serializowanych części.
- Obsługuje zagnieżdżone dataclass, value objects (przez `.value`), listy, dict, daty.

## Lokalizacja

- Przy agregacie w podfolderze `events/`.

```
shell/domain/<bc>/aggregates/<nazwa>/events/
```

## Pliki

- Jeden event = jeden plik.
