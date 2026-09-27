# Przekazanie FocusWatch na kolejny komputer

Stan: 27.09.2026. Dokument jest punktem startowym dla agenta **bez historii rozmowy**. Ostatnie zlecenie: skonsolidować ustalenia, raporty i repo do dalszej pracy; nie rozpoczynać jeszcze nowej implementacji.

## Co jest w repo

- `focuswatch/`, `test/`, `requirements.txt`, `focuswatch.spec`: starsza aplikacja Python/PySide6, wraz z naprawami modeli/migracji i modułem Projects. Nie jest to proponowany nowy rdzeń.
- `docs/research/2026-09/`: zakończone badanie obecnego kodu, 11 produktów, desktopu, adapterów, backendów, danych i chmur; raporty oraz wyniki JSON.
- `scripts/research/`: źródła eksperymentów, generator danych, kalkulator kosztów oraz lockfile; nie produkcyjny kod aplikacji.
- [Brief](PROJECT_BRIEF.md), [rejestr decyzji](architecture/DECISIONS.md), [plan](IMPLEMENTATION_PLAN.md): aktualny kontekst pracy. Technologie z raportu są rekomendacjami, nie automatycznie przyjętymi wymaganiami.

**Nie zbudowano** nowego agenta/GUI/API produkcyjnego, synchronizacji ani infrastruktury. Nie przeprowadzono pełnych testów Windows, GPU, podpisanych instalatorów, inferencji i rekomendacji AI. Nie wdrażano usług chmurowych.

## Stan Git i pobranie

Gałąź przekazania: **`codex/architecture-evaluation`**, repo `https://github.com/sieradzki/FocusWatch`.

Punkt wyjściowy starszego kodu: **`dc251ba1b02e108f61d97e382991e7f7223495aa`**. Obejmuje zachowanie prac Projects (`00101b8`) i naprawy modeli/migracji (`dc251ba`). Lokalny `main` został wcześniej doprowadzony do tego punktu. W chwili przygotowania przekazania `origin/main` był starszy (`09120c1`); **nie zakładaj, że zwykłe pobranie domyślnego brancha zawiera pakiet**. Gałąź przekazania zawiera potrzebną historię i dokumentację. Nie trzeba ponownie scalać Projects, aby kontynuować z tej gałęzi.

Nowy checkout:

```sh
git clone --branch codex/architecture-evaluation https://github.com/sieradzki/FocusWatch.git
cd FocusWatch
git status --short --branch
git log -3 --oneline
python3 scripts/verify_handoff.py
```

W istniejącym checkout najpierw sprawdź lokalne zmiany, następnie `git fetch origin` i przełącz się na gałąź przekazania. Jeśli nie ma jeszcze lokalnego brancha: `git switch --track origin/codex/architecture-evaluation`. Nie resetuj ani nie nadpisuj lokalnej pracy. Na Windows użyj dostępnego launchera Python 3.10+ zamiast `python3`, np. `py -3`.

Skrypt weryfikuje spójność pakietu, hashe źródeł pomiarów, zapisane wyniki, lokalne linki i odtwarzalność kalkulatora. Nie instaluje zależności, nie uruchamia watchera ani benchmarków. Jego powodzenie nie oznacza, że nowa aplikacja została zaimplementowana.

## Kolejność poznania projektu

1. Przeczytaj [AGENTS.md](../AGENTS.md) i [PROJECT_BRIEF.md](PROJECT_BRIEF.md). To zabezpiecza przed pomyleniem wymagań z dawnymi założeniami.
2. Przeczytaj [DECISIONS.md](architecture/DECISIONS.md) i [syntezę badań](research/2026-09/README.md). Szczegółowe raporty otwieraj przy właściwym obszarze pracy.
3. Sprawdź [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) i bieżące polecenie użytkownika. Przy zleceniu rozpoczęcia implementacji najbliższy zakres to kontrakt danych oraz lokalny przekrój pomiar → agregacja → raport → korekta.
4. Ustal dostępne środowisko OS/toolchain. Nie zakładaj istnienia lokalnego venv, cache, bazy lub dostępu do chmury z poprzedniej maszyny. Nie odtwarzaj ciężkich pomiarów bez powodu.

## Najważniejsze ustalenia do zachowania

- Pełny rewrite jest dopuszczalny i rekomendowany przez badanie. Nie ma wymogu utrzymania starego UI, kompatybilności, migracji ani Kanbana. Nowa implementacja w tym samym Git zachowuje historię bez narzucania starego modelu.
- Pomiar obejmuje równoległe źródła; czas osoby, czas urządzeń i uwaga to różne pojęcia. Interpretacje i korekty nie są surową obserwacją.
- Pierwsza użyteczna wersja działa bez AI. Docelowe cele, preferencje, profil i planowanie są częścią wizji, ale onboarding nie wymaga deklaracji kierunku życiowego.
- E2EE/odczyt chmurowy i wybór inferencji pozostają otwarte. Nie blokują modelu i raportów lokalnych; wpływają na sync, klucze i miejsce analityki.
- Cloudflare nie jest preferencją użytkownika. Porównanie rynku nie ogranicza się do Rize i ActivityWatch.

## Stan dowodów

| Obszar | Co wykonano | Czego nie dowodzi |
| --- | --- | --- |
| Starszy kod | Poprzedni review: 68/68 testów w opisanym środowisku, naprawy modeli/migracji | Obecna gotowość produkcyjna, działanie wszystkich trackerów i nowy produkt |
| Dane | SQLite/DuckDB: 1 mln i 10 mln; PostgreSQL: 1 mln i 200 trwałych batchy po 8 obserwacji | Pojemność chmury wielu kont, przewaga języków API |
| Semantyka/lifecycle | 10/10 scenariuszy czasu/outbox/retry oraz 10/10 syntetycznych sprawdzeń procesów/framing | Kompletny produkcyjny sync, Windows, utrata zasilania |
| UI | 18 prób Tauri/Electron/Qt Quick, 1000 i 10000 segmentów | Pełny dashboard, GPU, bateria, instalacja i aktualizacje |
| Realtime | 250/500/1000 połączeń localhost; poprawne dostarczenie i odrzucanie starych wersji | Autoryzacja, TLS, PostgreSQL fan-out, WAN, cloud capacity |
| Chmury/rynek | Oficjalne źródła i częściowy kalkulator kosztów; 11 produktów | Pełny TCO, ręczne testy skuteczności wszystkich produktów, skuteczność AI |

Źródła, środowiska i ograniczenia są w [raportach](research/2026-09/README.md). Liczby z badania są punktem odniesienia, nie specyfikacją produkcyjną.

## Co nie jest wymagane do przeniesienia kontekstu

Osobiste bazy i konfiguracja, wielogigabajtowe dane syntetyczne, `build/research/`, lokalne klastry PostgreSQL, `.venv` oraz cache npm/Cargo/Electron nie należą do pakietu Git. Czytanie raportów i weryfikacja kontekstu nie wymagają tych plików. Dane syntetyczne można wygenerować od nowa według [instrukcji](../scripts/research/README.md).

Surowe diagnostyki UI zawierają historyczne ścieżki maszyny pomiarowej; nie są ścieżkami wymaganymi na nowym komputerze. Drobne statystyki odczytane z osobistej starej bazy zostały zachowane wyłącznie lokalnie w ignorowanym `build/research/private`; nie są potrzebne do rekomendacji ani odtworzenia benchmarków.

Przy dalszych testach starszej aplikacji używaj izolowanej konfiguracji i bazy: program może korzystać z `~/.focuswatch` lub `%LOCALAPPDATA%/FocusWatch`. Dawne README opisuje uruchomienie watchera, a nie bezpieczny preflight repo. Historyczne instrukcje nie są kontraktem nowej aplikacji.

## Po kolejnym etapie

Uzupełnij ten dokument o zakres zmian, commit/branch, wykonane sprawdzenia, znane ograniczenia i następny konkretny krok. Statusy techniczne aktualizuj w rejestrze decyzji, a postęp w planie. Nie zapisuj ustaleń wyłącznie w czacie.
