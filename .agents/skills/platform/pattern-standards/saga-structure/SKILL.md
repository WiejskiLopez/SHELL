# Saga / Process Manager Structure

> Reguły struktury klas Saga i Process Manager we wszystkich bounded contextach.

## Definicja

- Saga jest potrzebna gdy pojedyncza operacja biznesowa rozciąga się na wiele agregatów/BC i wymaga: atomowości (kompensacje), koordynacji, długiego trwania, komunikacji asynchronicznej.

## Choreografia

- Decentralna, przez eventy.
- Każdy uczestnik reaguje na eventy i emituje własne.
- Brak centralnego koordynatora.
- Używaj dla prostych, liniowych przepływów (<= 5 kroków).

```python
# Workflow BC
class WorkflowStartedHandler:
    async def handle(self, workflow_started_event: WorkflowStartedEvent) -> None:
        # reakcja: utwórz zasoby, emituj ResourceProvisionedEvent
        ...

# Resource BC
class ResourceProvisionedHandler:
    async def handle(self, resource_provisioned_event: ResourceProvisionedEvent) -> None:
        # reakcja: konfiguruj, emituj ResourceConfiguredEvent
        ...
```

## Orkiestracja (Process Manager)

- Centralny Process Manager (Orchestrator) zarządza krokami.
- Ma własny stan — przechowywany w bazie, pozwalający na restart po awarii.
- Używaj dla złożonych przepływów z warunkami, pętlami, timeoutami.

```python
class WorkflowExecutionSaga:
    def __init__(self, ...) -> None:
        self._id: SagaId
        self._state: SagaState
        self._completed_steps: list[StepName]
        self._failed_steps: list[StepName]

    def start(self) -> None:
        self._state = SagaState.RUNNING
        self._execute_step(StepName.PROVISION_RESOURCES)

    def on_resource_provisioned(self, event: ResourceProvisionedEvent) -> None:
        self._completed_steps.append(StepName.PROVISION_RESOURCES)
        self._execute_step(StepName.CONFIGURE_RESOURCES)

    def on_step_failed(self, event: StepFailedEvent) -> None:
        self._state = SagaState.FAILING
        self._compensate_all()

    def _compensate_all(self) -> None:
        for step in reversed(self._completed_steps):
            self._execute_compensation(step)
        self._state = SagaState.COMPENSATED
```

## Kompensacje

- Każdy krok sagi musi mieć akcję kompensującą — cofającą zmianę.
- Kompensacje wykonywane są w odwrotnej kolejności.
- Jeśli krok nie wymaga kompensacji → `noop`.

## Timeout

- Każdy krok sagi może mieć timeout — jeśli nie otrzymamy odpowiedzi w określonym czasie, uruchamiamy kompensacje.

## Trwałość

- Saga musi być trwała — zapisana w bazie, aby przetrwać restart aplikacji.

## Rekomendacja

- Zacznij od choreografii. Gdy logika robi się zbyt skomplikowana → migruj do orkiestracji.

## Lokalizacja

- `shell/application/<bc>/sagas/`
