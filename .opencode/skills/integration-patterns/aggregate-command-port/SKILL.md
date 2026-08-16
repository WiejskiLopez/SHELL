---
name: aggregate-command-port
description: Wzorzec Command/Operation Port — porty, przez które agregat zleca operację lub mutację w innym agregacie/BC. Definicje portów w katalogu `ports/`, adaptery w infrastrukturze konsumującego agregatu. Używaj gdy agregat tworzy, zmienia, usuwa lub uruchamia zachowanie w źródle.
---

# Aggregate Command Port — porty operacji i mutacji

## 1. Definicja

**Command/Operation Port** to port (Protocol) przez który agregat zleca **operację, mutację lub
uruchomienie zachowania** w innym agregacie, BC lub zewnętrznym systemie. W przeciwieństwie do
Providera port operacyjny zmienia stan lub wykonuje akcję po stronie źródła.

Reguła decyzyjna: jeśli port ma **dowolny** element mutujący — należy do tego wzorca i nazwa musi
wskazywać operację (`<Czasownik><Obiekt>Port`). Porty wyłącznie do odczytu należą do wzorca
Aggregate Provider (`<Dane>Provider`). Oba typy żyją w tym samym katalogu `ports/` — rozróżnia je
**wyłącznie nazewnictwo**.

```python
# shell/<bc>/domain/<bc>/aggregates/<aggregate>/ports/workflow_session_command_port.py
class WorkflowSessionCommandPort(Protocol):
    async def add_session_output(self, session_id: SessionId, output: SessionOutput) -> None: ...
    async def complete_session(self, session_id: SessionId, result: SessionResult) -> SessionOutcome: ...
```

## 2. Obowiązkowość portu

Konsument (handler, domain service, inny agregat) nigdy nie wstrzykuje bezpośrednio serwisu komend,
repozytorium, agregatu źródłowego ani adaptera — również w obrębie tego samego BC. Adapter to
jedyny komponent który zna serwis/HTTP kontrakt źródła. Wydzielenie agregatu na osobny mikroserwis
zmienia tylko adapter.

```
❌ handler graph_execution → wstrzyknięty WorkflowSessionCommandService innego agregatu
✅ handler graph_execution → WorkflowSessionCommandPort (port z ports/)
        ↕
    adapter (infrastruktura konsumenta) — JEDYNE miejsce które zna serwis/HTTP źródła
```

## 3. Katalog portów

```
shell/<bc>/domain/<bc>/aggregates/<aggregate>/ports/
└── workflow_session_command_port.py
```

- Katalog `ports/` jest per agregat konsumujący, nigdy per źródło. Współdzielą go porty operacji
  (ten wzorzec) i porty odczytu (wzorzec Aggregate Provider).
- Port jest **własnością konsumenta** — nie leży w BC źródłowym.
- Port operuje na **własnych typach konsumenta** (VO, ID, lokalne wynik/status). Nigdy na obcych
  agregatach ani DTO źródła.

## 4. Nazewnictwo

| Artefakt | Wzorzec | Przykład |
|----------|---------|----------|
| Port | `<Czasownik><Obiekt>Port` | `WorkflowSessionCommandPort` |
| Plik portu | `<czasownik>_<obiekt>_port.py` | `workflow_session_command_port.py` |
| Adapter | `<PortNazwa><Transport>Adapter` | `WorkflowSessionCommandPortHttpAdapter` |
| Plik adaptera | `<port_nazwa>_<transport>_adapter.py` | `workflow_session_command_port_http_adapter.py` |

Nazwa portu wskazuje **działanie** (`add_session_output`, `complete_session`), nie odczyt.
`<Transport>` w adapterze: `Http` (cross-BC), `Sql`/`Local` (wewnętrzny serwis), `InMemory` (testy).
Adapter **dziedziczy po porcie**:

```python
class WorkflowSessionCommandPortHttpAdapter(WorkflowSessionCommandPort):
    ...
```

## 5. Reguły kontraktu

1. **Własność konsumenta** — port definiuje agregat który zleca operację.
2. **Kontrakt zwraca lokalny wynik** — wynik operacji, identyfikator, status lub `None`. Nigdy obcy
   agregat.
3. **Async** — każda metoda portu jest `async`.
4. **VO konsumenta w sygnaturach** — bez typów prostych.
5. **Mapowanie w adapterze** — adapter mapuje lokalną komendę → wersjonowany request źródła;
   odpowiedź źródła → lokalny wynik.
6. **Błędy transportowe → wyjątki domenowe** — adapter opakowuje błędy HTTP/timeouty w dedykowane
   wyjątki domeny konsumenta.
7. **Idempotencja** — operacje mogą być powtarzane; adapter/biznes musi być odporny na duplikaty.
8. **Retry / Circuit Breaker** — na poziomie adaptera, nigdy domeny.

## 6. Adaptery w infrastrukturze

Implementacje lądują w infrastrukturze **konsumującego agregatu**, w katalogu `adapters/`, w
podfolderze nazwanym od portu. Jeden podfolder skupia wszystkie transporty danego portu oraz jego
kontrakty i mappery:

```
shell/<bc>/infrastructure/<bc>/<aggregate>/adapters/<port_name>/
├── <port_name>_http_adapter.py      # WorkflowSessionCommandPortHttpAdapter (cross-BC)
├── <port_name>_sql_adapter.py       # WorkflowSessionCommandPortSqlAdapter (lokalny serwis)
├── contracts/v1/<nazwa>_request.py  # lokalny, wersjonowany model komendy
└── mappers/<nazwa>_response_to_domain.py
```

```
local command -> versioned HTTP request -> remote operation result -> local result
```

Adapter lokalny wywołuje serwis komend **innego agregatu** (ten sam BC) — jedynego miejsca które zna
źródło:

```python
class WorkflowSessionCommandPortSqlAdapter(WorkflowSessionCommandPort):
    def __init__(self, session_command_service: WorkflowSessionCommandService) -> None:
        self._session_command_service = session_command_service  # jedyne miejsce które zna serwis źródła

    async def add_session_output(self, session_id: SessionId, output: SessionOutput) -> None:
        await self._session_command_service.add_session_output(session_id, output)
```

### Testy

- **InMemory/fake adapter** — implementuje ten sam port, używany w testach jednostkowych.
- **Test integracyjny adaptera** — z prawdziwym zasobem.
- **Contract test** dla kontraktów cross-BC w `shell/tests/contracts/`.

## 7. Port operacyjny a eventy — granica sync/async

`ports/` obejmuje **synchroniczne** komendy/operacje (HTTP lub lokalny serwis). Operacja jest krótka
i wymaga natychmiastowego potwierdzenia.

Gdy operacja jest **asynchroniczna** — eventual consistency, czasowa niedostępność, proces długotrwały,
koordynacja wieloagregatowa — **nie modelujemy jej jako portu operacyjnego**:

- publikujemy **Domain Event / Integration Event** i subskrybujemy po stronie odbiorcy, albo
- orkiestrujemy przez **sagę / process manager** (warstwa `process/`).

```
sync, szybka komenda            → ports/ (port operacyjny)
async, eventual consistency      → eventy
długotrwała operacja wielo-BC    → saga / process manager
```

## 8. Czym port operacyjny NIE jest

| Koncept | Różnica |
|---------|---------|
| **Provider** | Provider = tylko odczyt (`<Dane>Provider`). Port z dowolną mutacją to Command Port — oba w `ports/`, rozróżnia nazwa. |
| **Repository** | Repository = persystencja WŁASNEGO agregatu. Port operacyjny nie udaje repozytorium obcego BC. |
| **QueryService** | QueryService = odczyt (read projection). Port operacyjny wykonuje akcję. |
| **Event** | Event = komunikacja asynchroniczna. Port operacyjny = synchroniczna komenda. |
| **Adapter** | Adapter implementuje port i zna transport; nigdy nie jest wstrzykiwany do konsumenta bezpośrednio. |

## 9. Checklista

- [ ] Port (Protocol) w `domain/<bc>/aggregates/<aggregate>/ports/`
- [ ] Nazwa wskazuje działanie, nie odczyt
- [ ] Zwraca lokalny wynik/status/ID, nigdy obcy agregat
- [ ] Adapter w `infrastructure/<bc>/<aggregate>/adapters/<nazwa>/` (`<nazwa>_http_adapter.py` cross-BC, `<nazwa>_sql_adapter.py` lokalny)
- [ ] Adapter dziedziczy po porcie, nazwa `<Port><Transport>Adapter`
- [ ] Idempotencja + błędy → wyjątki domenowe
- [ ] InMemory/fake adapter dla testów jednostkowych
- [ ] Brak bezpośredniego wstrzykiwania serwisu/QueryService/Repository źródła do konsumenta
- [ ] Operacja długotrwała/async → event lub saga, nie port operacyjny
