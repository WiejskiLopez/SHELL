---
name: domain-event
description: "Zasady projektowania zdarzeń domenowych (Domain Events) — struktura, emisja, wersjonowanie, backward compatibility. Używaj gdy dodajesz nowy event, poprawiasz istniejący, zmieniasz schemat eventu, albo review'ujesz poprawność emisji w agregacie."
---

# Domain Event — zdarzenia domenowe

## Definicja

Domain Event to niemutowalny fakt biznesowy, który wydarzył się w przeszłości. Jest emitowany przez Aggregate Root i konsumowany wewnątrz tego samego Bounded Context.

- Event rozszerza `DomainEvent` (base class z metadanymi: `event_id`, `aggregate_id`, `occurred_at`)
- Payload zawiera tylko fakty (co się stało), nigdy instrukcje (co ma się stać)

## Metadane (z base class `DomainEvent`)

| Pole | Typ | Opis |
|------|-----|------|
| `event_id` | `EventId` | Unikalny identyfikator tego wystąpienia eventu |
| `aggregate_id` | `AggregateId` | ID agregatu który wyemitował event |
| `occurred_at` | `OccurredAt` | Kiedy zdarzenie zaszło (czas domenowy) |

Wszystkie metadane bazy to ValueObjecty (`shell/platform/domain/value_objects/`). Pola pieczęci logowania (`correlation_id`, `causation_id`, `schema_version` oraz identyfikator dostarczenia) nie należą do klasy domenowej — są metadanymi envelope/integracji nadawanymi przez platformę po stronie serializerów i outbox/inbox.

## Emisja zdarzeń — bezwarunkowa dla przejść stanu

Jeśli metoda domenowa realizuje przejście stanu agregatu (np. `idle → running`, `running → done`), **emituj event przejścia bezwarunkowo**. Nie uzależniaj emisji od obecności optionala w parametrach. Warunkowanie emisji eventu stanu od parametru powoduje, że sagi/event-handlery subskrybujące ten event nigdy nie zostaną obudzone — obserwowany deadlock całego potoku.

## ⚠️ Primitive Obsession — w evencie tylko ValueObjecty

Wszystkie pola eventu domenowego (poza metadanymi z base class) muszą być ValueObjectami.

ZABRONIONE:
```python
@dataclass
class TaskExecutionCreatedEvent(DomainEvent):
    description: str                # ZŁO: str zamiast TaskDescription
    output: str                     # ZŁO: str zamiast EventOutput
    goal: str                       # ZŁO: str zamiast Goal
    verifier_result: dict           # ZŁO: dict zamiast StateData
    plan: dict[str, object]         # ZŁO: dict zamiast StateData
    skills: list[dict]              # ZŁO: list[dict] zamiast list[SkillPayload]
```

DOZWOLONE:
```python
@dataclass
class TaskExecutionCreatedEvent(DomainEvent):
    description: TaskDescription         # VO
    output: EventOutput                  # VO
    skills: list[SkillPayload] | None    # kolekcja VO
```

**Wyjątek**: pola metadane z base `DomainEvent` (`event_id: EventId`, `aggregate_id: AggregateId`, `occurred_at: OccurredAt`) są ValueObjectami platformy — dozwolone.

Test weryfikujący: `test_domain_event_fields_have_domain_types`.

## Struktura eventu

Event domenowy to subklasa `DomainEvent` w buildowane przez `@classmethod now(...)`:

```python
@dataclass(frozen=True, slots=True)
class TaskExecutionCreatedEvent(DomainEvent):
    task_execution_id: TaskExecutionId

    @classmethod
    def now(cls, task_execution_id: TaskExecutionId, now: OccurredAt) -> TaskExecutionCreatedEvent:
        return cls(occurred_at=now, task_execution_id=task_execution_id)
```

Agregat emituje event przez `append_event(...)`; metadane `event_id` i `aggregate_id` uzupełnia platforma.

## Event schema — backward compatibility

Kontrakt serializacji używanej w outbox/inbox zewnętrznych zależy od `schema_version` envelope, nie od klasy domenowej. Payload eventu musi być odporny na ewolucję: deserializacja integration eventów przez `payload.get("field", default)` zamiast `payload["field"]`. Zmiana schematu = nowa `schema_version` + obsługa starego formatu (patrz `integration-patterns/integration-event`).

## Powiązane skille

- `platform/application-layer/domain-event-handler/SKILL.md` — obsługa eventów przez handlery aplikacyjne
- `platform/domain-layer/aggregate-design/SKILL.md` — emisja eventów z agregatu przez `append_event()`
