# Wiki architektury platformy SHELL

Ten katalog (`shell/platform/doc/`) jest wiki platformy SHELL — wspólnej warstwy
technicznej, z której korzystają wszystkie bounded contexts. Każda koncepcja
architektoniczna ma **osobny plik**, który opisuje:

- **Cel** — co dana konstrukcja realizuje;
- **Problem** — jaki problem architektoniczny lub operacyjny rozwiązuje;
- **Realizacja techniczna** — jak jest zaimplementowana (klasy, przepływy,
  umiejscowienie w kodzie);
- **Kluczowe pliki** — ścieżki źródłowe;
- **Powiązane koncepcje** — linki do powiązanych stron wiki.

Dokumentacja jest **techniczna** i punktowa — opisuje faktyczny stan kodu, a nie
postulaty. Piszemy ją zgodnie z zasadami projektu (architektura hexagonalna,
DDD, CQRS, transactional outbox, inbox z lease, at-least-once).

---

## Indeks

### Przegląd

- [architecture-overview](architecture-overview.md) — warstwy, topologia modułów, reguły zależności

### Warstwa domeny (DDD building blocks)

- [aggregate-root](aggregate-root.md) — AggregateRoot i agregaty
- [entity](entity.md) — Encje i tożsamość
- [entity-id](entity-id.md) — Typowane identyfikatory (EntityId)
- [value-object](value-object.md) — Value Object
- [domain-event](domain-event.md) — Domain Events
- [domain-message](domain-message.md) — Domain Messages
- [domain-errors](domain-errors.md) — Wyjątki domenowe
- [domain-ports](domain-ports.md) — Porty domenowe (repozytoria, czas, identyfikatory, log)

### Warstwa aplikacji

- [cqrs-buses](cqrs-buses.md) — CommandBus / QueryBus / EventBus / MessageBus
- [unit-of-work](unit-of-work.md) — Unit of Work i transactional outbox
- [ports-and-adapters](ports-and-adapters.md) — Porty aplikacji i adaptery
- [tracing-context](tracing-context.md) — correlation_id / causation_id
- [session-scope](session-scope.md) — Ambientowy scope transakcji delivery
- [contract-catalog](contract-catalog.md) — Jawny katalog kontraktów

### Kontrakty integracyjne

- [integration-contracts](integration-contracts.md) — IntegrationEvent / IntegrationMessage i mapowanie

### Delivery (Inbox/Outbox)

- [delivery-overview](delivery-overview.md) — Przepływ end-to-end delivery
- [transactional-outbox](transactional-outbox.md) — Outbox transakcyjny
- [inbox-lifecycle](inbox-lifecycle.md) — Cykl życia rekordu inbox (maszyna stanów)
- [claim-lease](claim-lease.md) — Claim z lease (krótka transakcja)
- [inbox-processor](inbox-processor.md) — Wspólny cykl claim→process→ack
- [processed-delivery-dedup](processed-delivery-dedup.md) — Deduplikacja `processed_delivery`
- [heartbeat-lease](heartbeat-lease.md) — Odnawianie lease i limit czasu batcha
- [replay](replay.md) — Bezpieczny replay administracyjny
- [retention](retention.md) — Retencja DLQ i `processed_delivery`
- [delivery-transport](delivery-transport.md) — Port i adaptery transportu (RabbitMQ)
- [relay](relay.md) — Relay outbox→transport oraz outbox→inbox
- [envelope-versioning](envelope-versioning.md) — Wersjonowanie schematu, walidacja, upcaster
- [delivery-models](delivery-models.md) — Modele persistence delivery (bundle per BC)
- [polling-worker](polling-worker.md) — Worker cykliczny z backoff i heartbeat
- [metrics](metrics.md) — Metryki backlogu przez port MetricsBackend
- [readiness](readiness.md) — Readiness (DB, migracje, worker, backlog)

### Framework i API

- [http-api](http-api.md) — Aplikacja FastAPI (setup, wersjonowanie, OpenAPI)
- [api-middleware](api-middleware.md) — Middleware (correlation_id, api_key, api_version, audit)
- [error-handling](error-handling.md) — Obsługa błędów i Problem Details
- [pagination](pagination.md) — Paginacja odpowiedzi
- [authentication-principal](authentication-principal.md) — Uwierzytelnienie i principal

### Infrastruktura

- [sqlalchemy-persistence](sqlalchemy-persistence.md) — Sesje, modele SQL, mapowanie typów
- [integration-mapper](integration-mapper.md) — ReflectiveIntegrationMapper
- [logging](logging.md) — Logowanie, JSON formatter, audyt
- [configuration](configuration.md) — Konfiguracja (YAML + env)
- [cli-tools](cli-tools.md) — Narzędzia CLI (`shell-retention`)

---

## Reguły redagowania

- Linki między stronami używają względnych ścieżek: `[claim-lease](claim-lease.md)`.
- Ścieżki plików w kodzie są względne do katalogu `shell/`.
- Opisujemy stan faktyczny kodu; zmiana kodu powinna wymagać aktualizacji wiki.
