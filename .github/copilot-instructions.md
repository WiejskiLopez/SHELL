# SHELL — instrukcje repozytorium dla Copilota

## Zakres i źródła prawdy

Te instrukcje opisują wyłącznie stałe granice repozytorium. Szczegółowe zasady projektowania i implementacji znajdują się w skillach.

- Kod produkcyjny i testy w `shell/` są źródłem prawdy o aktualnym zachowaniu systemu.
- Testy architektury w `shell/tests/architecture/` są źródłem prawdy o egzekwowanych ograniczeniach.
- Szczegółowe reguły implementacyjne czytaj z `.opencode/skills/` przez adapter `.github/skills/shell-architecture/SKILL.md`.
- Nie twórz nowych plików produkcyjnych poza `shell/`, chyba że zadanie dotyczy konfiguracji repozytorium lub dokumentacji.

## Aktualna topologia

`SHELL` jest systemem podzielonym na bounded contexts, ze wspólną warstwą platformową. Główna struktura aplikacji to:

- `shell/domain/` — reguły domenowe, agregaty, encje, value objects i zdarzenia;
- `shell/application/` — przypadki użycia, handlery, porty, DTO i mapowanie;
- `shell/process/` — orkiestracja wieloagregatowa, process managery i sagi;
- `shell/infrastructure/` — implementacje portów, persistence i adaptery techniczne;
- `shell/framework/` — wejścia HTTP, CLI i adaptery driving-side;
- `shell/<bc>/bootstrap/` — composition root należący do konkretnego BC;
- `shell/platform/` — współdzielone prymitywy techniczne i kontrakty platformowe;
- `shell/config/` — konfiguracja środowiskowa;
- `shell/tests/` — testy jednostkowe, integracyjne, E2E i architektoniczne.

Kierunek zależności kontrolowany przez testy architektury:

```text
domain <- application <- process <- infrastructure <- framework <- <bc>/bootstrap
```

`platform/` jest współdzieloną warstwą bazową. Granice bounded contexts są izolowane; importy między kontekstami przechodzą przez dozwolone kontrakty platformowe lub integracyjne.

## Nienaruszalne guardraile

- Nie importuj zależności z warstwy zewnętrznej do wewnętrznej wbrew regułom testów architektury.
- Domena nie może zależeć od frameworków, infrastruktury ani I/O.
- Handlery aplikacyjne komunikują się ze światem zewnętrznym przez porty, a adaptery są składane w bootstrapie.
- Orkiestracja wielu agregatów należy do `process/`; pojedynczy handler aplikacyjny nie powinien przejmować tej odpowiedzialności.
- Zmiany w modelach persistence, kontraktach portów, eventach lub wejściach systemu wymagają odpowiednich testów i aktualizacji wszystkich powiązanych adapterów.
- Nie dodawaj wyjątków, `noqa` ani obejść wyciszających aktywne reguły bez wyraźnego uzasadnienia i zgodności z istniejącymi testami.
- Nie zakładaj, że aspiracyjne lub niezaimplementowane wzorce ze skillów są częścią bieżącego systemu.

## Routing do skillów

Przed zmianą kodu wybierz właściwy skill przez `.github/skills/shell-architecture/SKILL.md`. Nie kopiuj jego szczegółowych reguł do tego pliku.

Jeśli skill i kod/testy są sprzeczne, najpierw zweryfikuj stan testami i traktuj kod oraz egzekwowane testy jako źródło prawdy. Zgłoś rozbieżność zamiast utrwalać niepotwierdzone założenie.

## Minimalna walidacja

Dobierz węższy test do zmienionego obszaru, a przed zakończeniem uruchom odpowiedni zestaw architektoniczny. Standardowy punkt kontrolny repozytorium to:

```powershell
pytest shell/tests/architecture -x
```

Dla zmian wpływających na cały projekt użyj także lokalnego pipeline'u wdrożeniowego `.\deploy.ps1`. Skrypt wykonuje formatowanie oraz pełny `run_tests.ps1` (testy, lint, typowanie, granice architektury i audyty bezpieczeństwa), a następnie generuje OpenAPI, buduje obraz i restartuje kontenery. Ponieważ wykonuje także `git commit`, uruchamiaj go wyłącznie jako jawnie wybrany końcowy krok po zmianach.
