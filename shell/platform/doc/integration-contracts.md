# Kontrakty integracyjne (IntegrationEvent)

## Cel / Co realizuje

Definiuje jawny, wersjonowany kontrakt wymiany danych między bounded contextami:
bazowa klasa `IntegrationEvent` oraz mapowanie zdarzeń domenowych na zdarzenia
integracyjne (`ReflectiveIntegrationMapper`). Każdy event wychodzący poza BC
jest instancją tej klasy i niesie kompletny envelope tracingowy.

> Kanał `IntegrationMessage` został usunięty — patrz `docs/messages-removed.md`.

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
  `aggregate_id`, `aggregate_name`, `schema_version`.

### ReflectiveIntegrationMapper

`infrastructure/mapping/reflective_integration_mapper.py` mapuje **dowolny**
domain event na integration event na podstawie konwencji nazw:

1. `SessionOpenedEvent` → `SessionOpenedIntegrationEvent`;
2. rozpoznaje moduł docelowy na podstawie struktury ścieżki modułu zdarzenia
   (legacy `shell.domain.<bc>.aggregates.<agg>.events`, nowe
   `shell.<bc>.domain.<bc>.aggregates.<agg>.events`, platformowe
   `shell.platform.domain.events`);
3. wypełnia pola envelope z `correlation_id`/`causation_id` (z kontekstu
   [tracing-context](tracing-context.md)) oraz `event_id`/`occurred_at`/
   `aggregate_id`/`aggregate_name`/`schema_version` ze zdarzenia domenowego;
4. pozostałe pola integracyjnego eventu uzupełnia z pól zdarzenia domenowego
   (`_to_str`, wartość VO przez `.value`).

Brak klasy integracyjnej rzuca `IntegrationMappingError` z komunikatem
wskazującym oczekiwany moduł — wymusza deklarację kontraktu albo oznaczenie
zdarzenia jako wewnętrznego.

### Serializacja kontraktu

`DomainEventSerializer` (`infrastructure/serialization/event/domain_event_serializer.py`):
- `to_payload` — serializuje pola dataclass (pomija `occurred_at`,
  `schema_version`); wartości VO przez `.value`, `datetime` przez `isoformat`;
- `from_payload` — odtwarza obiekt z payloadu z obsługą `list`/`dict`,
  prymitywów, `CreatedAt`, jedno-polowych VO i zagnieżdżonych dataclass.

## Kluczowe pliki

- `shell/platform/application/events/integration_event.py`
- `shell/platform/infrastructure/mapping/reflective_integration_mapper.py`
- `shell/platform/infrastructure/mapping/integration_mapping_error.py`
- `shell/platform/infrastructure/serialization/event/domain_event_serializer.py`

## Powiązane koncepcje

- [integration-mapper](integration-mapper.md)
- [contract-catalog](contract-catalog.md)
- [tracing-context](tracing-context.md)
- [envelope-versioning](envelope-versioning.md)
- [transactional-outbox](transactional-outbox.md)
