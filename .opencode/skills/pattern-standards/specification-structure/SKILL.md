---
name: specification-structure
description: Reguły struktury klasy Specification — dziedziczenie po Specification[T], is_satisfied_by, kompozycja AND/OR/NOT, filtrowanie w repozytoriach.
---

# Specification Structure

> Reguły struktury klasy Specification we wszystkich bounded contextach.

## Definicja

- Specification to komponowalny predykat biznesowy — hermetyzuje pojedynczą regułę biznesową w osobnej klasie.
- Pozwala na: wielokrotne użycie reguł biznesowych; kompozycję reguł (AND, OR, NOT); filtrowanie w repozytoriach (specification → SQL WHERE); walidację obiektów domenowych.

## Klasa

- Dziedziczy po `Specification[T]` z platformy.
- Implementuje `is_satisfied_by(candidate: T) -> bool`.
- Hermetyzuje JEDNĄ regułę biznesową.

```python
class ActiveWorkflowSpecification(Specification[Workflow]):
    def is_satisfied_by(self, candidate: Workflow) -> bool:
        return candidate.status in (WorkflowStatus.RUNNING, WorkflowStatus.PAUSED)
```

## Kompozycja

- Komponowalna przez `&`, `|`, `~` (AND, OR, NOT).

```python
specification = ActiveWorkflowSpecification() & OwnerSpecification(owner_id)
active_workflows = await repository.list_by(specification)
```

## Parametry

- Specification może przyjmować parametry przez konstruktor dla konfigurowalnych reguł.

```python
class OwnerSpecification(Specification[Workflow]):
    def __init__(self, owner_id: UserId) -> None:
        self._owner_id = owner_id

    def is_satisfied_by(self, candidate: Workflow) -> bool:
        return candidate.owner_id == self._owner_id
```

## Zastosowania

- Walidacja obiektów domenowych.
- Filtrowanie w repozytoriach (specification → SQL WHERE).
- Reużywalne reguły biznesowe.

## Lokalizacja

- `shell/domain/<bc>/specifications/`
- Klasa bazowa: `shell/domain/platform/base/specification.py`

## Bezpieczeństwo

- Specyfikacja korzysta z czystych typow domenowych.
- Testowana w isolation (unit test).
