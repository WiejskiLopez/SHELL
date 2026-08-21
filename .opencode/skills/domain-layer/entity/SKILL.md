---
name: entity
description: Zasady projektowania encji DDD — identity-based equality, enkapsulacja stanu, child entities wewnątrz agregatu, lokalizacja w entities/child_entity.py, enum dla stanów.
---

# Encje w Enterprise DDD

## 1. Tożsamość — Fundament Encji

Encja jest jedynym typem domenowym, który ma **tożsamość**. Dwie encje z tym samym ID są tym samym obiektem biznesowym, niezależnie od różnic w pozostałych polach.

## 2. Child Entity vs Aggregate Root

Child entity:
- Ma lokalną tożsamość (ID) — ale tylko w kontekście rodzica
- Child entity zyje wewnatrz agregatu i korzysta z jego lifecycle.
- Modyfikowana wyłącznie przez metody Aggregate Root
- Może mieć własne Value Object ID

## 3. Repozytorium Encji

Aggregate Root posiada repozytorium. Child entities sa zapisywane i odczytywane przez repozytorium agregatu jako czesc grafu obiektow. Osobne repozytorium child entity wskazuje granice osobnego agregatu.

## 4. Czysta Logika Encji

Encje zawieraja czysty kod domenowy. Ich implementacja korzysta z domenowych typow i zachowan.

## ⚠️ 5. Primitive Obsession — w encji tylko ValueObjecty

Encja przechowuje stan w Value Objectach, Entity, identyfikatorach domenowych i kolekcjach tych typow.

Przyklad stanu prymitywnego:
```python
# child entity z typami prostymi — ZŁO
class WorkflowSkill(Entity[WorkflowSkillId]):
    _name: str              # ZŁO: str zamiast SkillName
    _config: dict           # ZŁO: dict zamiast SkillConfig
    _enabled: bool          # ZŁO: bool zamiast SkillStatus
```

Przyklad stanu domenowego:
```python
# child entity z ValueObjectami — DOBRZE
class WorkflowSkill(Entity[WorkflowSkillId]):
    _workflow_id: WorkflowId           # ID innego agregatu
    _payload: SkillPayload             # ValueObject
    _created_at: datetime              # stdlib — dozwolony
```

**Zasada**: `bool`, `str`, `int`, `float`, `bytes`, `dict`, `list`, `set` są ZABRONIONE jako typy pól. Każde z nich musi być opakowane w ValueObject z nazwą adekwatną do domeny.

Test weryfikujący: `test_entity_aggregate_fields_have_domain_types`.

## 6. Podsumowanie — Checklista

Podczas dodawania nowej encji:
- [ ] Leży w `entities/` wewnątrz agregatu
- [ ] Czysty kod domenowy korzystajacy z Value Objectow i encji
- [ ] Repozytorium nalezy do Aggregate Root
