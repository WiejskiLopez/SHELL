---
name: enterprise-over-hacks
description: Zasada decyzyjna — przy wyborze między wariantem enterprise a wariantem skrótowym architekt zawsze wybiera wariant enterprise (jawny, deterministyczny, standardowy, czytelny w PR, o niskim zadłużeniu). Używaj przy każdej decyzji architektonicznej, wyborze wzorca/projektu, migracjach, refaktoryzacji i rozstrzyganiu „czy to na pewno nie jest hack".
---

# Enterprise over hacks

## Zasada

Przy każdej decyzji architektonicznej wybieraj rozwiązanie **enterprise** — jawne,
standardowe, deterministyczne i nisko-zadłużone — zamiast sprytnego skrótu, który
obsługuje przypadek dzisiaj, a utrudnia utrzymanie i ewolucję jutro.

## Kryteria rozwiązania enterprise

Rozwiązanie jest enterprise, gdy spełnia większość z tych cech:

1. **Jawność** — decyzja, DDL i semantyka są widoczne w kodzie i w PR (review-able);
   logika nie jest ukryta w runtime-magic ani w nieprzejrzystych konwencjach.
2. **Determinizm** — ten sam artefakt zawsze daje ten sam wynik w czasie; historyczne
   kroki (np. migracje) pozostają zamrożone i niezależne od bieżącego stanu modeli.
3. **Standard** — wzorzec lub narzędzie branżowe wspiera to rozwiązanie (autogenerate
   migracji, Alembic, CQRS, outbox/inbox, DI …); wybór nie wymaga wymyślania własnego koła.
4. **Ewolucja** — zadanie jest odwracalne i powtarzalne (rollback, replay, ponowne zastosowanie);
   zmiany są krokowe i bezpieczne w czasie.
5. **Jedno źródło prawdy + artefakty** — prawda siedzi w modelach domeny, a artefakty
   (migracje, schematy) są z niej generowane i jawne, a nie wyprowadzane w runtime.
6. **Niskie zadłużenie** — brak duplikacji per serwis, braku ukrytego stanu i braku
   „naprawimy później".

## Warianty do porównania

| Wariant | Cechy | Werdykt |
|---|---|---|
| Enterprise | jawny, deterministyczny, standardowy, czytelny w review, odwracalny | wybór |
| Skrótowy | kompaktowy, „magiczny”, runtime-driven, nieprzejrzysty, jednorazowy | odrzucić bez ADR |

„Elegancja" w tym kontekście oznacza przejrzystość i niskie utrzymanie, a nie
zwięzłość kodu kosztem czytelności (np. pomiaru „im mniej widzę w migracji, tym lepiej"
to nie elegancja, to ukryta złożoność).

## Proces decyzyjny

1. Zidentyfikuj oba warianty: enterprise i skrótowy.
2. Oceniaj rozwiązanie przez kryteria z sekcji wyżej.
3. Wybierz **wariant enterprise**.
4. Odejście od wariantu enterprise wymaga **jawnego, udokumentowanego powodu** —
   zapisujemy go jako ADR z przyczyną i zakresem; bez ADR skrót nie zostaje w kodzie.
5. Uproszczenia deweloperskie oznaczaj jako „dev-only" i izoluj od ścieżki produkcyjnej
   (np. `metadata.create_all`/baseline z runtime metadata służy testom i dev, a łańcuchy
   migracyjne produkcji są jawne i zamrożone).

## Przykład zastosowania: migracje

- Modele/tabele platformowe: jedno źródło prawdy w fabrykach platformy (tak zostaje).
- Migracje produkcyjne: **jawne pliki** generowane z modeli (autogenerate), zamrożone
  w `versions/`, review-able, z działającym downgrade — zamiast 0001 czytającego runtime
  metadata w produkcji.
- Baseline z metadata: uprawniony wyłącznie jako narzędzie dev/test (szybka rekreacja bazy),
  wyizolowany od produkcyjnego łańcucha migracji.
- Wspólne zmiany schematu platformy: dostarczane wprost do każdego serwisu (przyrostowe
  migracje albo wspólny katalog `script_location`), a nie przez ukryty runtime.

## Checklista

- [ ] Decyzję/DDL widać w PR i można ją zrecenzować.
- [ ] Wynik jest deterministyczny w czasie (nie zależy od bieżących modeli).
- [ ] Rozwiązanie wspiera standardowe narzędzie/wzorzec branżowy.
- [ ] Istnieje możliwość rollbacku/readvanie.
- [ ] Źródło prawdy jest jedno, a artefakty wygenerowane i jawne.
- [ ] Brak duplikacji per serwis i ukrytego stanu.
- [ ] Jeżeli wybrano wariant spoza enterprise — istnieje ADR z uzasadnieniem.

## Powiązane

- `architectural-discipline` — kardynalne zasady projektu.
- `adr-standard` — zapis świadomych decyzji/odejść.
- `infrastructure-layer/model-migration-sync` — spójność modeli/migracji.
- `meta/skill-authoring` — zasada „treść twierdząca" w skillach.