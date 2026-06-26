---
name: domain-event
description: Zasady projektowania zdarzeń domenowych (Domain Events) — struktura, emisja, wersjonowanie, backward compatibility.
Używaj gdy dodajesz nowy event, poprawiasz istniejący, zmieniasz schemat eventu, albo review'ujesz poprawność emisji w agregacie.
---

# Domain Event — zdarzenia domenowe

## Definicja

Domain Event to niemutowalny fakt biznesowy, który wydarzył się w przeszłości. Jest emitowany przez Aggregate Root i konsumowany wewnątrz tego samego Bounded Context.

- Event rozszerza `DomainEvent` (base class z metadanymi: `event_id`, `aggregate_id`, `aggregate_type`, `occurred_at`, `correlation_id`, `causation_id`, `schema_version`)
- Payload zawiera tylko fakty (co się stało), nigdy instrukcje (co ma się stać)

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

**Wyjątek**: pola metadane z base `DomainEvent` (`event_id: str`, `occurred_at: datetime`, `correlation_id: str`, `causation_id: str`, `schema_version: int`) są dozwolone — to infrastruktura event systemu.

Test weryfikujący: `test_domain_event_fields_have_domain_types`.

## Event schema — backward compatibility

`from_payload()` obsługuje brakujące pola przez `.get()` z domyślną wartością. Nigdy `payload["field"]` — zawsze `payload.get("field", default)`. Każda zmiana schematu = inkrementacja `schema_version` + obsługa starego formatu.

## Powiązane skille

- `platform/application-layer/domain-event-handler/SKILL.md` — obsługa eventów przez handlery aplikacyjne
- `platform/domain-layer/aggregate-design/SKILL.md` — emisja eventów z agregatu przez `append_event()`
