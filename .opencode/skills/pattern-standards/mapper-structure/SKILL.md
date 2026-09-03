---
name: mapper-structure
description: Reguły struktury Mapper — symetryczność round-trip, mapowanie grafów obiektów, mapowanie pól bez logiki biznesowej.
---

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
            id=WorkflowId(model.id),
            name=WorkflowName(model.name),
            status=Status(model.status),
            version=model.version,
        )
```

## Zakres: mapowanie pól

- Mapper zawiera wyłącznie mapowanie pól; logika biznesowa pozostaje w domenie.
- Transformacje typów (UUID ↔ str, datetime ↔ str) są dozwolone.
- Reguły biznesowe, walidacja i kalkulacje realizowane są w domenie, poza mapperem.

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
    return Workflow.restore(id=WorkflowId(model.id), name=WorkflowName(model.name), nodes=nodes)
```

## restore()

- Mapper używa `restore()` na agregacie do odczytu; walidacja biznesowa pominięta (dane z bazy są spójne).

## Lokalizacja

- ORM: `shell/<service>/infrastructure/<bc>/<aggregate>/persistence/sql/mappers/<aggregate>_mapper.py`
- DTO: `shell/<service>/application/<bc>/<aggregate>/mappers/<aggregate>_dto_mapper.py`
- Command: `shell/<service>/application/<bc>/<aggregate>/mappers/<command>_mapper.py`
