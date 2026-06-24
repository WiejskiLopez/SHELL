# Domain Event Structure

> Reguły struktury klasy Domain Event we wszystkich bounded contextach.

## Definicja

- Domain Event to niemutowalny fakt biznesowy, który wydarzył się w przeszłości.
- Emitowany przez Aggregate Root i konsumowany wewnątrz tego samego Bounded Context.

## Klasa

- `@dataclass(frozen=True)` — niemutowalny.
- Rozszerza `DomainEvent` (klasa bazowa z metadanymi).

```python
@dataclass(frozen=True)
class WorkflowStartedEvent(DomainEvent):
    workflow_id: WorkflowId
    started_by: UserId
    started_at: datetime
```

## Metadane

- Klasa bazowa dostarcza: `event_id`, `aggregate_id`, `aggregate_type`, `occurred_at`, `correlation_id`, `causation_id`, `schema_version`.

## Payload

- Zawiera tylko fakty (co się stało), nigdy instrukcje (co ma się stać).
- Typy: VO domenowe, typy proste. Nigdy referencje do agregatów.

```python
# Dobrze (fakt)
WorkflowStartedEvent(workflow_id=..., started_by=..., started_at=...)

# Źle (instrukcja)
WorkflowStartedEvent(send_email_to=..., notify_admin=...)
```

## Emisja

- Jeśli metoda domenowa realizuje przejście stanu agregatu, emituj event przejścia bezwarunkowo.
- Nie uzależniaj emisji od obecności optionala w parametrach.

```python
# Dobrze — bezwarunkowo
def start(self) -> None:
    self._status = WorkflowStatus.RUNNING
    self.append_event(WorkflowStartedEvent(...))

# Źle — warunkowo
def start(self, emit_event: bool = True) -> None:
    self._status = WorkflowStatus.RUNNING
    if emit_event:
        self.append_event(WorkflowStartedEvent(...))
```

## Backward compatibility

- `from_payload()` obsługuje brakujące pola przez `.get()` z domyślną wartością.
- Nigdy `payload['field']` — zawsze `payload.get('field', default)`.
- Każda zmiana schematu = inkrementacja `schema_version` + obsługa starego formatu.

```python
@classmethod
def from_payload(cls, payload: dict[str, Any]) -> WorkflowStartedEvent:
    return cls(
        workflow_id=WorkflowId.from_string(payload.get('workflow_id', '')),
        started_by=UserId.from_string(payload.get('started_by', '')),
        started_at=parse_datetime(payload.get('started_at', '1970-01-01')),
    )
```

## Lokalizacja

- Przy agregacie w podfolderze `events/`.

```
shell/domain/<bc>/aggregates/<nazwa>/events/
```

## Pliki

- Jeden event = jeden plik.
