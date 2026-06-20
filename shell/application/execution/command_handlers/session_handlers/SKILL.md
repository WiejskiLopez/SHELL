# Zasady pracy z handlerami aplikacyjnymi

## Przed wprowadzeniem jakichkolwiek zmian

Przed modyfikacją handlera, komendy, kwerendy, eventu, DTO, mappera, strategii, portu, bądź jakiegokolwiek innego elementu warstwy aplikacyjnej — **zapoznaj się w całości** z plikiem:

`C:\Users\palysiewicz\IdeaProjects\SHELL\.agents\skills\shell-architecture\references\application.md`

Zawiera on obowiązujące reguły architektoniczne dla warstwy `application/`, w tym:
- CQRS — separacja komend i kwerend
- Unit of Work — wzorzec transakcyjny (w tym two-phase UoW)
- Bezstanowość handlerów
- DTO i mappery
- Strategie wykonania węzłów grafu
- Porty aplikacyjne (protokoły)
- Zasady importów (`from __future__ import annotations`, `TYPE_CHECKING`)

## Zakaz bezpośredniego wołania agregatów innych domen

Handler aplikacyjny **nie może bezpośrednio wołać agregatów, serwisów domenowych, repozytoriów ani żadnych innych elementów** należących do domeny innej niż ta, której dotyczy handler.

### Co wolno?

- Sięgać wyłącznie do agregatów i repozytoriów **własnej domeny** (tej, dla której handler został napisany).
- W przypadku konieczności skorzystania z funkcjonalności **innej domeny** — należy użyć **portu (protokołu)** zdefiniowanego w `application/ports/` lub w domenie docelowej.

### Gdzie implementować adaptery?

Implementacja adaptera dla portu pochodzącego z innej domeny **musi** znajdować się w `infrastructure/` w podkatalogu o nazwie zgodnej z nazwą tej domeny.

Przykład:
- Handler w `shell/application/execution/` potrzebuje funkcjonalności z domeny `platform`
- W `shell/domain/platform/ports/` (lub `shell/application/ports/`) istnieje port (protokół) `PlatformPort`
- Adapter tego portu implementujesz w `shell/infrastructure/platform/`
- Handler wstrzykuje port przez DI — nigdy nie tworzy bezpośrednio instancji agregatu z innej domeny

### Komunikacja poza domenę

To samo dotyczy komunikacji z **elementami spoza systemu domenowego** (np. zewnętrzne API, biblioteki systemowe, bazy danych). Zawsze przez port w warstwie aplikacyjnej/domenowej, z implementacją adaptera w `infrastructure/`.

## Metody wywoływane na agregatach w handlerze

### Tylko metody o nazwie biznesowej

Handler **może wywoływać na agregatach wyłącznie metody, których nazwy wyrażają intencję biznesową** w języku domeny — nigdy metody techniczne.

- ✅ **Dobrze**: `order.confirm()`, `workflow.mark_completed()`, `task.assign_to(user)`, `invoice.cancel()`
- ❌ **Źle**: `order.save()`, `workflow.update()`, `task.merge()`, `invoice.set_status()`, `aggregate.persist()`

Nazwa metody musi mówić **co się dzieje z biznesowego punktu widzenia**, a nie jaką operację techniczną wykonujemy.

### Metody techniczne (`save`, `update`, `merge`, `persist` itp.) są wewnętrzne dla agregatu

Wszelkie metody techniczne, które dotyczą zapisu, scalania, aktualizacji czy synchronizacji stanu — **służą wyłącznie do użytku wewnątrz agregatu**. Nie mogą być wołane przez handler ani żaden inny element zewnętrzny.

Agregat sam zarządza swoim stanem wewnętrznym. Handler jedynie wywołuje metody domenowe (biznesowe), a agregat wewnętrznie (w swojej metodzie biznesowej) wykonuje niezbędne operacje techniczne na swoich polach i za pomocą `append_event()` rejestruje zdarzenia domenowe.
