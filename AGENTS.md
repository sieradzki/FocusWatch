# FocusWatch — wskazówki dla agenta

Repo zawiera starszą aplikację Python/PySide6 oraz badania przed nową implementacją. **Nowy rdzeń nie został jeszcze zbudowany.** Nie potrzebujesz historii czatu, żeby kontynuować.

## Przeczytaj na początku

1. [Przekazanie pracy](docs/HANDOFF.md) — stan repo, co wykonano, jak zacząć na nowej maszynie.
2. [Brief produktu](docs/PROJECT_BRIEF.md) — wymagania i intencje użytkownika.
3. [Rejestr decyzji](docs/architecture/DECISIONS.md) — co jest wymaganiem, rekomendacją lub otwartą decyzją.
4. [Plan implementacji](docs/IMPLEMENTATION_PLAN.md) — następny zakres i kryteria odbioru.
5. [Synteza badań](docs/research/2026-09/README.md) — uzasadnienia i odnośniki do dowodów; czytaj szczegóły stosownie do zadania.

Najnowsze polecenie użytkownika ma pierwszeństwo. Nie uznawaj rekomendacji z raportu za zatwierdzony przez użytkownika stos. Aktualizuj rejestr, gdy decyzja faktycznie zapadnie; nie wymagaj osobnej zgody na każdą rutynową czynność w już zleconym zakresie.

## Zasady projektu

- Docelowo komercyjny companion osobisty, nie narzędzie kontroli pracowników. Pierwszym użytkownikiem jest właściciel projektu.
- Zachowuj niezależne obserwacje z wielu urządzeń i źródeł; foreground, odtwarzanie i uwaga nie są tym samym. Pomiar, interpretacja, intencja oraz ręczna korekta mają osobną semantykę.
- Podstawowe pomiary, raporty i reguły działają bez LLM. Hipotez o osobowości czy produktywności nie zapisuj jako bezspornych faktów.
- Pełny rewrite jest dopuszczalny. Nie narzucaj kompatybilności, migracji ani feature parity starej aplikacji. To nie upoważnia do usuwania osobistych danych.
- Cloudflare był przykładem, nie preferowanym dostawcą; Rize i ActivityWatch były przykładami, nie granicą researchu.
- Granica prywatności chmury jest otwarta. Nie traktuj kosztorysu wariantu z odczytem danych przez serwer jako zgody na upload historii.

## Praca i dowody

- Zaczynaj od `git status --short --branch` i `python3 scripts/verify_handoff.py` (Python 3.10+; sam standard library). To sprawdza pakiet przekazania, nie poprawność aplikacji.
- Kod w `focuswatch/`, `test/`, `requirements.txt` i `focuswatch.spec` należy do starej implementacji. Materiały `docs/feature-task-scheduling.md` i `docs/review-projects-readiness.md` są historyczne.
- `scripts/research/` to izolowane eksperymenty, nie biblioteka nowego produktu. Przed odtwarzaniem przeczytaj [instrukcję badań](scripts/research/README.md). Nie uruchamiaj wszystkich kosztownych prób tylko po to, by poznać repo.
- Zachowuj wyniki badania z 2026-09 jako historyczny punkt odniesienia. Nowe pomiary zapisuj oddzielnie z metodą, wersjami i ograniczeniami; nie usuwaj granic dowodów.
- Przy testach starej aplikacji używaj izolowanej konfiguracji i bazy. Uruchomienie watchera może zbierać rzeczywistą aktywność; sam start GUI nie jest neutralnym testem odczytowym.
- Po istotnym etapie uzupełnij HANDOFF, plan oraz rejestr decyzji. Zapisz zakres zmian, wykonane komendy i ich wynik, ograniczenia oraz konkretny następny krok, żeby kolejny agent nie musiał rekonstruować rozmowy.
