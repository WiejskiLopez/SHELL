# Factory Structure

> Reguły struktury klas Factory (Factory Method i Factory Class) we wszystkich bounded contextach.

## Definicja

- Factory Method — proste tworzenie, metoda klasowa na agregacie, encji lub VO.
- Factory Class — osobna klasa dla złożonego tworzenia, gdy proces wymaga zależności, walidacji międzyobiektowej lub koordynacji.

## Factory Method

- `@classmethod` na samym obiekcie.
- Używany gdy tworzenie jest proste lub wymaga tylko parametrów wejściowych.

```python
@classmethod
def create(cls, name: WorkflowName, owner_id: UserId, nodes: list[NodeConfig]) -> Workflow:
    workflow = cls(WorkflowId.generate(), name, WorkflowStatus.IDLE)
    for node_config in nodes:
        workflow._add_node(Node.from_config(node_config))
    workflow.append_event(WorkflowCreatedEvent(workflow.id, owner_id))
    return workflow
```

## Factory Class

- Osobna klasa w `shell/domain/<bc>/factories/`.
- Używany gdy: tworzenie wymaga zewnętrznych danych (konfiguracja, polityki); należy wygenerować wiele encji dziecięcych; potrzebna jest walidacja krzyżowa przed utworzeniem; agregat wymaga wstrzyknięcia usług domenowych.

```python
class WorkflowFactory:
    def __init__(self, id_generator: IdGenerator, clock: Clock) -> None:
        self._id_generator = id_generator
        self._clock = clock

    def create_workflow(self, name: WorkflowName, owner_id: UserId, template: WorkflowTemplate) -> Workflow:
        workflow_id = WorkflowId(self._id_generator.generate())
        nodes = [self._create_node(template_node) for template_node in template.nodes]
        workflow = Workflow(workflow_id, name, nodes)
        workflow.append_event(WorkflowCreatedEvent(workflow_id, owner_id, self._clock.now()))
        return workflow
```

## restore()

- Każdy agregat ma factory method `restore()` (lub osobną klasę) do rekonstrukcji z persistance.
- `restore()` pomija walidację biznesową — zakłada że dane są spójne.

```python
@classmethod
def restore(cls, workflow_id: WorkflowId, name: WorkflowName, status: WorkflowStatus, nodes: list[Node], version: int) -> Workflow:
    workflow = cls.__new__(cls)
    super(Workflow, workflow).__init__(workflow_id)
    workflow._name = name
    workflow._status = status
    workflow._nodes = nodes
    workflow._version = version
    return workflow
```

## Zależności

- Factory może mieć zależności (Domain Services, IdGenerator, Clock).
- Factory w domenie — brak importów infrastrukturalnych.

## Lokalizacja

- `shell/domain/<bc>/factories/`
