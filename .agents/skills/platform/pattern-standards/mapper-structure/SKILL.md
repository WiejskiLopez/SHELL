# Mapper Structure

> Reguły struktury klasy Mapper we wszystkich bounded contextach.

## Definicja

- Mapper odpowiada za konwersję między warstwami architektury:
  - Domain → ORM Model (zapis do bazy)
  - ORM Model → Domain (odczyt z bazy)
  - Domain → DTO (output dla klienta)
  - Command/DTO → Domain (input od klienta)

## Symetryczność

- Mapper musi być symetryczny: `to_domain(to_model(domain)) == domain` dla wszystkich pól.
- Round-trip test — obowiązkowy dla każdego mappera.

```python
class WorkflowMapper:
    def to_model(self, domain: Workflow) -> WorkflowModel:
        return WorkflowModel(
            id=domain.id.value,
            name=domain.name.value,
            status=domain.status.value,
            version=domain.version,
        )

    def to_domain(self, model: WorkflowModel) -> Workflow:
        return Workflow.restore(
            workflow_id=WorkflowId(model.id),
            name=WorkflowName(model.name),
            status=Status(model.status),
            version=model.version,
        )
```

## Brak logiki biznesowej

- Mapper nie zawiera logiki biznesowej — tylko mapowanie pól.
- Transformacje typów (UUID ↔ str, datetime ↔ str) są dozwolone.
- Reguły biznesowe, walidacja, kalkulacje — nie w mapperze.

## Graf obiektów

- Gdy agregat zawiera encje dziecięce, mapper mapuje cały graf obiektów.

```python
def to_model(self, domain: Workflow) -> WorkflowModel:
    return WorkflowModel(
        id=domain.id.value,
        name=domain.name.value,
        nodes=[NodeModel(id=n.id.value, name=n.name.value) for n in domain.nodes],
    )

def to_domain(self, model: WorkflowModel) -> Workflow:
    nodes = [Node.restore(NodeId(n.id), NodeName(n.name)) for n in model.nodes]
    return Workflow.restore(WorkflowId(model.id), WorkflowName(model.name), nodes)
```

## restore()

- Mapper używa `restore()` na agregacie do odczytu — pomija walidację biznesową (dane z bazy są spójne).

## Lokalizacja

- ORM: `shell/infrastructure/<bc>/mappers/<aggregate>_mapper.py`
- DTO: `shell/application/<bc>/mappers/<aggregate>_dto_mapper.py`
- Command: `shell/application/<bc>/mappers/<command>_mapper.py`
