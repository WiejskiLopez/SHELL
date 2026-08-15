# Integration Mapper

## Cel / Co realizuje

`ReflectiveIntegrationMapper` w `shell/platform/infrastructure/mapping/reflective_integration_mapper.py` konwertuje **dowolny** DomainEvent na odpowiadający mu IntegrationEvent bez per-aggregatowych mapperów. Używa wyłącznie konwencji nazw (klasa, moduł) i refleksji nad polami dataclass — brak `isinstance`, `try/except`, fallbacków czy rejestrów. Błędy zgłasza jako `IntegrationMappingError`.

## Problem

Eventy domenowe emitowane przez agregaty (np. `SessionOpenedEvent`) muszą być publikowane między bounded contextami jako IntegrationEventy (`SessionOpenedIntegrationEvent`) z kompletem pól koperty (event_id, correlation_id, causation_id, occurred_at, aggregate_id, aggregate_name, schema_version). Ręczne mapowanie każdej pary klas w każdym BC prowadzi do powielania kodu i rozjazdu kontraktów. Rozwiązanie: jeden refleksyjny mapper oparty na twardych konwencjach nazewniczych — jeśli IntegrationEvent nie istnieje, to jest to błąd konfiguracji/programowania, a nie błąd runtime'owy.

## Realizacja techniczna

### Konwencje adresowania

`_resolve_int_class(domain_event)` wyznacza klasę IntegrationEvent w dwóch krokach:

1. **Nazwa klasy**: `event_cls.__name__.replace("Event", "IntegrationEvent")` — `SessionOpenedEvent` → `SessionOpenedIntegrationEvent`.
2. **Moduł**: na podstawie `event_cls.__module__` wybierana jest jedna z trzech ścieżek:

- `parts[1] == "platform"`: `shell.platform.domain.events.aggregate_deleted_event` → `shell.application.domain.integration_events.aggregate_deleted_integration_event`;
- `len(parts) > 5 and parts[2] == "domain"` (wyekstrahowany BC `shell.user_service`): `shell.<bc>.domain.<bc>.aggregates.<agg>.events.<file>` → `shell.<bc>.application.<bc>.<agg>.integration_events.<file>`;
- ścieżka legacy: `shell.domain.<bc>.aggregates.<agg>.events.<file>` → `shell.application.<bc>.<agg>.integration_events.<file>`.

Nazwa pliku powstaje z nazwy klasy przez `re.sub(r"(?<!^)(?=[A-Z])", "_", int_name).lower()` (PascalCase → snake_case). Moduł jest importowany przez `importlib.import_module`, a klasa pobierana przez `getattr(mod, int_name)`.

### Budowa kwargs i mapowanie pól

`map(domain_event)`:

1. Uzupełnia pola koperty z domenowego eventu: `event_id=str(domain_event.event_id.value)`, `correlation_id=get_correlation_id()`, `causation_id=get_causation_id()` (z kontekstu — patrz [tracing-context](tracing-context.md)), `occurred_at`, `aggregate_id`, `aggregate_name`, `schema_version`.
2. `ENVELOPE_FIELDS` — frozenset nazw pól `IntegrationEvent` (`dataclasses.fields(IntegrationEvent)`) — służy do pominięcia pól koperty przy mapowaniu pól biznesowych.
3. Dla każdego pozostałego pola klasy IntegrationEvent pobiera atrybut o tej samej nazwie z eventu domenowego i konwertuje przez `_to_str(raw)` (wartość `raw.value` albo `None`).
4. Zwraca `int_cls(**kwargs)`.

Dzięki temu **nazwy pól biznesowych** muszą się zgadzać między DomainEvent a IntegrationEvent, a wartości są łańcuchowane (`str`), z zachowaniem `None`.

### `IntegrationMappingError`

`shell/platform/infrastructure/mapping/integration_mapping_error.py` definiuje `IntegrationMappingError(ValueError)` — zgłaszany, gdy moduł nie istnieje (`ModuleNotFoundError` przechwytywany i przepakowany) lub gdy klasy nie ma w module. Komunikat wskazuje naprawę: zadeklarować IntegrationEvent albo oznaczyć event jako internal-only. Dziedziczenie po `ValueError` utrzymuje kompatybilność z istniejącymi `except ValueError`.

## Kluczowe pliki

- `shell/platform/infrastructure/mapping/reflective_integration_mapper.py`
- `shell/platform/infrastructure/mapping/integration_mapping_error.py`

## Powiązane koncepcje

- [integration-contracts](integration-contracts.md)
- [domain-event](domain-event.md)
- [tracing-context](tracing-context.md)
- [transactional-outbox](transactional-outbox.md)
- [relay](relay.md)
