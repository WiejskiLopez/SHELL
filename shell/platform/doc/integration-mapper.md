# Integration Mapper

## Cel / Co realizuje

`ReflectiveIntegrationMapper` w `shell/platform/infrastructure/mapping/reflective_integration_mapper.py` konwertuje **dowolny** DomainEvent na odpowiadający mu IntegrationEvent bez per-aggregatowych mapperów. Używa konwencji nazw (klasa, moduł) i refleksji nad polami dataclass; błędy zgłasza jako `IntegrationMappingError`.

## Problem

Eventy domenowe emitowane przez agregaty (np. `UserCreatedEvent`) muszą być publikowane między bounded contextami jako IntegrationEventy (`UserCreatedIntegrationEvent`) z kompletem pól koperty (event_id, correlation_id, causation_id, occurred_at, aggregate_id, schema_version). Ręczne mapowanie każdej pary klas w każdym BC prowadzi do powielania kodu i rozjazdu kontraktów. Rozwiązanie: jeden refleksyjny mapper oparty na twardych konwencjach nazewniczych — jeśli IntegrationEvent nie istnieje, to jest to błąd konfiguracji/programowania, a nie błąd runtime'owy.

## Realizacja techniczna

### Konwencje adresowania

`_resolve_int_class(domain_event)` wyznacza klasę IntegrationEvent w dwóch krokach:

1. **Nazwa klasy**: `event_cls.__name__.replace("Event", "IntegrationEvent")` — `UserCreatedEvent` → `UserCreatedIntegrationEvent`.
2. **Moduł**: na podstawie `event_cls.__module__` wyznaczana jest **jedna** obsługiwana topologia — per-BC w ekstrakcji `_service`:

- `parts = module.split(".")`; wymagane `len(parts) > 5`, `parts[0] == "shell"`, `parts[1].endswith("_service")`, `parts[2] == "domain"`;
- `shell.<bc>_service.domain.<bc>.aggregates.<agg>.events.<file>` → `shell.<bc>_service.application.<bc>.<agg>.integration_events.<file>`;
- inna topologia → `IntegrationMappingError("Unsupported domain event module topology: ...")`.

Nazwa pliku powstaje z nazwy klasy przez `re.sub(r"(?<!^)(?=[A-Z])", "_", int_name).lower()` (PascalCase → snake_case). Moduł jest importowany przez `importlib.import_module`, a klasa pobierana przez `getattr(mod, int_name)`. Brak modułu (`ModuleNotFoundError`) lub brak klasy w module → `IntegrationMappingError` z komunikatem naprawy.

### Budowa kwargs i mapowanie pól

`map(domain_event)`:

1. Uzupełnia pola koperty: `event_id=str(domain_event.event_id.value)`, `correlation_id=get_or_create_correlation_id()`, `causation_id=get_causation_id()` (z kontekstu — patrz [tracing-context](tracing-context.md)), `occurred_at`, `aggregate_id=str(...)`, `schema_version=1` (stała — wersja jest nadawana na granicy kontraktu).
2. `ENVELOPE_FIELDS` — frozenset nazw pól `IntegrationEvent` (`dataclasses.fields(IntegrationEvent)`) — służy do pominięcia pól koperty przy mapowaniu pól biznesowych.
3. Dla każdego pozostałego pola klasy IntegrationEvent pobiera atrybut o tej samej nazwie z eventu domenowego i konwertuje przez `_to_str(raw)` (`str(raw.value)` albo `None`).
4. Zwraca `int_cls(**kwargs)`.

Dzięki temu **nazwy pól biznesowych** muszą się zgadzać między DomainEvent a IntegrationEvent, a wartości są łańcuchowane (`str`), z zachowaniem `None`.

### `IntegrationMappingError`

`shell/platform/infrastructure/mapping/integration_mapping_error.py` definiuje `IntegrationMappingError(ValueError)` — zgłaszany przy nieobsługiwanej topologii modułu, braku modułu lub braku klasy w module. Komunikat wskazuje naprawę: zadeklarować IntegrationEvent albo oznaczyć event jako internal-only. Dziedziczenie po `ValueError` utrzymuje kompatybilność z istniejącymi `except ValueError`.

## Kluczowe pliki

- `shell/platform/infrastructure/mapping/reflective_integration_mapper.py`
- `shell/platform/infrastructure/mapping/integration_mapping_error.py`

## Powiązane koncepcje

- [integration-contracts](integration-contracts.md)
- [domain-event](domain-event.md)
- [tracing-context](tracing-context.md)
- [transactional-outbox](transactional-outbox.md)
- [relay](relay.md)