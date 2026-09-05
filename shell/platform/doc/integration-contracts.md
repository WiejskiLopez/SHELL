# Kontrakty integracyjne (IntegrationEvent)

## Cel / Co realizuje

Definiuje jawny, wersjonowany kontrakt wymiany danych między bounded contextami:
bazowa klasa `IntegrationEvent` oraz mapowanie zdarzeń domenowych na zdarzenia
integracyjne (`ReflectiveIntegrationMapper`). Każdy event wychodzący poza BC
jest instancją tej klasy i niesie kompletny envelope tracingowy.

## Problem

Domenowe agregaty emitują zdarzenia w języku domeny (np. `SessionOpenedEvent`),
które nie powinny być bezpośrednio wystawiane jako publiczne API. Granica między
BC wymaga jawnego, stabilnego kontraktu (envelope z `correlation_id`,
`causation_id`, `occurred_at`, `aggregate_id`, `schema_version`), a jego
tworzenie nie może wymagać ręcznych mapperów per agregat.

## Realizacja techniczna

### Bazowa klasa kontraktu

- `IntegrationEvent` (`application/events/integration_event.py`): frozen dataclass
  z polami `event_id`, `correlation_id`, `causation_id`, `occurred_at`,
  `aggregate_id`, `schema_version`.

### ReflectiveIntegrationMapper

`infrastructure/mapping/reflective_integration_mapper.py` mapuje **dowolny**
domain event na integration event na podstawie konwencji nazw:

1. `UserCreatedEvent` → `UserCreatedIntegrationEvent`;
2. rozpoznaje moduł docelowy na podstawie struktury ścieżki modułu zdarzenia —
   jedyna obsługiwana topologia to `shell.<bc>_service.domain.<bc>.aggregates.<agg>.events.<file>`
   (inna → `IntegrationMappingError`; szczegóły w [integration-mapper](integration-mapper.md));
3. wypełnia pola envelope z `correlation_id` (przez `get_or_create_correlation_id()`)
   i `causation_id` (z kontekstu [tracing-context](tracing-context.md)) oraz
   `event_id`/`occurred_at`/`aggregate_id`/`schema_version` ze zdarzenia domenowego
   (`schema_version` = stała `1`);
4. pozostałe pola integracyjnego eventu uzupełnia z pól zdarzenia domenowego
   (`_to_str`, wartość VO przez `.value`).

Brak klasy integracyjnej rzuca `IntegrationMappingError` z komunikatem
wskazującym oczekiwany moduł — wymusza deklarację kontraktu albo oznaczenie
zdarzenia jako wewnętrznego.

### Serializacja kontraktu

`IntegrationEventSerializer` (`infrastructure/serialization/integration_event/integration_event_serializer.py`):
- `to_payload` — serializuje pola dataclass, pomijając pola koperty
  (`event_id`, `correlation_id`, `causation_id`, `occurred_at`, `aggregate_id`,
  `schema_version`); wartości VO przez `.value`, `datetime` przez `isoformat`;
- `to_envelope(...)` — buduje envelope wire: `event_id`, `source_service`,
  `contract_type`, `occurred_at`, `schema_version`, `correlation_id`,
  `causation_id`, `aggregate_id`, `payload`.

Deserializacja odbywa się przez `IntegrationEventDeserializer`
(`infrastructure/serialization/integration_event/integration_event_deserializer.py`),
z opcjonalnym upcastem `schema_version` (patrz [envelope-versioning](envelope-versioning.md)).

## Kluczowe pliki

- `shell/platform/application/events/integration_event.py`
- `shell/platform/infrastructure/mapping/reflective_integration_mapper.py`
- `shell/platform/infrastructure/mapping/integration_mapping_error.py`
- `shell/platform/infrastructure/serialization/integration_event/integration_event_serializer.py`
- `shell/platform/infrastructure/serialization/integration_event/integration_event_deserializer.py`

## Powiązane koncepcje

- [integration-mapper](integration-mapper.md)
- [contract-catalog](contract-catalog.md)
- [tracing-context](tracing-context.md)
- [envelope-versioning](envelope-versioning.md)
- [transactional-outbox](transactional-outbox.md)
