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
- Nie istnieje samodzielnie — zawsze jest wewnątrz agregatu
- Modyfikowana wyłącznie przez metody Aggregate Root
- Może mieć własne Value Object ID

## 3. Encje Nie Mają Własnych Repozytoriów

Tylko Aggregate Root ma repozytorium. Child entities są zapisywane i odczytywane wyłącznie przez repozytorium agregatu (jako część grafu obiektów). Jeśli child entity wymaga osobnego repozytorium — to znak, że powinna być osobnym agregatem.

## 4. Encje Nie Zawierają Logiki Infrastrukturalnej

Encje to czysty kod domenowy:
- Brak importów ORM (SQLAlchemy itp.)
- Brak adnotacji serializacyjnych
- Brak zależności od `shell.infrastructure.*`

## ⚠️ 5. Primitive Obsession — w encji tylko ValueObjecty

Encja (zarówno Aggregate Root jak i child entity) NIGDY nie używa typów prostych do przechowywania stanu.

ZABRONIONE:
```python
# child entity z typami prostymi — ZŁO
class WorkflowSkill(Entity[WorkflowSkillId]):
    _name: str              # ZŁO: str zamiast SkillName
    _config: dict           # ZŁO: dict zamiast SkillConfig
    _enabled: bool          # ZŁO: bool zamiast SkillStatus
```

DOZWOLONE:
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
- [ ] Brak zależności od ORM / infrastruktury
- [ ] Nie ma własnego repozytorium (chyba że to Aggregate Root)
