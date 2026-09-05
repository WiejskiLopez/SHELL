# Architektura platformy SHELL — przegląd

## Cel

Platforma SHELL jest wspólną warstwą techniczną, na której opierają się wszystkie
bounded contexts projektu. Implementuje raz mechanizmy przekrojowe: modelowanie
DDD, CQRS, transactional outbox/inbox z at-least-once, tracing, kontrakty,
readiness i metryki. Bounded contexts dostarczają wyłącznie swoje modele domenowe,
registry, handlery, UoW i konfigurację.

## Warstwy i topologia modułów

Kod platformy żyje w `shell/platform/` i dzieli się na:

```
shell/platform/
├── application/   # porty (Protocol), busy, kontekst tracingu/scopu, katalog kontraktów
├── bootstrap/     # composition root platformy (busy, logging)
├── domain/        # budulce DDD bez zależności: AggregateRoot, Entity, ValueObject, eventy, porty domenowe
├── framework/     # adaptery API (FastAPI), middleware, CLI
├── infrastructure/# adaptery: persistence SQL, messaging/delivery, serializacja, logging, konfiguracja
└── types/         # typy współdzielone (JSONString)
```

### Reguły zależności

Egzekwowane przez `import-linter` (pyproject.toml, kontrakt
`Platform must not import bounded contexts`):

1. **Platforma nie importuje żadnego bounded context** (`shell.definition_service`,
   `shell.execution_service`, `shell.session_service`, `shell.user_service`, `shell.project_service`,
   `shell.scheduling_service`, `shell.ingestion_service`).
2. Wewnątrz platformy kierunek zależności jest jednokierunkowy:
   `domain` ← `application` ← `infrastructure`/`framework`.
   - `domain` nie importuje niczego poza standardową biblioteką;
   - `application` definiuje porty (Protocol) i zależne od nich mechanizmy;
   - `infrastructure` implementuje porty aplikacji (adaptery);
   - `framework` eksponuje adaptery HTTP/CLI;
   - `bootstrap` składa wszystko (composition root).
3. Adaptery testowe (fakes) żyją w `shell/platform/infrastructure/persistence/memory/`.

### Bounded context jako konsument platformy

Każdy BC:
- definiuje własne modele ORM w swoim `metadata` i `baseline` (tabele delivery
  budowane z platformowych fabryk `build_*_model`);
- dostarcza kontener DI (Composition Root) łączący platformowe adaptery z
  własnymi repozytoriami/handlerami;
- rejestruje własny katalog kontraktów i registry eventów;
- uruchamia własny worker (PollingWorker) i aplikację FastAPI.

## Kluczowe przepływy

### Przetwarzanie komendy (write path)

```
API/CLI → Command → CommandBus → CommandHandler → UnitOfWork → Aggregate →
  DomainEvent → outbox (jedna transakcja) → commit
```

### Delivery między BC (at-least-once)

```
BC A: UoW → outbox → relay → transport → broker
BC B: broker → consumer → inbox → claim (lease) → processor → handler →
      efekt + outbox + ack (jedna transakcja)
```

Pełny opis: [delivery-overview](delivery-overview.md).

## Główne decyzje architektoniczne

- **Hexagonalna architektura**: porty w `application/`, adaptery w `infrastructure/`.
- **CQRS**: osobne komendy/zapytania, osobne modele read (query services).
- **Transactional outbox**: zdarzenia zapisywane w tej samej transakcji co stan
  domeny; relay przenosi je do brokera.
- **Inbox z lease (at-least-once)**: claim w krótkiej transakcji + lease,
  processing w osobnej transakcji z ack warunkowym; deduplikacja przez unikalny
  `(source_service, event_id|command_id)` na tabelach inbox
  (`on_conflict_do_nothing` przy insert + warunkowy ack).
- **Kontrakty jawne i wersjonowane**: `schema_version`, upcaster, jawny katalog.
- **Obserwowalność**: tracing (`correlation_id`/`causation_id`), metryki przez
  port `MetricsBackend`, readiness przez `ReadinessProbe`.

## Powiązane koncepcje

- [cqrs-buses](cqrs-buses.md)
- [unit-of-work](unit-of-work.md)
- [delivery-overview](delivery-overview.md)
- [ports-and-adapters](ports-and-adapters.md)
