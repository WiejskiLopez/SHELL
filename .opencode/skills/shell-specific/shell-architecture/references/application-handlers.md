# Zasady pracy z handlerami aplikacyjnymi

> Uzupełnienie do `application.md` — reguły dotyczące wyłącznie handlerów warstwy aplikacyjnej (command, query i event handlers).

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

Agregat sam zarządza swoim stanem wewnętrznym. Handler jedynie wywołuje metody domenowe (biznesowe), a agregat wewnętrznie (w swojej metodzie biznesowej) wykonuje niezbędne operacje techniczne na swoich polach i za pomocą `append_event()` rejestruje zdarzenia domenowe.


