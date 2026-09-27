# Odczyt i odtwarzanie badań architektury

Ten katalog zawiera **eksperymenty z września 2026**, a nie nową implementację FocusWatch. Do kontynuowania analizy na innym komputerze wystarczy repozytorium: nie trzeba uruchamiać aplikacji, pobierać modeli, instalować bibliotek ani odzyskiwać prywatnej bazy. Poniższe komendy zakładają katalog główny repozytorium jako bieżący katalog.

## Najpierw przeczytaj zapisane wyniki

Punktem wejścia jest [synteza i mapa materiałów](../../docs/research/2026-09/README.md). Dalej, zależnie od pytania:

- [Desktop: porównanie](../../docs/research/2026-09/desktop-comparison.md) oraz [wyniki i ograniczenia pomiarów](../../docs/research/2026-09/desktop-results.md).
- [Dane: metoda](../../docs/research/2026-09/data-evaluation.md) oraz [wyniki](../../docs/research/2026-09/data-results.md).
- [Backend](../../docs/research/2026-09/backend-comparison.md), [realtime](../../docs/research/2026-09/realtime-design.md) i [chmura z modelem kosztów](../../docs/research/2026-09/cloud-comparison.md).
- [Konkurencja](../../docs/research/2026-09/competitors.md) oraz [ocena przebudowy](../../docs/research/2026-09/rewrite-assessment.md).

Markdown i JSON można czytać dowolnym edytorem na Windows, Linux lub macOS. Wnioski mają ograniczenia opisane przy konkretnym eksperymencie. Liczby są historycznym pomiarem jednego hosta; ceny i dokumentacja dostawców odnoszą się do zapisanej daty. Odczyt danych nie wymaga konta chmurowego ani sieci.

## Lekkie sprawdzenie bez instalacji i uruchamiania prób

Wystarczy Python 3.10+ ze standardową biblioteką. Na Windows można zastąpić `python3` przez `py -3`:

```sh
python3 scripts/verify_handoff.py
```

Skrypt sprawdza dokumenty i lokalne linki, składnię źródeł, 27 zapisanych odwołań do hashy, statusy prób oraz ponownie liczy offline model chmury w katalogu tymczasowym. Nie instaluje pakietów, nie uruchamia aplikacji, benchmarków ani usług i nie wymaga dostępu do prywatnych danych. Przeliczenie korzysta z zapisanych cen; nie sprawdza aktualnego cennika ani pojemności instancji.

To kontrola spójności zapisów i zgodności źródeł, **nie powtórzenie benchmarku ani niezależne potwierdzenie jego wyników**. X11 i lifecycle nie mają własnego manifestu hashy; ich skrypty są ujęte w manifestach UI. Jeśli źródła zostaną później świadomie zmienione, nie „naprawiać” hashy historycznych JSON. Zachować stary wynik wraz z rewizją źródeł, a nowe pomiary zapisać osobno. Reguły `.gitattributes` utrzymują LF w snapshotcie, żeby automatyczne konwersje końców linii nie zmieniały hashy między systemami.

`summarize_data.py` nie wykonuje pomiarów, ale **nadpisuje** `docs/research/2026-09/data-results.md`; nie jest potrzebny do samego odczytu.

## Opcjonalne odtworzenie: osobne środowisko i wyniki

Poniższe kroki są kosztowniejsze: pobierają zależności, kompilują programy, generują duże syntetyczne pliki lub uruchamiają lokalne procesy. Nie są wymagane przy przejęciu zadania przez następnego agenta. Najpierw określić, którą hipotezę ma rozstrzygnąć nowy pomiar; nie odtwarzać całego zestawu automatycznie.

Użyć **osobnego checkoutu/worktree bieżącej rewizji**, bez prywatnych plików aplikacji. Domyślne ścieżki wielu runnerów prowadzą do historycznych JSON w `docs/research/2026-09`. Tam, gdzie jest `--output`, podać nową ścieżkę w `build/research/replay-results`. `sync_semantics_probe.py`, `desktop_collector_probe.py`, `desktop_x11_probe.py` i `realtime_probe.py` nie mają opcji wyjścia: uruchamiać je tylko w checkoutcie przeznaczonym do nowego pomiaru, a ich wyników nie traktować jako oryginalnej serii z 2026-09-27.

Nie uruchamiać pomiarów równolegle z innymi benchmarkami lub kompilacją. Zachować informacje o systemie, CPU/RAM, wersjach narzędzi, obciążeniu oraz zmienionej konfiguracji. Nie scalać liczb z różnych hostów w jedną serię. Wynik na Windows lub z GPU jest nowym eksperymentem; istniejące runnery nie stanowią gotowego zestawu testów Windows.

### Wymagania i przenośność

| Próba | Co musi być dostępne lokalnie | Zakres i miejsce zapisu |
| --- | --- | --- |
| Odczyt / sprawdzenie hashy / koszty | Python 3 dla komend; edytor wystarczy do odczytu | Przenośne; brak dostępu do prywatnych danych |
| SQLite + DuckDB | Python, `duckdb`, `psutil`; SQLite z modułem `dbstat` | Runner czyta `/proc/cpuinfo`, więc obecny harness jest Linux-only; duże pliki w `--data-dir` |
| PostgreSQL | Poprzednie zależności oraz `psycopg`, lokalne `initdb` i `pg_ctl` w `PATH`, zwykły użytkownik bez roota | Własny klaster, Unix socket, bez TCP i bez połączenia z istniejącą bazą; nowy `--cluster` |
| Semantyka synchronizacji | Python i dane strefy `Europe/Warsaw` dla `zoneinfo` | Standardowa biblioteka i tymczasowe syntetyczne SQLite; sprawdzono na Linux, nie kwalifikowano innych systemów |
| Desktop UI | Linux x86-64, Python + PySide6 + psutil, Node/npm, Rust przez rustup, linker/toolchain C, `pkg-config`, GTK3, WebKitGTK 4.1, libsoup3, Xvfb, `dbus-run-session`, biblioteki platformy Qt xcb | PSS i `/proc`, prywatne Xvfb/D-Bus; obecny runner Linux-only, software rendering |
| X11 | Python, `Xvfb`, `xdotool`, `libX11.so.6` | Linux/X11, własny syntetyczny display; bez odczytu pulpitu użytkownika |
| Lifecycle collectora | Python, `rustc +stable`, obsługa Unix socket | Mały program Rust bez Cargo; obecna próba Unix, wykonana na Linux |
| Realtime | Linux, Python + psutil, `cargo +stable`, Node 22 z wbudowanym WebSocket, co najmniej dwa dostępne logiczne CPU | Linux affinity/PSS; własny serwer na `127.0.0.1:0`, bez chmury, auth i TLS |

Historyczne wersje: Python 3.14.7, SQLite 3.53.4, PostgreSQL 18.6, Node 22.22.0, rustc 1.96.0. UI: PySide6/Qt 6.10.2, Electron 42.3.0, React 19.3.0, Tauri 2.12.0, WebKitGTK 2.52.6. Szczegółowe wersje znajdują się w odpowiednich JSON. To opis użytego środowiska, nie deklaracja minimalnych wersji ani zamrożony obraz systemu. Nie instalować pakietów systemowych tylko w celu przeczytania wyników.

`requirements.in` przypina DuckDB 1.5.5, psutil 7.2.2 i psycopg[binary] 3.3.6. **Nie obejmuje PySide6** i nie jest kompletnym lockfile wszystkich zależności Python/platformy. `desktop_npm.lock`, `desktop_cargo.lock` i `realtime_probe_cargo.lock` utrwalają grafy odpowiednich pakietów. `cargo +stable` wybiera lokalny aktualny toolchain, więc sam lockfile nie odtwarza historycznej wersji kompilatora ani bibliotek systemowych. `realtime_probe.py --prepare` wykonuje `cargo fetch` i kopiuje lockfile z powrotem do źródeł; po nim sprawdzić diff, nie akceptować zmiany locka jako neutralnej względem historycznych hashy.

### Przygotowanie izolowanego Pythona

Tylko jeśli wybrano odtwarzanie prób, w jego checkoutcie:

```sh
python3 -m venv build/research/venv
build/research/venv/bin/python -m pip install -r scripts/research/requirements.in
```

Dla UI dodatkowo potrzebny jest PySide6 w tym samym interpreterze. Historycznie wykorzystano istniejącą `.venv`; na nowym komputerze nie zakładać jej obecności:

```sh
build/research/venv/bin/python -m pip install 'PySide6==6.10.2'
```

Dostępność odpowiedniego wheel zależy od systemu i wersji Pythona. Jeśli wersja historyczna nie jest dostępna, odnotować zmianę środowiska zamiast przypisywać nowy wynik starej konfiguracji.

### Dane i PostgreSQL

```sh
build/research/venv/bin/python scripts/research/data_benchmark.py \
  --rows 1000000 10000000 \
  --data-dir build/research/replay-data \
  --output build/research/replay-results/data-results.json
build/research/venv/bin/python scripts/research/postgres_benchmark.py \
  --parquet build/research/replay-data/observations-1000000.parquet \
  --cluster build/research/replay-pg/cluster \
  --output build/research/replay-results/postgres-results.json
```

To rzeczywiste generowanie i ładowanie 11 mln wierszy, nie szybki test. Sam wynik SQLite dla 10 mln zajmował około 4,83 GB; dochodzą Parquet, drugi zbiór, klaster PostgreSQL, pliki tymczasowe/WAL oraz buildy. Potrzebny jest zapas wielu GB na dysku. Nie wybierać `/tmp` będącego tmpfs do dużych baz. `--reuse` wymaga obu kompletnych, wcześniej utworzonych plików SQLite/Parquet i nie zastępuje pierwszego generowania.

PostgreSQL odmawia nadpisania istniejącego klastra. Socket ma stały port 54391 w katalogu nadrzędnym klastra; używać osobnego katalogu nadrzędnego dla niezależnych prób. Obecny harness zakłada Unix socket i ścieżki nadające się do jego opcji startowych. Wybrać krótką lokalną ścieżkę bez apostrofu: bardzo głębokie katalogi mogą przekroczyć limit długości socketu. Nie wskazywać istniejącego klastra produkcyjnego.

### Desktop i brakujący artefakt Electron

Repozytorium **nie zawiera zipa Electron ani jego cache**. `desktop_probe.py --prepare` sam go nie pobiera. Oryginalny plik pochodził z lokalnego cache; na nowym komputerze trzeba osobno pozyskać tę samą wersję `electron-v42.3.0-linux-x64.zip` i zweryfikować ją względem oficjalnych sum kontrolnych. W repo nie zapisano SHA-256 tego zipa, więc obecne hashe źródeł nie poświadczają tożsamości jego bajtów.

Ustawić zmienną na rzeczywisty plik — poniższa ścieżka jest miejscem do uzupełnienia, nie częścią repo:

```sh
FOCUSWATCH_ELECTRON_ZIP='/absolute/path/to/electron-v42.3.0-linux-x64.zip'
build/research/venv/bin/python scripts/research/desktop_probe.py \
  --prepare --electron-zip "$FOCUSWATCH_ELECTRON_ZIP"
build/research/venv/bin/python scripts/research/desktop_probe.py \
  --run --segments 1000 --repeats 3 \
  --output build/research/replay-results/desktop-results-1000.json
build/research/venv/bin/python scripts/research/desktop_probe.py \
  --run --segments 10000 --repeats 3 \
  --output build/research/replay-results/desktop-results-10000.json
```

`--prepare` pobiera npm/Cargo i kompiluje Tauri z `-j2`; mimo nazwy jest kosztownym krokiem. Używa `build/research/desktop` oraz cache narzędzi, nie instaluje pakietów systemowych. Runner obecnie odpytuje wersje PySide, WebKitGTK i Rust także przy wybranym podzbiorze runtime; `--runtimes electron` nie jest obejściem wszystkich pozostałych wymagań środowiska. Nie obiecywać działania tej samej komendy na ARM, Windows ani macOS.

Próby X11 i lifecycle opisuje [raport desktop](../../docs/research/2026-09/desktop-results.md). W osobnym checkoutcie można wykonać je poleceniami `build/research/venv/bin/python scripts/research/desktop_x11_probe.py` i `build/research/venv/bin/python scripts/research/desktop_collector_probe.py`. Obie zapiszą wyniki pod historycznymi nazwami w `docs`; nie uruchamiać ich w ramach samej weryfikacji istniejących artefaktów.

### Realtime

Dokładną semantykę i ograniczenia opisuje [realtime-design.md](../../docs/research/2026-09/realtime-design.md). W checkoutcie do odtwarzania:

```sh
build/research/venv/bin/python scripts/research/realtime_probe.py --prepare
build/research/venv/bin/python scripts/research/realtime_probe.py --build
build/research/venv/bin/python scripts/research/realtime_probe.py --run
```

Pierwszy krok pobiera zależności, drugi kompiluje, trzeci mierzy lokalny relay przy 250/500/1000 połączeniach i nadpisuje `realtime-results.json` tego checkoutu. Host musi pozwalać na CPU affinity i odpowiednią liczbę deskryptorów; nie podnosimy limitów systemowych automatycznie. To nie pomiar chmury ani obietnica jej pojemności.

## Co przenosimy przez Git

Przenosimy źródła, lockfile, opisy, wejścia kalkulatora i niewielkie wyniki JSON/Markdown. `build/` i `.venv` są ignorowane i muszą zostać odtworzone lokalnie, jeśli dalszy eksperyment tego wymaga. Nie przenosimy prywatnego `focuswatch.sqlite`, jego kopii/WAL, sekretów, cache przeglądarki, profili ani wygenerowanych wielkich zbiorów. Ignorowanie `*.sqlite` nie jest ogólną ochroną wszystkich formatów danych; duże artefakty trzymać pod `build/research`, a przed commitem przejrzeć `git status` i zawartość dodawanych plików.

Ograniczone statystyki starej lokalnej bazy (`legacy-density.json`) pozostają wyłącznie w ignorowanym `build/research/private` na komputerze pomiarowym. Nie są częścią pakietu Git ani wymaganiem odtworzenia badań. Nie prosić automatycznie o przekazanie prywatnej historii na nowy komputer.

Pozostałe wystąpienia `/home/sefni` w surowych wynikach UI są historycznymi komunikatami diagnostycznymi o ścieżce checkoutu. Nie są konfiguracją do skopiowania. Zachowano je wraz z oryginalnym evidence; przykłady poleceń używają ścieżek względnych i zmiennej dla zewnętrznego zipa.
