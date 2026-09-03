---
name: factory
description: Wzorzec Factory w DDD — odpowiedzialność tworzenia złożonych agregatów, rekonstrukcja z persistance, factory methods na VO/Entity, AggregateFactory. Używaj gdy tworzenie agregatu wymaga skomplikowanej logiki, rekonstruujesz obiekt z bazy, albo potrzebujesz scentralizować logikę tworzenia.
---

# Factory Pattern w Enterprise DDD

## Wzorzec SHELL — factory methods na agregacie

W SHELL agregat nie ma osobnych klas w katalogu `factories/`. Tworzenie i rekonstrukcja odbywają się przez **factory methods (classmethod) na samej klasie agregatu**:

- `_new(*, ...)` — prywatna; buduje nowy agregat i emituje event utworzenia (`append_event`).
- `create(*, ...)` — publiczna; deleguje do `_new`, przyjmuje domenowy `CreatedAt` i typy domenowe.
- `restore(*, ...)` — publiczna; rekonstruuje agregat z persystencji **bez emisji eventów** i bez zmiany stanu.

```python
class User(AggregateRoot[UserId]):
    @classmethod
    def _new(cls, *, id: UserId, now: OccurredAt, email: UserEmail) -> Self:
        user = cls(
            id=id,
            email=email,
            status=UserStatus.ACTIVE,
            created_at=CreatedAt.from_datetime(now.value),
        )
        user.append_event(UserCreatedEvent.now(user_id=id, now=now))
        return user

    @classmethod
    def create(cls, *, id: UserId, now: CreatedAt, email: UserEmail) -> User:
        return cls._new(id=id, email=email, now=OccurredAt.from_datetime(now.value))

    @classmethod
    def restore(
        cls,
        *,
        id: UserId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        email: UserEmail,
        status: UserStatus,
    ) -> Self:
        return cls(
            id=id,
            email=email,
            status=status,
            created_at=created_at,
            changed_at=changed_at,
            deleted_at=deleted_at,
        )
```

## Reguły

- **`create` vs `restore`:** `create` emituje event utworzenia; `restore` **nigdy nie emituje eventów** i nigdy nie zmienia stanu (dotyka identycznych pól co mapper).
- `create` i `restore` przyjmują **wyłącznie typy domenowe** (VO, ID) — zero typów prostych (Primitive Obsession).
- Zgodnie z arch-testami: każdy agregat ma `restore` (`test_enterprise_patterns__test_all_aggregates_have_restore`) oraz wewnętrzne, prywatne `_new` (`test_aggregate_scaffold__test_aggregates_have_private_new`).
- Factory dla encji/VO może być factory method na encji (`@classmethod`) — ten sam wzorzec `now`/`from_*`.

## Factory a Mapper — Różnice

| Aspekt | Factory (`create`/`_new`) | Mapper / `restore` |
|--------|---------------------------|--------------------|
| Odpowiedzialność | Tworzy **nowe** obiekty | Konwertuje między warstwami / rekonstruuje z bazy |
| Walidacja | Tak (biznesowa) | Nie (zakłada że dane są poprawne) |
| Emisja eventów | `_new`/`create` — tak | `restore` — **nigdy** |
| Używane w | Handlerach, Domain Services | Repozytoriach / mapperach ORM |
| Źródło danych | Komendy, eventy, dane wejściowe | Modele ORM |
| Output | Agregaty, encje, VO | Agregaty (stan odtworzony) |

## Podsumowanie — Checklista

Tworząc agregat:
- [ ] `_new` prywatne, emituje event utworzenia
- [ ] `create` publiczne, deleguje do `_new`
- [ ] `restore` publiczne, bez eventów, pełny stan
- [ ] Tylko typy domenowe w sygnaturach
- [ ] Testy jednostkowe dla każdej ścieżki tworzenia
- [ ] Lokalizacja: metody na klasie agregatu (`shell/<service>/domain/<bc>/aggregates/<agregat>/<agregat>.py`) — bez katalogu `factories/`