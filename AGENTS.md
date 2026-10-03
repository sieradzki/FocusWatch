# FocusWatch — wskazówki dla agenta

Repo zawiera starszą aplikację Python/PySide6 oraz badania przed nową implementacją. **Nowy rdzeń nie został jeszcze zbudowany.** Nie potrzebujesz historii czatu, żeby kontynuować.

## Przeczytaj na początku

1. [Przekazanie pracy](docs/HANDOFF.md) — stan repo, wykonane sprawdzenia i następny krok.
2. [Brief produktu](docs/PROJECT_BRIEF.md) — wymagania i intencje użytkownika.
3. [Rejestr decyzji](docs/architecture/DECISIONS.md) — wymagania, rekomendacje i otwarte decyzje.
4. [Aktualizacja rekomendacji z 03.10.2026](docs/architecture/REBUILD_BASELINE_2026-10-03.md) — płatny produkt, kryteria doboru technologii i architektura referencyjna.
5. [Plan implementacji](docs/IMPLEMENTATION_PLAN.md) oraz [odbiór prototypu](docs/architecture/PROTOTYPE_ACCEPTANCE.md).
6. [Badanie z września](docs/research/2026-09/README.md) — historyczne wyniki, uzasadnienia i granice dowodów.

Najnowsze polecenie użytkownika ma pierwszeństwo. Nie uznawaj rekomendacji z raportu za zatwierdzony przez użytkownika stos. Aktualizuj rejestr, gdy decyzja faktycznie zapadnie; nie wymagaj osobnej zgody na każdą rutynową czynność w już zleconym zakresie.

## Zasady projektu

- Docelowo **płatny** companion osobisty B2C, nie narzędzie kontroli pracowników. Pierwszym użytkownikiem jest właściciel projektu. Płatność nie rozstrzyga ceny, subskrypcji, licencji jednorazowej ani okresu próbnego.
- **Nie premiuj technologii ze względu na znajomość przez właściciela.** Rozwój ma uwzględniać agentów AI. Oceniaj produkt, testowalność, bezpieczeństwo, dystrybucję i utrzymanie; nie zakładaj bez dowodu, że agenci bezbłędnie obsługują każdy stos.
- Zachowuj niezależne obserwacje z wielu urządzeń i źródeł; foreground, odtwarzanie, obecność i uwaga nie są tym samym. Unia wszystkich obserwacji nie jest automatycznie czasem aktywności człowieka.
- Pomiar, interpretacja, intencja, hipoteza profilu, ręczna korekta i polityka działania mają osobną semantykę. Korekta nie znika przy przeliczeniu reguł.
- Podstawowe pomiary, raporty i reguły działają bez LLM i bez ciągłej dostępności chmury. Nie oznacza to obowiązkowej darmowej wersji produktu.
- Pełny rewrite jest dopuszczalny. Nie narzucaj kompatybilności, migracji ani feature parity starej aplikacji. To nie upoważnia do usuwania osobistych danych.
- Cloudflare był przykładem, nie preferencją użytkownika. Rize i ActivityWatch nie wyznaczają granic researchu.
- Granica prywatności chmury jest otwarta. Rekomendowane E2EE nie jest zaakceptowaną obietnicą produktu. Kosztorys nie upoważnia do uploadu historii ani tworzenia płatnych zasobów.

## Praca i dowody

- Zaczynaj od `git status --short --branch` i `python3 scripts/verify_handoff.py` (Python 3.10+; standard library). To sprawdza pakiet przekazania, nie poprawność aplikacji. Brak checkout lub testowanego OS odnotuj; nie zastępuj go deklaracją powodzenia.
- Kod w `focuswatch/`, `test/`, `requirements.txt` i `focuswatch.spec` należy do starej implementacji. `docs/feature-task-scheduling.md` i `docs/review-projects-readiness.md` są historyczne.
- `scripts/research/` to izolowane eksperymenty, nie biblioteka produktu. Przed odtwarzaniem przeczytaj [instrukcję badań](scripts/research/README.md). Nie uruchamiaj kosztownych prób tylko po to, by poznać repo.
- Zachowuj badanie `2026-09` jako punkt odniesienia. Nowe wyniki zapisuj osobno z metodą, wersjami i ograniczeniami. Nie porównuj języków na podstawie różnych schematów SQL albo różnych strategii dostępu do OS.
- Przy testach starej aplikacji używaj izolowanej konfiguracji i bazy. Start watchera może zbierać rzeczywistą aktywność; uruchomienie GUI nie jest neutralnym testem odczytowym.
- Po istotnym etapie uzupełnij HANDOFF, plan i rejestr decyzji. Zapisz zakres, wykonane komendy, wyniki, ograniczenia i konkretny następny krok. Nie zapisuj ustaleń wyłącznie w czacie.
