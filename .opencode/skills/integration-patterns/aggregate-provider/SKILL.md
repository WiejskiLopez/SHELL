---
name: aggregate-provider
description: Wzorzec Provider — porty tylko-do-odczytu danych dostarczanych agregatowi z zewnątrz (inny agregat, inny BC, zewnętrzne źródło). Definicje portów w katalogu `ports/`, adaptery w infrastrukturze konsumującego agregatu w katalogu `adapters/`. Używaj gdy agregat pobiera dane do podjęcia decyzji, bez modyfikacji źródła.
---

# Aggregate Provider — porty odczytu danych zewnętrznych

## 1. Definicja

**Provider** to port (Protocol) przez który agregat pobiera dane z zewnętrznego źródła —
innego agregatu, innego BC, zewnętrznego mikroserwisu lub dowolnego systemu — wyłącznie **do odczytu**.

Provider udostepnia odczyt danych z zewnetrznego zrodla. Operacje tworzenia, aktualizacji, usuwania i uruchamiania procesu należą do Command Port.

```python
# shell/<service>/domain/<bc>/aggregates/<aggregate>/ports/graph_definition_provider.py
class GraphDefinitionProvider(Protocol):
    async def get_graph_definition(self, definition_id: GraphDefinitionReferenceId) -> GraphDefinitionReference | None: ...
    async def get_graph_definition_by_semantic(self, query: GraphDefinitionSemanticQuery) -> GraphDefinitionReference | None: ...
```

## 2. Porty wyjściowe agregatu — dwa katalogi

Każdy agregat definiuje swoje porty wyjściowe w dwóch katalogach swojej domeny. Provider to
jeden z dwóch wzorców portów wyjściowych (obok Repository):

```
shell/<service>/domain/<bc>/aggregates/<aggregate>/
├── repositories/   # PERSYSTENCJA WŁASNYCH danych agregatu (save / get_by_id / delete) — wzorzec Repository
└── ports/          # WSZYSTKIE POZOSTAŁE PORTY ZEWNĘTRZNE — odczyt (Provider) i operacje/mutacje (Command Port)
```

W katalogu `ports/` żyją razem porty odczytu (Provider) i porty operacji (Command Port). Dzieli je
wyłącznie **nazewnictwo**, nie katalog:

| Metoda portu | Wzorzec | Nazwa portu |
|--------------|---------|-------------|
| czyta dane, nic nie zmienia | **Aggregate Provider** (ten wzorzec) | `<Dane>Provider` |
| tworzy / zmienia / usuwa / uruchamia | Command Port | `<Czasownik><Obiekt>Port` |
| pełny cykl życia WŁASNEGO agregatu (persystencja) | Repository | `<Agregat>Repository` |

Jeśli port ma **dowolny** element mutujący — nazwa musi wskazywać operację (Command Port), nie odczyt.

## 3. Obowiązkowość portu — kardynalna reguła

Konsument korzysta z portu Provider, a adapter portu zna QueryService, Repository albo kontrakt HTTP zrodla. Agregaty zachowuja autonomie wewnatrz BC.

```
✅ handler graph_execution → GraphDefinitionProvider (port z ports/)
        ↕
    adapter (infrastruktura konsumenta) — JEDYNE miejsce które zna QueryService/HTTP źródła
```

Adapter to jedyny komponent który importuje i woła cudzy QueryService (adapter lokalny) lub HTTP
kontrakt (adapter cross-BC). Dzięki temu wydzielenie agregatu na osobny mikroserwis zmienia **tylko
adapter** — port i cała logika konsumenta zostają bez zmian.

## 4. Katalog portów

```
shell/<service>/domain/<bc>/aggregates/<aggregate>/ports/
├── graph_definition_provider.py     # Provider (tylko odczyt)
├── workflow_session_command_port.py           # Command Port (operacja) — obok, ten sam katalog
└── graph_definition_semantic_query.py         # VO query, jeśli potrzebne
```

- Katalog `ports/` jest per agregat konsumujący, nigdy per źródło.
- Port jest **własnością konsumenta** — nie leży w BC źródłowym.
- Port operuje na **własnych typach konsumenta**: ValueObjecty / read modele / snapshoty. Nigdy na
  obcych agregatach, DTO źródła ani modelach ORM.
- Pobieraj tylko pola których lokalna domena faktycznie używa.

## 5. Nazewnictwo

| Artefakt | Wzorzec | Przykład |
|----------|---------|----------|
| Port | `<Dane>Provider` | `GraphDefinitionProvider` |
| Plik portu | `<dane>_provider.py` | `graph_definition_provider.py` |
| Adapter | `<PortNazwa><Transport>Adapter` | `GraphDefinitionProviderHttpAdapter` |
| Plik adaptera | `<port_nazwa>_<transport>_adapter.py` | `graph_definition_provider_http_adapter.py` |

`<Transport>` w adapterze: `Http` (cross-BC), `Sql`/`Local` (wewnętrzny QueryService), `InMemory`
(testy). Adapter **dziedziczy po porcie**:

```python
class GraphDefinitionProviderHttpAdapter(GraphDefinitionProvider):
    ...
```

## 6. Reguły kontraktu

1. **Własność konsumenta** — port definiuje agregat który potrzebuje danych.
2. **Read-only** — żadnej metody mutującej w porcie.
3. **Async** — każda metoda portu jest `async` (dane spoza agregatu).
4. **VO konsumenta w sygnaturach** — bez typów prostych.
5. **Mapowanie w adapterze** — adapter mapuje surową odpowiedź źródła (DTO/HTTP) na VO konsumenta;
   nigdy nie przepuszcza surowego DTO źródła.
6. **Błędy transportowe → wyjątki domenowe** — adapter łapie błędy HTTP/timeouty i opakowuje w
   dedykowany wyjątek domeny konsumenta (np. `GraphDefinitionUnavailable`). Nie propaguje surowych
   wyjątków transportowych.
7. **Retry / Circuit Breaker** — na poziomie adaptera, nigdy domeny.
8. **Minimalny kontrakt** — port definiuje tylko to, czego konsument naprawdę potrzebuje.

## 7. Adaptery w infrastrukturze

Implementacje lądują w infrastrukturze **konsumującego agregatu**, w katalogu `adapters/`, w
podfolderze nazwanym od portu. Jeden podfolder skupia wszystkie transporty danego portu oraz jego
kontrakty i mappery:

```
shell/<service>/infrastructure/<bc>/<aggregate>/adapters/<port_name>/
├── <port_name>_http_adapter.py      # GraphDefinitionProviderHttpAdapter (cross-BC)
├── <port_name>_sql_adapter.py       # GraphDefinitionProviderSqlAdapter (lokalny QueryService)
├── contracts/v1/<nazwa>_response.py # lokalny, wersjonowany model kontraktu (HTTP)
└── mappers/<nazwa>_response_to_domain.py
```

Adapter cross-BC mapuje kontrakt transportowy:

```
remote API V1 response
    -> consumer-local ResponseV1 (contracts/v1)
    -> mapper / Anti-Corruption Layer
    -> consumer VO / read model
```

Dodatkowe pola odpowiedzi są ignorowane. Brak wymaganego pola = błąd kontraktu, nigdy fałszywa
wartość domyślna.

Adapter lokalny korzysta z QueryService **innego agregatu** (ten sam BC) — jedynego miejsca które
zna źródło:

```python
class GraphDefinitionProviderSqlAdapter(GraphDefinitionProvider):
    def __init__(self, query_service: GraphExecutionQueryService) -> None:
        self._query_service = query_service  # jedyne miejsce które zna QueryService źródła

    async def get_graph_definition(self, definition_id: GraphDefinitionReferenceId) -> GraphDefinitionReference | None:
        source = await self._query_service.get_graph_definition(definition_id.value)
        if source is None:
            return None
        return self._mapper.to_domain(source)
```

### Testy

- **InMemory/fake adapter** — implementuje ten sam port, używany w testach jednostkowych (jak
  repozytoria InMemory).
- **Test integracyjny adaptera** — z prawdziwym zasobem (HTTP test server / SQL).
- **Contract test** dla kontraktów cross-BC w `shell/tests/contracts/`.

## 8. Czym Provider NIE jest

| Koncept | Różnica |
|---------|---------|
| **Repository** | Repository = persystencja WŁASNEGO agregatu (pełny cykl życia). Provider = cudze dane, tylko odczyt. |
| **Command Port** | Port z dowolną mutacją to Command Port (nazwa wskazuje operację), nie Provider. Oba typy żyją w `ports/` — rozróżnia je nazwa. |
| **QueryService** | QueryService = read projection / implementacja wewnątrz agregatu lub źródła. Provider = port konsumenta. Adapter providera może **wewnętrznie** używać QueryService źródła. |
| **Domain Service** | Domain Service = logika biznesowa (może korzystać z portów). Provider = sam kontrakt odczytu. |

## 9. Checklista

- [ ] Port (Protocol) w `domain/<bc>/aggregates/<aggregate>/ports/`
- [ ] Nazwa `<Dane>Provider` — tylko odczyt, wszystkie metody `async`
- [ ] Sygnatury na VO konsumenta, bez typów prostych
- [ ] Adapter w `infrastructure/<bc>/<aggregate>/adapters/<nazwa>/` (`<nazwa>_http_adapter.py` cross-BC, `<nazwa>_sql_adapter.py` lokalny)
- [ ] Adapter dziedziczy po porcie, nazwa `<Port><Transport>Adapter`
- [ ] Mapowanie na VO konsumenta, błędy → wyjątki domenowe
- [ ] InMemory/fake adapter dla testów jednostkowych
- [ ] Brak bezpośredniego wstrzykiwania QueryService/Repository źródła do konsumenta
