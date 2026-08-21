---
name: aggregate-design
description: Zasady projektowania agregatów DDD — wyznaczanie granic, enkapsulacja stanu, referencje przez ID, optymistyczne blokowanie, maszyny stanów. Używaj gdy modelujesz nowy agregat, refaktoryzujesz istniejący, dzielisz za duży agregat, albo nie jesteś pewien gdzie postawić granicę transakcyjną.
---

# Projektowanie agregatów DDD

Agregat to podstawowa jednostka konsystencji transakcyjnej w DDD. Każdy agregat ma jeden Aggregate Root — encję przez którą odbywa się cały dostęp do agregatu z zewnątrz.

## Cztery zasady Vaughna Vernona

Każdy projekt agregatu weryfikuj przez te cztery pytania:

### 1. Czy agregat jest wystarczająco mały?

Agregat zawiera dokładnie tyle encji/VO, ile potrzeba do zachowania invariantów biznesowych w jednej transakcji. Nie ładuj całego grafu obiektów do jednego agregatu "bo będzie wygodniej".

Sygnały że agregat jest za duży:
- Pojedynczy zapis dotyka wielu kolekcji wewnątrz agregatu
- Różne przypadki użycia modyfikują kompletnie różne części tego samego agregatu
- Dwie encje wewnątrz agregatu są zawsze modyfikowane w różnych transakcjach
- Zapis agregatu trwa długo (dużo danych), bo ładujesz rzeczy niepotrzebne do bieżącej operacji

### 2. Czy zachowuję invariants natychmiastowo?

Invariant to reguła biznesowa która MUSI być spełniona zawsze, bez żadnego okna czasowego. Jeśli dwie encje muszą być spójne natychmiast (w tej samej transakcji) — są w tym samym agregacie. Jeśli mogą być spójne ostatecznie (eventual consistency) — są w różnych agregatach.

### 3. Referencje miedzy agregatami sa przez ID

Agregat A przechowuje referencje do agregatu B poprzez `B_id`. Relacje miedzy agregatami nawiguje repository.

### ⚠️ 5. Primitive Obsession — w agregacie tylko ValueObjecty

Agregat przechowuje stan w Value Objectach, encjach, identyfikatorach domenowych i kolekcjach tych typow.

ZABRONIONE:
```python
class GraphExecution(AggregateRoot[GraphExecutionId]):
    _status: str                    # ZŁO
    _state_input: dict              # ZŁO
    _skills: list                   # ZŁO
    _correlation_id: str            # ZŁO
```

DOZWOLONE:
```python
class GraphExecution(AggregateRoot[GraphExecutionId]):
    _status: GraphExecutionStatus   # VO (enum)
    _skills: list[GraphExecutionSkill]  # kolekcja encji
    _node_execution_ids: list[NodeExecutionId]  # kolekcja ID
    _transitions: list[TransitionDefinition]  # kolekcja VO
```

**Zasada**: każde pole agregatu ma typ, który jest albo:
- ValueObject (klasa dziedzicząca po `ValueObject`)
- Entity (klasa dziedzicząca po `Entity`)
- ID (klasa kończąca się na `Id`)
- Kolekcja powyższych (`list[SomeVO]`, `tuple[SomeId]`)
- `datetime` (stdlib, dozwolony dla timestampów)

Test sprawdza to automatycznie — `test_entity_aggregate_fields_have_domain_types`.

### 4. Czy rozmiar transakcji jest minimalny?

Pojedyncza transakcja modyfikuje DOKŁADNIE JEDEN agregat. Jeśli musisz zapisać dwa agregaty w jednej operacji — użyj eventual consistency: pierwszy agregat zapisuje się i emituje event, drugi subskrybuje ten event i zapisuje się w osobnej transakcji.

Wyjątek: dwa agregaty w jednej transakcji są akceptowalne tylko gdy oba są nowe (tworzone) i żaden inny proces nie może ich współbieżnie modyfikować. Ale to sygnał że może powinny być jednym agregatem.

## Kiedy czytasz references

- Wyznaczasz granice nowego agregatu → `references/aggregate-heuristics.md`
- Debugujesz problem z konsystencją, wydajnością albo blokadami → `references/aggregate-anti-patterns.md`
