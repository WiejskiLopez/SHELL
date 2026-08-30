---
name: review-severity-levels
description: Kontrakt klasyfikacji ustaleń code review — poziomy BLOCKER/CRITICAL/HIGH/MEDIUM/LOW/NIT, kryteria przypisania, format raportu i kolejność weryfikacji. Używaj przy każdym code review aplikacji DDD/hexagonalnych w Pythonie — jest składowym modelem dla wszystkich skilli review-*.
---

# Review Severity Levels — kontrakt kode review

> Każde ustalenie z review MUSI otrzymać poziom istotności. Ten skill definiuje skalę
> i kryteria przypisania. Pozostałe skille `review-*` odwołują się do tej skali etykietami
> (BLOCKER/CRITICAL/HIGH/...) — definicje poziomów żyją wyłącznie tutaj.

## 1. Skala istotności

| Poziom | Znaczenie | Przykłady |
|--------|-----------|-----------|
| **BLOCKER** | Uniemożliwia merge — błąd krytyczny skutkujący utratą/kompromitacją danych, naruszeniem bezpieczeństwa albo złamaniem kardynalnej zasady architektonicznej | wyciek sekretów do kodu; złamanie reguły zero-wyjątków (architectural-discipline); utrata kontroli nad invariantami domeny; złamanie kierunku zależności warstw `domain -> infra` |
| **CRITICAL** | Musi być naprawione przed mergem; istotne naruszenie architektury, domeny lub kontraktu | naruszenie granicy Bounded Context; handler nieidempotentny; niezgodność ORM model z migracją; brak walidacji invariantu w metodzie domenowej; naruszenie port-adapter bez ACLa |
| **HIGH** | Istotna wada jakościowa lub ryzykowny wzorzec; naprawa w najbliższym cyklu (ticket priorytetowy) | brak testów krytycznej logiki; N+1 w gorącej ścieżce; brak walidacji wejścia na granicy API; obsługa błędów przez połykanie wyjątków |
| **MEDIUM** | Zalecenie; refaktoryzacja lub poprawa struktury bez wpływu na działanie | zduplikowana logika; ustawienie lifecycle DI przedyskutowane; brak precyzji typów w prywatnej metodzie |
| **LOW** | Drobiazg; kosmetyka architektoniczna, porządek | nazewnictwo zmiennych lokalnych; kolejność pól w dataclass |
| **NIT** | Czysta opinia/styl; zero wpływu, można ignorować | sugestia innego formatowania; preferencja stylistyczna |

## 2. Kryteria przypisania

Przy każdym ustaleniu odpowiedz na pytania w tej kolejności:

1. **Czy to zagraża danym, bezpieczeństwu lub stabilności produkcji?** → BLOCKER / CRITICAL.
2. **Czy łamie kardynalną zasadę zero-wyjątków albo regułę, która ma status "zero wyjątków"?** → CRITICAL (BLOCKER jeśli uruchamia ścieżkę degradacji danych).
3. **Czy narusza strukturę warstw, granicę BC albo kontrakt integracyjny?** → CRITICAL.
4. **Czy to błąd funkcjonalny/ryzykowny wzorzec który przejdzie do produkcji?** → HIGH.
5. **Czy to problemem jakości/utrzymania bez wpływu na działanie?** → MEDIUM / LOW.
6. **Czy to wyłącznie kwestia gustu?** → NIT.

Nie zawyżaj ani nie zaniżaj: kosmetyka nigdy nie jest HIGH, a naruszenie invarianta
biznesowego nigdy nie jest LOW.

## 3. Format raportu

Każde ustalenie raportuj zwięźle i jednoznacznie:

```
[SEVERITY] (file:line) — co dokładnie jest nie tak
- Reguła: <nazwa reguły lub nazwa skill-a, np. review-domain-layer / aggregate-structure>
- Dlaczego: <obiektywne uzasadnienie wpływu>
- Proponowana poprawka: <konkretna zmiana, ewentualnie szkic kodu>
```

Przykład:

```
[CRITICAL] (shell/application/project/project/command_handlers/create_project_handler.py:41)
- Reguła: review-application-layer / handler bez logiki biznesowej
- Dlaczego: handler wykonuje kalkulację ceny (logika domenowa) zamiast delegować do agregatu
- Proponowana poprawka: przenieść kalkulację do metody agregatu i wywołać ją z handlera
```

## 4. Kolejność weryfikacji

Weryfikuj wg top-down, by błędy strukturalne nie maskowały detali:

1. Architektura i zależności (review-dependency-architecture)
2. Warstwa domenowa (review-domain-layer)
3. Warstwa aplikacji (review-application-layer)
4. Kontrakty API (review-api-contracts)
5. Persystencja i migracje (review-persistence-and-migrations)
6. DI / Composition Root (review-dependency-injection)
7. Integracja zdarzeniowa (review-event-driven-integration)
8. Obsługa błędów i logowanie (review-error-handling-and-logging)
9. Bezpieczeństwo (review-security)
10. Współbieżność i spójność (review-concurrency-and-consistency)
11. Wydajność (review-performance)
12. Jakość kodu (review-python-code-quality)
13. Testy i CI (review-testing-and-ci)

## 5. Zasady końcowe

- **Jeden finding = jeden temat.** Nie łącz niezwiązanych uwag w jedno ustalenie.
- **Uzasadniaj obiektywnie.** Odwołuj się do reguły/konsekwencji, nie do gustu.
- **Proponuj naprawę.** Review bez propozycji to tylko lista skarg.
- **Nie eskaluj bez potrzeby.** Jeśli masz wątpliwości między dwoma poziomami — wybierz niższy,
  ale zawsze oznacz "decyzja wymaga potwierdzenia", gdy dotyczy BLOCKER/CRITICAL.