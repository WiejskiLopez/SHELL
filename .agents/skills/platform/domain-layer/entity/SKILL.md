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

## 5. Podsumowanie — Checklista

Podczas dodawania nowej encji:
- [ ] Leży w `entities/` wewnątrz agregatu
- [ ] Brak zależności od ORM / infrastruktury
- [ ] Nie ma własnego repozytorium (chyba że to Aggregate Root)
