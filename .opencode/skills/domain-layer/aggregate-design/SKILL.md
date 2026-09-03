---
name: aggregate-design
description: "Zasady projektowania agregatów DDD — wyznaczanie granic, enkapsulacja stanu, referencje przez ID, Primitive Obsession, minimalna transakcja. Używaj gdy modelujesz nowy agregat, refaktoryzujesz istniejący, dzielisz za duży agregat, albo nie jesteś pewien gdzie postawić granicę transakcyjną."
---

# Projektowanie agregatów DDD

Agregat to podstawowa jednostka konsystencji transakcyjnej w DDD. Każdy agregat ma jeden Aggregate Root — encję przez którą odbywa się cały dostęp do agregatu z zewnątrz.

## Pięć zasad Vaughna Vernona

Każdy projekt agregatu weryfikuj przez te pięć pytań:

### 1. Czy agregat jest wystarczająco mały?

Agregat zawiera dokładnie tyle encji/VO, ile potrzeba do zachowania invariantów biznesowych w jednej transakcji; granicę wyznacza wymóg spójności, a pełny graf obiektów pozostaje rozproszony między agregatami.

Sygnały że agregat jest za duży:
- Pojedynczy zapis dotyka wielu kolekcji wewnątrz agregatu
- Różne przypadki użycia modyfikują kompletnie różne części tego samego agregatu
- Dwie encje wewnątrz agregatu są zawsze modyfikowane w różnych transakcjach
- Zapis agregatu trwa długo (dużo danych), bo ładujesz rzeczy niepotrzebne do bieżącej operacji

### 2. Czy zachowuję invariants natychmiastowo?

Invariant to reguła biznesowa która MUSI być spełniona zawsze, bez żadnego okna czasowego. Jeśli dwie encje muszą być spójne natychmiast (w tej samej transakcji) — są w tym samym agregacie. Jeśli mogą być spójne ostatecznie (eventual consistency) — są w różnych agregatach.

### 3. Referencje miedzy agregatami sa przez ID

Agregat A przechowuje referencje do agregatu B poprzez `B_id`. Relacje miedzy agregatami nawiguje repository.

### 4. Primitive Obsession — w agregacie tylko ValueObjecty

Agregat przechowuje stan w Value Objectach, encjach, identyfikatorach domenowych i kolekcjach tych typow.

ANTYWZORZEC:
```python
class GraphExecution(AggregateRoot[GraphExecutionId]):
    _status: str                    # Antywzorzec
    _state_input: dict              # Antywzorzec
    _skills: list                   # Antywzorzec
    _correlation_id: str            # Antywzorzec
```

POPRAWNIE:
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

### 5. Czy rozmiar transakcji jest minimalny?

Pojedyncza transakcja modyfikuje DOKŁADNIE JEDEN agregat. Jeśli musisz zapisać dwa agregaty w jednej operacji — użyj eventual consistency: pierwszy agregat zapisuje się i emituje event, drugi subskrybuje ten event i zapisuje się w osobnej transakcji.

Dwa nowe (tworzone) agregaty mogą znaleźć się w jednej transakcji przy braku współbieżnych
modyfikacji; taki układ zwykle wskazuje, że granice powinny przebiegać przez jeden agregat.

## Kiedy czytasz references

- Wyznaczasz granice nowego agregatu → `references/aggregate-heuristics.md`
- Debugujesz problem z konsystencją, wydajnością albo blokadami → `references/aggregate-anti-patterns.md`
