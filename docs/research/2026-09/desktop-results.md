# Desktop i collector: wyniki wykonanych prób

Pomiar: 27 września 2026. Dane są syntetyczne. Nie uruchamiano obecnego FocusWatch, nie czytano prywatnych tytułów okien i nie zmieniano autostartu. Kierunek architektury oraz źródła platformowe: [desktop-comparison.md](desktop-comparison.md).

**Wniosek:** przy 1000 widocznych segmentów wszystkie trzy implementacje utrzymywały medianę odstępów między rozpoczęciami odrysowania około 16–17 ms. Qt Quick miał zdecydowanie najniższe zużycie pamięci i najkrótszy start. Electron rysował szybciej niż pozostałe powłoki, szczególnie przy 10 tys. segmentów, ale wymagał około 322–330 MiB PSS dla otwartego, minimalnego UI. Tauri był wykonalny przy zwykłym widoku i lżejszy od Electron. Wyniki nie dają podstaw do uniwersalnego rankingu frameworków ani deklaracji wydajności kompletnego raportu.

## Co i jak zmierzono

Host: Intel Core i7-6700HQ, 32 GB RAM, Arch Linux, kernel 7.2.7-arch1-1. Każdy runtime uruchamiano jako rzeczywistą aplikację desktopową we własnym Xvfb 1280×800, z programowym renderowaniem, oddzielnym D-Bus oraz nowym profilem/cache/XDG. Okno miało 1200×700, a Canvas 1000×500 z 10 rzędami syntetycznych segmentów. Tauri i Electron używały tego samego produkcyjnego bundle React; Qt Quick Canvas wykonywał odpowiadającą mu pętlę QML/JavaScript. Nie używano GPU, bazy danych ani collectora w pomiarze UI.

Zbadano osobno 1000 segmentów jako przykładowy widok po agregacji i 10 tys. jako obciążenie. To zakresy eksperymentu, nie zatwierdzone wymagania produktu. Każdą kombinację uruchomiono trzy razy, ze zmienianą kolejnością runtime. Po pierwszym rysowaniu następowało 5 sekund bezczynności i 60 odrysowań. Wszystkie **18 prób zakończyły się poprawnie**.

Wersje zapisane w wynikach: Python 3.14.7, PySide6/Qt 6.10.2, psutil 7.2.2, Electron 42.3.0, Tauri 2.12.0, React 19.3.0, WebKitGTK 2.52.6, rustc 1.96.0. Tauri zbudowano w profilu release z `opt-level=1`; jest to profil próby, nie porównanie optymalizacji kompilatora.

Definicje metryk:

- **Start**: od uruchomienia procesu do otrzymania przez harness komunikatu po pierwszym wysłaniu poleceń Canvas. Obejmuje start mostu raportującego, nie potwierdza wyświetlenia pikseli na ekranie. Nie czyszczono cache systemu operacyjnego; nie jest to pomiar zimnego startu.
- **PSS idle**: mediana próbek całego obserwowanego drzewa procesów podczas bezczynności, z pominięciem pierwszych 0,5 s i ostatnich 0,2 s. Obejmuje własny wrapper i daemon D-Bus. PSS proporcjonalnie rozdziela strony współdzielone; nie oznacza pełnego dodatkowego kosztu w całym systemie. Usługi portalu odłączone od drzewa mogą pozostać poza pomiarem.
- **Czas rysowania**: czas pętli wysyłającej polecenia Canvas, mierzony `Date.now()` z rozdzielczością 1 ms. Nie mierzy ukończenia pracy GPU ani prezentacji klatki.
- **Odstęp odrysowań**: różnica czasów rozpoczęcia kolejnych odrysowań, z harmonogramem rAF w webview oraz Timer w Qt. Nie jest pomiarem opóźnienia wejście–ekran.

W tabelach podano **medianę z trzech statystyk poszczególnych uruchomień**. P95 jest najpierw liczone metodą nearest-rank dla 60 odrysowań lub 59 odstępów w jednym uruchomieniu; następnie podawana jest mediana trzech p95. Nawiasy przy starcie i pamięci pokazują min–max trzech prób. Nie wyznaczamy p95 startu z trzech otwarć.

## 1000 segmentów: zwykły widok po agregacji

Źródło: [desktop-results-1000.json](desktop-results-1000.json).

| Runtime | Start, ms (min–max) | PSS idle, MiB (min–max) | Rysowanie: mediana / p95, ms | Odstęp odrysowań: mediana / p95, ms |
| --- | ---: | ---: | ---: | ---: |
| Tauri + React | 1728 (1586–1819) | 244,5 (243,6–245,2) | 4 / 8 | 16 / 17 |
| Electron + React | 1077 (1024–1099) | 322,2 (320,0–323,7) | 1 / 1 | 17 / 18 |
| Qt Quick + PySide6 | 437 (401–562) | 56,6 (56,6–56,6) | 3 / 6 | 16 / 21 |

Electron ma zapas czasu wykonywania tej pętli, lecz przy tym zakresie różnica 1 vs 3–4 ms nie przekłada się automatycznie na zauważalnie płynniejszy raport: harmonogram odrysowań wszystkich kandydatów jest zbliżony. Qt jest mocnym kandydatem do interfejsu, dla którego zasoby mają pierwszeństwo. Tauri ma około 78 MiB mniej PSS niż Electron, ale ponad czterokrotnie więcej niż Qt w tej konkretnej próbie. Electron zużywa około 32% więcej PSS niż Tauri i około 5,7 razy tyle co Qt.

Mediana odczytanego CPU idle, jako procent **jednego** logicznego CPU: Tauri 0,484%, Electron 0,485%, Qt 0,000%. Przedziały trzech prób wyniosły odpowiednio 0,478–0,730%, 0,244–0,734% i 0–0%. Zera oznaczają brak przyrostu przy rozdzielczości licznika i krótkim oknie, nie dowód absolutnego braku pracy. To nie test energii ani długotrwałych wycieków. Nie używamy tych drobnych różnic do wyboru frameworka.

## 10 tys. segmentów: próba obciążeniowa

Źródło: [desktop-results.json](desktop-results.json).

| Runtime | Start, ms (min–max) | PSS idle, MiB (min–max) | Rysowanie: mediana / p95, ms | Odstęp odrysowań: mediana / p95, ms |
| --- | ---: | ---: | ---: | ---: |
| Tauri + React | 1482 (1441–1484) | 248,1 (247,1–248,2) | 27 / 40 | 33 / 50 |
| Electron + React | 1007 (910–1086) | 329,6 (326,7–330,7) | 5 / 7 | 17 / 23 |
| Qt Quick + PySide6 | 454 (440–486) | 58,2 (58,1–58,2) | 17 / 25 | 34 / 46 |

Electron zachował największy zapas w tym programowym wariancie Canvas. Tauri i Qt Canvas przy tym obciążeniu nie utrzymywały odstępów około 16,7 ms. To przesłanka na rzecz Electron przy gęstych raportach React, ale nie dowód, że aplikacja musi stale rysować 10 tys. segmentów. Agregacja do rozdzielczości widoku jest pierwszym środkiem kontroli kosztu. Natywna scena Qt, WebGL, inne biblioteki wykresów i prawdziwe GPU mogą zmienić relacje; nie były badane.

Niższy start Tauri przy 10 tys. niż przy 1000 nie oznacza przyspieszania przez dodawanie danych. To osobne krótkie serie na współdzielonym hoście, bez kontrolowania cache systemowego i temperatury. Zapisano load average przed/po każdej serii; obciążenie hosta nie wynosiło zero. Inne benchmarki zespołu i kompilacje wstrzymano na czas pomiarów, ale nie zatrzymywano zwykłych procesów użytkownika.

## Co wyniki zmieniają w wyborze

**Rekomendujemy do dalszego pionowego prototypu Electron + React/TypeScript oraz niezależny collector Rust**, z umiarkowaną pewnością. Przesłankami są kontrolowana wersja Chromium na pierwszych dwóch systemach, dostęp do narzędzi raportowych React i zmierzony zapas renderowania. Nie jest to zwycięstwo pod względem zasobów: Qt wyraźnie wygrywa zmierzoną pamięcią i startem, a Tauri także zużywa mniej pamięci. Tauri nie zostaje odrzucony przez sam wynik 10 tys. segmentów; 1000 potwierdza wykonalność zwykłego widoku.

Proponowany wcześniej cel **300 MiB PSS UI nie jest wymaganiem użytkownika**. Minimalny Electron go przekracza już przed dodaniem prawdziwego dashboardu. Nie podnosimy tego progu, aby uzyskać wynik „pass”. Budżet docelowego interfejsu pozostaje do oceny wraz z rzeczywistymi funkcjami. Jeżeli niski koszt pamięci stanie się wymogiem twardym, pierwszym alternatywnym wyborem jest nowy Qt Quick; przy zachowaniu Reacta należy ponownie ocenić Tauri.

UI ma się całkowicie zamykać, a collector działać oddzielnie. To pozwala nie płacić kosztu Electron, kiedy raporty nie są otwarte; nie usuwa kosztu podczas używania raportów. Pomiar nie uzasadnia uruchamiania całego UI stale w tle. Rust jest osobną decyzją dotyczącą adapterów, dystrybucji i kontroli zasobów; wyniki UI i X11 nie dowodzą konieczności tego języka.

Przed wdrożeniem potrzebny jest rzeczywisty pionowy raport na Windows 11 i Arch/dwm, z GPU, użyciem klawiatury, filtrowaniem/panowaniem, dłuższym idle oraz instalacją/aktualizacją. Nie wykonano tych testów. Trzy falsyfikowalne warunki dalszej decyzji są zapisane w [porównaniu](desktop-comparison.md#trzy-warunki-utrzymania-rekomendacji).

## X11: koszt strategii dostępu do API

Źródło: [desktop-results-x11.json](desktop-results-x11.json), skrypt [desktop_x11_probe.py](../../../scripts/research/desktop_x11_probe.py).

Ten sam Python odczytywał własne syntetyczne okno na prywatnym Xvfb: raz przez utrzymywane połączenie Xlib, raz przez dwa procesy `xdotool` na snapshot. W obu ścieżkach sprawdzano zgodność nazwy i klasy. Wykonano 5 partii po 100 odczytów każdą metodą.

| Metoda | Mediana z median partii, ms | Zakres median partii, ms |
| --- | ---: | ---: |
| Stałe połączenie Xlib | 0,149 | 0,124–0,167 |
| Dwa procesy xdotool | 11,121 | 10,907–14,791 |

Odczyt po stałym połączeniu był około 75 razy krótszy w tym eksperymencie. Porównujemy całe ścieżki, w tym inicjalizację `xdotool` i dodatkowe żądania, a nie sam koszt `fork`. To dowód, że można usunąć koszt podprocesów **również w Pythonie**. Nie wykonano porównania Rust vs Python, pomiaru rezydentnego CPU collectora ani testu subskrypcji zdarzeń. Praktyczny adapter powinien korzystać ze zdarzeń oraz ponownych odczytów tylko wtedy, gdy są potrzebne.

Fixture sam ustawiał `_NET_SUPPORTED` i `_NET_ACTIVE_WINDOW`. Nie był prawdziwym menedżerem okien, więc wynik nie potwierdza kompatybilności konkretnej konfiguracji dwm, zachowania po restarcie X czy niepełnych właściwości aplikacji.

## Cykl życia collectora i framing

Źródło: [desktop-results-lifecycle.json](desktop-results-lifecycle.json), [harness](../../../scripts/research/desktop_collector_probe.py) i [syntetyczny collector Rust](../../../scripts/research/desktop_collector_probe.rs). **10/10 sprawdzeń zakończonych powodzeniem:**

- Proces zbiera syntetyczne zdarzenia bez UI, a awaria klienta nie zatrzymuje collectora.
- Socket w prywatnym katalogu ma tryb `0600`; nieobsługiwany komunikat jest odrzucany.
- Snapshot może jednocześnie reprezentować foreground edytora oraz odtwarzanie mediów.
- Restart zwiększa numer sekwencji, usuwa niepełną końcówkę dziennika i nie powiela zatwierdzonej numeracji.
- Framing native messaging przechodzi roundtrip w pamięci oraz odrzuca za duży i ucięty komunikat.

To walidacja granicy procesów na Unix socket i małym syntetycznym dzienniku. Nie jest to produkcyjne crash recovery, audyt autoryzacji IPC, protokół synchronizacji ani rzeczywista integracja przeglądarki. Parser socketu jest celowo uproszczony. Brakujący czas podczas zatrzymania collectora pozostaje luką; spójna numeracja nie odtwarza niezarejestrowanej aktywności. Windows named pipe, autostart, blokowanie aplikacji i updater nie były testowane.

## Odtwarzalność i stan po zakończeniu

Komendy przygotowania i uruchomienia są w [desktop-comparison.md](desktop-comparison.md#reprodukowalne-próby). Zależności npm/Cargo mają zapisane lockfile. UI 1000 i 10000 zapisują identyczną mapę SHA-256 dziesięciu plików `desktop_*`; po zakończeniu sprawdzono jej zgodność z aktualnymi źródłami. Każde uruchomienie zawiera surowe próbki pamięci, komunikaty z czasami rysowania i ostatnie diagnostyki. Przed końcowym opisem sprawdzono `/proc`: nie pozostał żaden własny runtime próby ani Xvfb.

Przygotowanie Tauri wykorzystało istniejące GTK 3.24.52, WebKitGTK 4.1/2.52.6, libsoup 3.6.6 i toolchain Rust, bez instalowania pakietów systemowych. Od utworzenia pierwszego logu przygotowania do powstania binarki minęło około 11 min 14 s, wliczając zależności, naprawę brakującej syntetycznej ikony i równoległe ładowanie danych przez inną próbę. Ten czas nie jest uczciwym benchmarkiem czystej kompilacji. Zaobserwowany później incremental build trwał około 1 min 6 s. Nie mierzono porównywalnego czasu budowania instalatorów, rozmiaru pełnej dystrybucji ani podpisywania/aktualizowania.

W izolowanym środowisku część logów zawierała diagnostyki niedostępnego PipeWire i błędu montowania document portal/FUSE. Testowana ścieżka Canvas zakończyła się poprawnie, ale nie dowodzi to działania dialogów plików, mediów ani integracji portalu. Te funkcje wymagają osobnego sprawdzenia na docelowym pulpicie.

Surowe JSON z tej próby to pomiary minimalnych aplikacji na jednym hoście. Nie dowodzą wydajności obsługi milionów rekordów, pracy mobilnej, jakości wykresów, dostępności, skuteczności rekomendacji ani niezawodności przyszłego produktu.
