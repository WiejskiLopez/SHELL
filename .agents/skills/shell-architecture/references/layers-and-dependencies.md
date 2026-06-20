# Warstwy i reguły zależności

Architektura: **Clean Architecture + DDD + Hexagonal + CQRS**. Kierunek zależności jest jednokierunkowy — warstwa wewnętrzna nie wie o istnieniu zewnętrznych.

```
domain/ ← application/ ← infrastructure/ ← framework/ ← bootstrap/
```

## Tabela warstw

| Warstwa | Może importować | Przykładowa zawartość |
|---------|----------------|----------------------|
| `domain/` | Tylko stdlib | Entities, Value Objects, Aggregate Roots, Domain Events, Repository porty (Protocol), Domain Services, Domain Exceptions |
| `application/` | `domain/` + stdlib | Command/Query/Event Handlers, CommandBus/QueryBus/EventBus, DTO, Mapper, Strategy, Application Ports |
| `infrastructure/` | `domain/` + `application/` + biblioteki zewn. | SQLAlchemy ORM modele, SQL Reposytoria, InMemory adapters, logging, messaging (outbox/inbox), serializacja, system clock |
| `framework/` | Wszystkie niższe warstwy | FastAPI app + routers + middleware, CLI (argparse), entrypointy, orchestration runner |
| `bootstrap/` | Wszystkie warstwy (Composition Root) | DI Containery, Factory klasy, konfiguracja — jedyne miejsce gdzie tworzone są konkretne implementacje |
| `shared/` | Tylko stdlib | Narzędzia cross-cutting (UUID generator, serializacja) |

## Kluczowe zakazy

- `domain/` nigdy nie importuje: `sqlalchemy`, `pydantic`, `fastapi`, `motor`, `shell.application`, `shell.infrastructure`, `shell.framework`, `shell.bootstrap`
- `application/` nigdy nie importuje: `sqlalchemy`, `fastapi`, `motor`, `shell.infrastructure`, `shell.framework`, `shell.bootstrap`
- Żadna warstwa nie ma bezpośredniej wiedzy o innych warstwach poza dozwolonym kierunkiem zależności
- Wszystkie zależności między warstwami idą przez porty (Protocol) — nigdy przez konkretne implementacje

Reguły te są egzekwowane statycznie przez `tests/architecture/test_imports.py` i `import-linter`. Zanim zaproponujesz import, który przekracza warstwę, sprawdź czy nie istnieje już port dla tej zależności.

## Dlaczego to ma znaczenie

Każde naruszenie kierunku zależności tworzy sprzężenie zwrotne: zmiana w warstwie zewnętrznej (np. zmiana schematu SQLAlchemy) wymusza zmianę w warstwie wewnętrznej (domain). To niszczy testowalność domeny w izolacji i sprawia, że reguły biznesowe przestają być niezależne od technologii persystencji. Porty (Protocol) są jedynym dozwolonym mostem — domain definiuje kontrakt, infrastructure go implementuje.
