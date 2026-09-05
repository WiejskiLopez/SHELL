---
name: saga-pilot-and-readiness
description: Koncepcje przyszłościowe (roadmap) wokół wsparcia sag na platformie — wzorzec pilota sagi (ProjectProvisionSaga) oraz readiness w kontekście sag (probe backlogu saga_timeout). Używaj przy planowaniu/review nowych sag oraz gdy rozszerzasz ekspozycję zdrowia serwisów o stan quietów procesowych.
---

# Saga: wzorzec pilota oraz readiness — koncepcje przyszłościowe

> **Status:** niniejszy skill opisuje **koncepcje docelowe (roadmap / future concept)**.
> Część fundamentu jest **zaimplementowana i zwalidowana** (szkielet wsparcia sag:
> `SagaManager`, `SagaRepository`, `SagaTimeoutProcessor`, `CommandDeliveryDispatcher`,
> wrapper delivery do rejestracji ról). Zapisane poniżej jako *future*:
> **(1)** powielanie wzorca pilota na kolejne BC oraz **(2)** readiness w kontekście sag.
> Przed implementacją zawsze weryfikuj aktualny stan kodu w `shell/<service>/...`.

---

## 1. Wzorzec pilota sagi — referencja (future: propagacja na inne BC)

Pilot to **pierwsza działająca saga w jednym bounded contextu**, stanowiąca żywy
wzorzec implementacji. Nie jest to funkcja produkcyjna wymagająca replikacji w
każdym BC — wystarczy **jeden działający wzorzec** (`ProjectProvisionSaga` w
`project_service`). Propagacja na kolejne BC to świadoma, przyszłościowa decyzja.

### 1.1 Gdzie żyje pilota (referencja)

```
shell/project_service/
├── application/project/project_provision/
│   ├── commands/          # StartProjectProvisionCommand (inicjalizator), ProvisionWorkspaceCommand (krok),
│   │                      # ReleaseWorkspaceCommand (kompensacja) — wszystkie z __post_init__
│   ├── integration_events/# WorkspaceProvisioned/Failed/Released
│   └── command_handlers/  # uczestnicy: ProvisionWorkspaceHandler, ReleaseWorkspaceHandler
└── process/project/project_provision/
    ├── state.py           # ProjectProvisionStatus (StrEnum) + ProjectProvisionState (@dataclass)
    ├── steps.py           # StepRegistry (StepDefinition: krok → target_service, kompensacja)
    ├── manager.py         # ProjectProvisionSagaManager(SagaManager) — start/on_event/_complete/_fail
    └── handlers/          # StartProjectProvisionHandler + saga handlers event rezultatów
```

### 1.2 Jak powieniała się nowa saga w innym BC (future)

Kolejność implementacji nowej sagi na bazie wzorca:

1. **Aplikacja (uczestnicy i kontrakty):**
   - komendy kroków/kompensacji (`commands/`, `__post_init__` wymagany),
   - integration eventy rezultatów (`integration_events/`),
   - handlery uczestników (`command_handlers/`) — stateless, publikujące fakty,
   - wpisy eventów do katalogu kontraktów BC (`bootstrap/<bc>/contract_catalog.py`).
2. **Warstwa procesu (saga):**
   - `state.py` (Status StrEnum + State @dataclass — wymogi testów architektury),
   - `steps.py` (StepRegistry),
   - `manager.py` (podklasa `SagaManager`; `start` → krok → `on_event` completuje
     albo dispatchuje kompensację),
   - `handlers/` — start handler + saga handlers rezultatów (stateless, async).
3. **Wiring w DI:** fabryka `build_<saga>_manager_factory`, rejestracja start
   handlera na `CommandBus`, subskrypcja eventów rezultatów na `EventBus`.
4. **Reguły architektury, które muszą być spełnione:** komendy z `__post_init__`,
   handlery stateless/async/1-metoda, `state.py` dataclass/StrEnum, process→process
   imports (same layer), kontrakty w katalogu BC.

Test offline (SQLite) wykonuje pętlę: inicjalizator → instancja → krok przez
`command_outbox` → (transport symulowany klonem do `command_inbox`) → handler →
event rezultatu → kompletacja / kompensacja. Referencyjny test:
`shell/tests/project_service/unit/process/test_project_provision_saga.py`.

---

## 2. Readiness w kontekście sag (future concept)

### 2.1 Co to jest readiness

Readiness to **wskaźnik zdrowia usługi — "czy usługa jest gotowa przyjąć ruch"**
(możliwość wyłączenia z rotacji, gdy zalega). Odróżnij od liveness ("czy żyje").

W SHELL: port `ReadinessProbe` + adaptery:
- `SqlReadinessProbe` — baza odpowiada i backlog inboxu nie zalega,
- `RabbitReadinessProbe` — broker osiągalny,
- `CompositeReadinessProbe` — składa wiele probe'ów w jedno „gotowe/nie".
Endpoint: `framework/api/readiness.py`. Wiązanie per BC: provider `readiness_probe`
w kontenerze.

### 2.2 Readiness w kontekście sag (future)

Zaplanowano `SagaTimeoutReadinessProbe` — **readiness
backlogu timeoutów**: raportuje, czy tabela `saga_timeout` nie ma zaległych
rekordów (dojrzałych, `next_attempt_at <= now`, w stanie PENDING/RETRY, lub
wisi w PROCESSING z wygasłym lease). Cel: nawał timeoutów nie przechodzi
niezauważenie jako „usługa zdrowa".

Proponowany kształt (future concept — do wdrożenia):
```
shell/platform/observability/infrastructure/health/saga_timeout_readiness_probe.py
class SagaTimeoutReadinessProbe:
    def __init__(self, session_factory, timeout_model, max_backlog: int, consumer_name: str) -> None
    async def is_ready(self) -> bool:   # policz zaległe saga_timeout <= max_backlog
```
Podłączenie: dodać instancję do `CompositeReadinessProbe` w kontenerze BC, który
deklaruje sagi (podobnie jak `SqlReadinessProbe` bierze `inbox_model`).

> **Status:** nie zaimplementowane — pozycja roadmap. Implementacja jest mała i
> testowalna offline (SQLite): count zaległych wierszy `saga_timeout` vs `max_backlog`.

---

## 3. Kluczowe pliki i reguły

- Pilotażowa saga (zaimplementowana): `shell/project_service/process/project/project_provision/`
  + uczestnicy w `shell/project_service/application/project/project_provision/`.
- Mechanizm sagi (zaimplementowany, wydzielony do biblioteki): `packaging/saga-orchestration`
  (`process/saga` — kontrakty i manager; `infrastructure/process/saga` — adaptery SQL,
  repozytoria, worker timeoutów). Capability opt-in per serwis (`include_saga`, migracja
  adopcyjna per serwis).
- Mechanizm readiness (istniejący): `shell/platform/observability/infrastructure/health/*`,
  `shell/platform/observability/framework/api/readiness.py`.
- Reguły: kontrakty w `bootstrap/<bc>/contract_catalog.py`; testy process:
  `shell/tests/architecture/test_process_structure__*`.