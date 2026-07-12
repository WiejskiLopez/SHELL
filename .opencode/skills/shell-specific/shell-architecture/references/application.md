# Warstwa aplikacyjna

`application/` zawiera atomowe operacje przypadków użycia: pobiera jeden agregat z repozytorium, wywołuje metody domenowe, persystuje wynik. Nie zawiera reguł biznesowych ani orkiestracji wieloagregatowej.

**Orkiestracja** (koordynacja wielu agregatów, saga, process manager) należy do warstwy `process/`. Application wysyła komendy, process decyduje KIEDY i W JAKIEJ KOLEJNOŚCI.

## CQRS — Command / Query Separation

- **Commands** zmieniają stan, zwracają `None` lub ID utworzonego obiektu
- **Queries** nie zmieniają stanu, zwracają DTO
- Każda komenda/kwerenda w osobnej klasie w `application/<bc>/<aggregate>/commands/` lub `application/<bc>/<aggregate>/queries/`
- Każdy handler w osobnej klasie w `application/<bc>/<aggregate>/command_handlers/` lub `application/<bc>/<aggregate>/query_handlers/`
- Handler spełnia kontrakt: `handle(command: TCommand) -> Any`

### Command / Query / Event Bus
- `CommandBus` → rejestracja `command_type → handler_factory`
- `QueryBus` → rejestracja `query_type → handler_factory`
- `EventBus` → rejestracja `event_type → handler_factory` (1:N — jeden event może mieć wielu subskrybentów)
- Bus jest tylko dispatcherem — nie zawiera logiki biznesowej
- Busy konfigurowane w `bootstrap/`

## Unit of Work (UoW) — wzorzec transakcyjny

`UnitOfWork` jest zawsze async context managerem. Outbox zapisywany w tej samej transakcji co zmiany domenowe.

### Two-phase UoW — dla długotrwałych operacji

Gdy między pobraniem agregatu a zapisem wyniku jest długotrwała operacja zewnętrzna (np. `NodeExecutionProcessRunner.run()`), nie trzymaj otwartej transakcji na ten czas. Użyj dwóch osobnych bloków.

## Handler — bezstanowy

Handler nigdy nie przechowuje mutowalnego stanu między wywołaniami `handle()`. W przypadku stateful orchestration (saga, process manager) — używaj warstwy `process/`.

## DTO (Data Transfer Object)

- W `application/<bc>/<aggregate>/dto/` — proste dataclasses lub Pydantic modele
- Służą wyłącznie do przenoszenia danych między warstwami
- Nigdy nie zawierają logiki biznesowej

## Mapper

- W `application/<bc>/<aggregate>/mappers/` lub `infrastructure/<bc>/<aggregate>/persistence/sql/mappers/` — konwersja Entity ↔ DTO
- Statyczne metody lub osobne klasy
- Mapper jest własnością warstwy aplikacyjnej

Każde pole DTO musi mieć źródło. Hardcoded `[]` albo `""` zamiast mapowania to sygnał, że refaktoryzacja agregatu nie została domknięta w warstwie aplikacyjnej — DTO stanie się niezgodne ze stanem domenowym i zwróci klientowi puste/źle dane.

## Strategy — NodeExecutionStrategy

- W `framework/execution/entrypoints/strategies/`
- `protocol.py` definiuje kontrakt (Protocol) z adnotacją `@runtime_checkable`
- `_base_strategy.py` — wspólna logika dla wszystkich strategii
- `registry.py` — rejestr dostępnych strategii z rzucaniem `InvalidNodeMode` dla nieznanych trybów

## Application Port (Protocol)

- W `application/<bc>/ports/` — interfejsy dla adapterów infrastrukturalnych
- Każdy w osobnym module (`unit_of_work.py`, `time.py`, `logging.py`)
- Obowiązkowe porty: `UnitOfWork`, `Clock`, `IdGenerator`, `EventPublisher`, `Logger`, `NodeExecutionProcessRunner`, `NodeExecutionWorkspace`, `TaskExecutionLoader`
- `ports.py` agreguje re-exporty dla wygody

## Factory / Bus — zakaz `Any` escape

W plikach factory nie używaj `Any` do pomijania type-checkingu. Używaj `providers.Container[T]` lub jawnych typów kontenera zamiast `Any` + `type: ignore`.
