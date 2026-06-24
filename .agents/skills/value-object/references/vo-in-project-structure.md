# VO w strukturze projektu

> Wyciągnięte z `aggregate-design/SKILL.md` — struktura folderów agregatu.

## Struktura folderów agregatu

W folderze agregatu znajduje się **wyłącznie** plik agregatu (klasa dziedzicząca po `AggregateRoot`).
Wszystkie value objects (w tym ID) należą do podfolderu `value_objects/` wewnątrz agregatu:

```
aggregates/my_aggregate/
    __init__.py
    my_aggregate.py                          # tylko agregat
    value_objects/
        __init__.py
        my_aggregate_id.py                   # ID jako VO
        my_aggregate_skill_id.py             # inne VO
        child_entity_id.py
```

Importy wewnątrz agregatu zawsze wskazują na `value_objects`:

```python
# my_aggregate.py
from .value_objects.my_aggregate_id import MyAggregateId
from .value_objects.my_aggregate_skill_id import MyAggregateSkillId
```

Wszystkie value objects są wprost w `value_objects/` — bez dodatkowych podfolderów.
