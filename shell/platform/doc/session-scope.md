# Session Scope

## Cel / Co realizuje

Implementuje ambientowy scope jednej jednostki pracy przetwarzania delivery
(`DeliverySessionScope`) — obiekt, który "wisi" w `ContextVar` i wskazuje na
transakcję należącą do inbox processora. Handler-side'owy Unit of Work wchodzący
w zasięgu scope'a współdzieli sesję processora i odkłada commit, dzięki czemu
zmiana biznesowa, wiersze lokalnego outboxu i potwierdzenie inbox (ack) są
zapisywane w jednej transakcji. Flaga `rolled_back` sygnalizuje processorowi,
że handler cofnął odroczoną jednostkę pracy.

## Problem

Przetwarzanie rekordu inbox wymaga atomowości trzech zapisów: efektu
biznesowego (handler + jego UoW), wierszy outboxu oraz oznaczenia rekordu jako
przetworzonego. Bez wspólnej transakcji awaria w połowie zostawia system w
stanie niespójnym (efekt zapisany, ack nie, albo odwrotnie). Jednocześnie
niedopuszczalne jest współdzielenie jednej sesji SQLAlchemy między równoległymi
zadaniami — każdy rekord musi mieć własny scope i własną sesję.

## Realizacja techniczna

### Definicja — `shell/platform/application/context/session_scope.py`

- `DeliverySessionScope` — `@dataclass(slots=True)` z polami:
  - `session: Any` — sesja SQLAlchemy processora (właściciel transakcji);
  - `rolled_back: bool = False` — ustawiana, gdy handler cofnął odroczone UoW.
- `session_scope_var: ContextVar[DeliverySessionScope | None]` z domyślnym
  `None` (brak aktywnego scope'a);
- `get_session_scope() -> DeliverySessionScope | None`;
- `set_session_scope(scope) -> Token[DeliverySessionScope | None]`;
- `reset_session_scope(token)`.

Semantyka scope'a (komentarz w module):
- scope = dokładnie jeden rekord inbox i jedno UoW przetwarzania;
- jedna sesja SQLAlchemy nigdy nie jest współdzielona między równoległymi
  taskami — każdy rekord dostaje własny scope/sesję;
- `rolled_back` oznacza, że processor musi przerwać transakcję i zaplanować
  retry zamiast ack.

### Konsumpcja przez UoW — `SqlAlchemyUnitOfWorkBase`

W `__aenter__` (`sql_alchemy_uow_base.py`):

- `scope = get_session_scope()`; gdy `scope is not None` → `self._session =
  scope.session`, `_deferred_commit = True` (reuse sesji processora, commit
  odroczony do processora); w przeciwnym razie nowa sesja z `self._factory()`
  i `_deferred_commit = False`.

W `__aexit__` — gdy brak wyjątku i nie było commita, wywoływany jest
`await self.commit()`; w trybie deferred `commit()` wykonuje
`await self._session.flush()` (materializacja zmian, a nie finalny DB commit).

W `rollback()` — przy `_deferred_commit` po cofnięciu sesji:
`scope = get_session_scope()` i `scope.rolled_back = True` — sygnał dla
processora, by przerwać transakcję.

### Producent i konsument scope'a

Scope jest tworzony i publikowany przez inbox processor przed dispatchem
rekordu (proces claim→process→ack, patrz [inbox-processor](inbox-processor.md)),
a po zakończeniu przetwarzania resetowany przez `reset_session_scope(token)`.
Handlery (także te w `DeliveryDedupStore`, które rozwiązują sesję z aktywnego
scope'a) odczytują go przez `get_session_scope()`.

### Re-export

`shell/platform/infrastructure/context/__init__.py` re-exportuje
`DeliverySessionScope`, `get_session_scope`, `set_session_scope`,
`reset_session_scope` i `session_scope_var` z `application.context`.

## Kluczowe pliki

- `shell/platform/application/context/session_scope.py`
- `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py`
- `shell/platform/infrastructure/context/__init__.py`
- `shell/platform/application/ports/delivery_dedup_store.py`

## Powiązane koncepcje

- [inbox-processor](inbox-processor.md)
- [unit-of-work](unit-of-work.md)
- [transactional-outbox](transactional-outbox.md)
- [tracing-context](tracing-context.md)
- [processed-delivery-dedup](processed-delivery-dedup.md)
- [inbox-lifecycle](inbox-lifecycle.md)
