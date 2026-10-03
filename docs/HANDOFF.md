# Przekazanie FocusWatch

Stan: **03.10.2026**. Dokument wystarcza do kontynuacji bez historii czatu. Ostatni etap to domknięcie rekomendacji i planu po doprecyzowaniu płatnego modelu oraz kryteriów wyboru technologii. **Nie rozpoczęto nowej implementacji ani płatnego wdrożenia.**

## Bieżąca gałąź i baza

Gałąź tej aktualizacji: **`codex/paid-product-architecture-2026-10-03`**.

Baza: `codex/architecture-evaluation`, odczytany commit **`cdd122389904f7449814179a989f53f0a176cb49`**. Nowa gałąź dokumentacyjna jest przygotowana do przeglądu; nie oznacza scalenia do bazy ani `main`.

Starszy kod bazował na `dc251ba1b02e108f61d97e382991e7f7223495aa`, obejmującym Projects (`00101b8`) i poprawki modeli/migracji. Nie należy ponownie scalać Projects ani zakładać, że zwykły checkout `main` zawiera pakiet badawczy.

```sh
git clone --branch codex/paid-product-architecture-2026-10-03 https://github.com/sieradzki/FocusWatch.git
cd FocusWatch
git status --short --branch
git log -3 --oneline
python3 scripts/verify_handoff.py
```

W istniejącym checkout najpierw sprawdzić lokalne zmiany, następnie fetch i bezpieczne przełączenie. Nie resetować pracy użytkownika. Na Windows użyć dostępnego Python 3.10+, np. `py -3`.

## Co jest w repo

- `focuswatch/`, `test/`, `requirements.txt`, `focuswatch.spec`: stara aplikacja Python/PySide6, nie nowy rdzeń.
- [Badanie 2026-09](research/2026-09/README.md): historyczne raporty oraz JSON pomiarów; nie zostały przeliczone ani zmienione w tym etapie.
- `scripts/research/`: izolowane eksperymenty, generator i kalkulator; nie produkcyjny kod.
- [Brief](PROJECT_BRIEF.md), [decyzje](architecture/DECISIONS.md), [plan](IMPLEMENTATION_PLAN.md): aktualny kontekst.
- [Baseline 03.10](architecture/REBUILD_BASELINE_2026-10-03.md) i [macierz odbioru prototypu](architecture/PROTOTYPE_ACCEPTANCE.md): nowa rekomendacja i konkretna kolejność weryfikacji.

## Najważniejsze doprecyzowania

**Wymagania użytkownika:** produkt z założenia płatny, rozsądnie wyceniony; brak premii dla stosu z powodu znajomości właściciela; rozwój uwzględnia agentów AI. Nie ustalono ceny, subskrypcji, trialu ani liczby urządzeń.

**Rekomendacja inżynierska:** Rust agent + SQLite + Electron/React/TypeScript, niezależnie od UI i sieci. Chmura zależy od prywatności: rekomendowane E2EE z Workers/R2/DO kontra czytelna historia i serwis OCI/PostgreSQL. Nie zapisywać, że użytkownik wybrał E2EE lub Cloudflare.

Nie optymalizować kilku groszy kosztu kosztem niezawodności. Pokazywać koszt na płacącego i koszt całkowity; R2 jest częścią kosztorysu, nie całym TCO. Płatność, konto, urządzenie, licencja offline i klucze historii mają odrębne znaczenia.

Unia wszystkich obserwacji nie oznacza czasu aktywności człowieka. Zachować odrębne źródła, jakość i nieznane okresy. Pomiar, interpretacja, intencja, profil, korekta i polityka są oddzielone. Brak wymogu starego UI, migracji, Kanbana ani feature parity.

## Wykonane sprawdzenia i ograniczenia tego etapu

Odczytano przez GitHub aktualny ref, dokumenty startowe i skrypt weryfikacji. Sprawdzono oficjalne dokumentacje wskazane w baseline. Aktualizacja dotyczy dokumentów; nie zmienia kodu aplikacji, zależności, danych ani źródeł historycznych benchmarków.

Próba:

```sh
git clone --branch codex/architecture-evaluation --single-branch https://github.com/sieradzki/FocusWatch.git /mnt/data/FocusWatch_work
```

zakończyła się `Could not resolve host: github.com`. Dostęp connectora GitHub działał, ale nie powstał lokalny checkout. **Nie wykonano w nim `git status` ani `python3 scripts/verify_handoff.py`.** Zdalny odczyt i przegląd dokumentów nie zastępują tych komend. Ścieżka `/mnt/data` opisuje środowisko tej sesji, nie wymóg nowej maszyny.

Nie wykonano nowych pomiarów Windows, GPU, baterii, instalatorów, inferencji, pełnego syncu ani kosztów wdrożenia. Wszystkie scenariusze nowego prototypu są planem, nie zaliczonym testem.

## Historyczny stan dowodów z 27.09

| Obszar | Wykonane w badaniu wrześniowym | Czego nie dowodzi |
| --- | --- | --- |
| Stary kod | 68/68 testów w opisanym środowisku | Nowy produkt, gotowość trackerów i dystrybucji |
| Dane | SQLite/DuckDB 1 mln i 10 mln; PostgreSQL 1 mln i 200 batchy po 8 | Chmura wielu kont, przewaga języków API |
| Czas/lifecycle | 10/10 scenariuszy czasu/outbox/retry i 10/10 procesów/framing | Produkcyjny sync, Windows, utrata zasilania |
| UI | 18 prób Tauri/Electron/Qt Quick | Pełny raport, GPU, bateria, instalacja |
| Realtime | 250/500/1000 połączeń localhost | TLS/auth, WAN, fan-out i pojemność chmury |
| Koszty/rynek | Dokumentacja i częściowy model; 11 produktów | Pełny TCO, skuteczność produktów i AI |

Metody, wersje i granice: [raporty](research/2026-09/README.md). Skrypt `verify_handoff.py` sprawdza spójność tego pakietu, nie nową aplikację.

## Konkretny następny krok

Przy zleceniu implementacji rozpocząć **P0: kontrakt i szkielet lokalnego przekroju**, zgodnie z [planem](IMPLEMENTATION_PLAN.md) i [odbiorem](architecture/PROTOTYPE_ACCEPTANCE.md). Najpierw checkout i preflight, następnie testowane reguły czasu/korekt, syntetyczne źródło, tymczasowe SQLite i minimalny klient raportu. Nie otwierać ponownie ogólnego researchu bez nowej przesłanki lub polecenia.

Prywatność nie blokuje P0. Przed prawdziwym sync trzeba ją rozstrzygnąć wraz z kluczami, odzyskiwaniem i usuwaniem. Nie tworzyć płatnych zasobów na podstawie samego planu.

## Dane i środowisko

Osobiste bazy/konfiguracja, `build/research/`, venv, cache npm/Cargo i lokalne klastry nie należą do przekazania. Dane syntetyczne można odtworzyć według [instrukcji](../scripts/research/README.md); nie trzeba odtwarzać ciężkich prób dla poznania repo.

Nie używać prywatnych danych jako domyślnego fixture. Stara aplikacja może sięgać do `~/.focuswatch` lub `%LOCALAPPDATA%/FocusWatch`; jej start może rozpocząć zbieranie. Testy wymagają izolacji. Po następnym etapie uzupełnić gałąź/commit, zakres, wykonane komendy i wyniki, ograniczenia i następną czynność.
