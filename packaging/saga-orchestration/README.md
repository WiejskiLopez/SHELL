# saga-orchestration

Generyczny mechanizm orkiestracji sag wydzielony z SHELL (opcjonalna capability).

## Zakres

- `process/saga` — kontrakty i rdzeń bez zależności od SHELL: `SagaManager`,
  `SagaStatus`/`SagaState`, `SagaInstance`, `SagaTimedOut`, `StepDefinition`/`StepRegistry`,
  `EventRoute`/`SagaRegistry`, porty `SagaRepository`, `SagaTimeoutRepository`,
  `CommandDeliveryDispatcher`.
- `infrastructure/process/saga` — opcjonalne adaptery techniczne integrujące z SHELL:
  modele ORM `saga_instance`/`saga_timeout` (`build_saga_delivery_models`),
  `SqlSagaRepository`, `SqlSagaTimeoutRepository`, `InMemorySagaRepository`,
  `SagaTimeoutProcessor` (worker), `build_command_delivery_dispatcher`.
- `infrastructure/persistence/migrations/sql/versions` — referencyjne migracje
  capability: `saga_0001_create_instance` → `saga_0002_create_timeout`.

Pakiet nie zawiera konkretnych sag, komend, eventów ani migracji konkretnego serwisu.
Biblioteka nie importuje modeli ORM serwisu, `DATABASE_URL`, routerów FastAPI,
konkretnych komend/eventów SHELL ani RabbitMQ.

## Integracja z serwisem

Mechanizm sagi jest **opcjonalny per serwis**. Włączenie capability to świadoma
decyzja serwisu; serwis bez sagi nie dostaje tabel, modeli ani handlerów sagowych.

### 1. Instalacja

Rdzeń (`process/saga`) nie zależy od SHELL. Adaptery integrujące z transportem SHELL
wymagają extra `shell`:

```text
python -m pip install -e "packaging/saga-orchestration[shell]"
```

### 2. Włączenie capability w migracjach (opcjonalne)

Platformowy runner nie tworzy tabel sagi automatycznie. Parametr `include_saga`
w `run_platform_baseline(...)` domyślnie ma wartość `False`:

- serwis **bez sagi** — zostaje przy wartości domyślnej; nie tworzy `saga_instance`/`saga_timeout`;
- serwis **z sagą** — ustawia `include_saga=True`.

Historyczne revisions `platform_0008_saga_instance` / `platform_0009_saga_timeout`
pozostają w platformie wyłącznie dla kompatybilności baz, które już je wykonały.
Nowe bazy serwisu z capability dostają tabele z referencyjnego łańcucha biblioteki.

### 3. Rejestracja modeli w `MetaData` serwisu

Modeli nie dodaje się globalnie. Serwis z capability rejestruje modele w swoim
`MetaData` przez `build_saga_delivery_models(base)` — tylko po włączeniu capability.

### 4. Adopcja migracji

Serwis pozostaje właścicielem swojej bazy i jawnie decyduje, jak adoptuje tabele:

- własna migracja adopcyjna (wzorzec `project_0004_saga_capability_adopted`) —
  weryfikuje istnienie tabel, nie tworzy ich drugi raz, `downgrade()` nie usuwa stanu;
- albo własne migracje zgodne z kontraktem referencyjnym biblioteki;
- albo referencyjny łańcuch biblioteki (`saga_0001`/`saga_0002`) — tylko jeśli serwis
  celowo go adoptuje.

Biblioteka nigdy nie uruchamia migracji automatycznie przy instalacji.

### 5. Wiring w composition root

Serwis z capability rejestruje: `SagaRepository`, `SagaTimeoutRepository` (jeśli używa
timeoutów), `SagaTimeoutProcessor` (worker przez `run_delivery_workers(...)`,
`extra_processors=...`), `build_command_delivery_dispatcher(...)`, a także konkretne
fabryki managera i handlery startu/rezultatów. Serwis bez sagi nie rejestruje żadnego
z tych elementów.

### 6. Konkretna saga zostaje w serwisie

Biblioteka dostarcza generyczny mechanizm. Reguły biznesowego przebiegu
(`manager.py` jako podklasa `SagaManager`, `steps.py`, `handlers/`) należą do
serwisu, np. `shell/project_service/process/project/project_provision/`.

### 7. Korelacja

- Instancja sagi jest korelowana przez parę `saga_type + saga_key`
  (`SagaRepository.get_by_key(saga_type, saga_key)`).
- `saga_id` jest wyłącznie wewnętrzną tożsamością `SagaInstance` i rekordów timeoutów.
  Nie dodaje się go do bazowych klas `Command`/`IntegrationEvent`, payloadów ani kopert.
- Komendy kroków i eventy rezultatów nie niosą `saga_id` — handlery procesu odnajdują
  sagę po kluczach biznesowych.

### 8. Czego nie robi serwis bez sagi

- nie ustawia `include_saga=True`;
- nie rejestruje modeli, repozytoriów, dispatchera ani procesora timeoutów;
- nie importuje adapterów persistence sagi;
- nie otrzymuje tabel `saga_instance`/`saga_timeout` na świeżej bazie.

## Instalacja developerska (tylko rdzeń)

```text
python -m pip install -e packaging/saga-orchestration
```