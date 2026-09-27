# Desktop i collector: porównanie oraz próby

Stan badania: 27 września 2026. Zakres: Windows 11 i Arch Linux/dwm/X11; macOS, Wayland i telefony jako przyszłe adaptery. Pierwsza wersja zbiera metadane i dane jawnych integracji. Próby nie uruchamiają obecnej aplikacji, nie czytają prywatnych tytułów okien, nie instalują autostartu ani pakietów systemowych.

## Rekomendacja i poziom pewności

Rekomendowany kierunek dla produktu z rozbudowanymi raportami: **samodzielny collector w Rust oraz opcjonalnie uruchamiany desktop Electron + React/TypeScript**. To rekomendacja inżynierska z umiarkowaną pewnością, nie wynik punktowego rankingu ani wymóg zachowania starego kodu. Electron daje kontrolę nad wersją renderera na Windows i Linux oraz dobry zapas w syntetycznym rysowaniu. Kosztem jest dostarczanie i aktualizowanie Chromium/Node oraz większa pamięć otwartego UI. **Nowy Qt Quick jest najmocniejszą alternatywą, gdy priorytetem będzie niski koszt zasobów interfejsu**; w wykonanych próbach miał zdecydowanie najniższe PSS i najkrótszy start.

**Tauri pozostaje wykonalną alternatywą dla tego samego Reacta.** Zwykły widok po agregacji jest istotniejszy niż test 10 tys. segmentów; sam wynik stresowy nie dyskwalifikuje WebKitGTK. Tauri oszczędza pamięć względem Electron w tych próbach, ale nadal wymaga obsługi różnic WebKitGTK/WebView2 i nie wykazał tutaj przewagi responsywności. Nie wybieramy go tylko dlatego, że collector jest w Rust.

Collector ma własny cykl życia, lokalny zapis i synchronizację. Zamknięcie UI, błąd renderera i aktualizacja okien nie mogą zatrzymywać zbierania. Dzięki temu koszt otwartego Electron nie jest stałym kosztem działania collectora w tle. Pewność jest **wysoka dla rozdzielenia procesów**, **umiarkowana dla Rust**. Rust uzasadniamy dystrybucją samodzielnego programu, typami protokołu i kontrolą zasobów przy natywnych adapterach. Nie jest warunkiem obsłużenia milionów rekordów. Nowy collector Python lub C++ może realizować te same API; wykonane porównanie X11 dowodzi przewagi strategii dostępu do API, a nie języka.

Wybór Electron wymaga jeszcze raportu z docelowymi interakcjami na prawdziwych Windows 11 i Arch/dwm, z GPU i pomiarem dłuższej bezczynności. Qt Quick trzeba porównywać również przez natywną scenę/model widoku, jeżeli ten wariant zostanie wybrany; syntetyczny Qt Canvas nie wyznacza wydajności całego Qt. Nie wykonano pomiarów Flutter, C++ UI ani urządzeń mobilnych.

Nie potrzebujemy publicznej aplikacji webowej, żeby uzasadnić React: służy tutaj budowie raportów i interakcji w lokalnym desktopie. Portal konta, płatności czy zarządzania urządzeniami jest osobną decyzją produktową. Kod raportów może być współdzielony później, ale nie należy uzależniać MVP od takiego portalu.

## Uczciwa lista kandydatów

| Wariant | Powód, żeby go wybrać | Koszt i warunek zmiany decyzji |
| --- | --- | --- |
| Rust collector + Tauri 2 + React/TS | Native core w Rust; UI korzysta z WebView2 na Windows i WebKitGTK na Linux. Dostęp do ekosystemu wykresów, wirtualizowanych tabel i dostępnego HTML. | Testy dwóch silników webowych, zależności Linux i obsługa regresji WebKitGTK. Sam Tauri nie zapewnia niezależnego collectora ani blokowania aplikacji. |
| Rust collector + Electron + ten sam React/TS | Jeden dostarczany silnik Chromium; mało zmian frontendu podczas zamiany powłoki; dojrzały model main/preload/renderer. | Dystrybucja i aktualizowanie własnego Chromium/Node. Zasoby trzeba zmierzyć w całym drzewie procesów. Renderer bez Node i z małym, walidowanym mostem preload. |
| Nowy Qt Quick + PySide6 | Najniższe zmierzone PSS i najkrótszy start; natywne modele widoków i scena Qt. Python może sterować backendem, a rendering wykonuje Qt. To kandydat na nowy interfejs bez zależności od zachowania legacy. | Obecny interfejs jest Qt Widgets, więc jego wygląd nie ocenia możliwości Qt Quick. Należy oddzielić model danych od GUI, unikać milionów obiektów Python/QML i gorących pętli w Pythonie. Opakowanie interpretera i Qt w dystrybucję; osobny dobór narzędzi wykresów i ich licencji. |
| Qt Quick + C++ | Sensowny, jeśli głównym kryterium stanie się zaawansowany, natywny rendering sceny oraz zespół wybierze Qt jako podstawę produktu. | Przepisywanie logiki na C++ nie jest uzasadnione samą liczbą rekordów. Przy collectorze Rust dokładamy trzeci stos albo własne granice FFI; IPC pozwala ich uniknąć. Nie wykonano osobnego benchmarku C++. |
| Flutter/Dart + collector | Realna alternatywa, jeśli wspólny desktopowy i mobilny interfejs stanie się ważniejszy niż webowy ekosystem raportów. | Dokłada Dart i pluginy/platform channels. Nie usuwa adapterów systemowych, ograniczeń mobilnego tła ani potrzeby niezależnego collectora. Brak SDK i pomiaru oznacza brak oceny wydajności. Przy obecnym pierwszeństwie desktopowych raportów nie ma potwierdzonego wymagania, które dawałoby Flutterowi pierwszeństwo. |
| Osobne natywne UI na system | Najpełniejsza integracja z konkretną platformą. | Kilka implementacji raportów i interakcji przy pierwszych dwóch platformach; brak wymogu produktu, który obecnie uzasadnia ten koszt. Natywne moduły mobilne pozostają prawdopodobne niezależnie od desktopu. |

Źródła: [Tauri: procesy](https://v2.tauri.app/concept/process-model/), [silniki webview](https://v2.tauri.app/reference/webview-versions/), [Electron: procesy](https://www.electronjs.org/docs/latest/tutorial/process-model), [Qt Quick: wydajność i modele](https://doc.qt.io/qt-6/qtquick-performance.html), [Flutter desktop](https://docs.flutter.dev/platform-integration/desktop), [Flutter platform channels](https://docs.flutter.dev/platform-integration/platform-channels).

## Wspólna architektura niezależna od UI

```text
adapter Win32 / X11 / MPRIS / browser bridge
                    ↓
        collector w sesji użytkownika
     normalizacja → lokalny zapis/outbox
              ↙              ↘
      report/query API     sync worker
              ↑
   Tauri core / Electron main / Qt client
              ↑
       UI: agregaty, strony, zakres czasu

osobno, dopiero gdy potrzebne: ograniczony helper blokowania
```

Autostart uruchamia collector w sesji użytkownika, nie całe UI. Windows Service działa w innym kontekście niż interaktywny pulpit; uprzywilejowany helper nie powinien przejmować przechwytywania foreground. Na X11 potrzebny jest prawidłowy kontekst sesji, `DISPLAY` i autoryzacja X. W dwm nie zakładamy, że komponent środowiska desktopowego automatycznie obsłuży XDG Autostart ani że użytkownik ma tray. Instrukcja/pakiet powinny wspierać uruchamianie przez sesję i opcjonalne zarządzanie procesem użytkownika. Próby nie zmieniają konfiguracji startu. [Microsoft: usługi interaktywne](https://learn.microsoft.com/en-us/windows/win32/services/interactive-services), [XDG Autostart](https://specifications.freedesktop.org/autostart/latest/), [plugin Tauri Autostart](https://v2.tauri.app/plugin/autostart/).

IPC: wersjonowane komunikaty, ograniczony rozmiar, limity czasu i kolejek, metody opisane typami. Linux/macOS: Unix domain socket w prywatnym katalogu; Windows: named pipe z ACL dla użytkownika. UI nie dostaje dostępu do plików bazy, sekretów ani dowolnego wykonania shell. Tauri `invoke` jest mostem webview–core; **nie zastępuje** protokołu core–collector. Qt ma `QLocalSocket` mapowany na Unix socket/named pipe, więc niezależny collector jest równie wykonalny w tym stosie. [Qt QLocalSocket](https://doc.qt.io/qt-6/qlocalsocket.html).

Rozszerzenie przeglądarki wysyła małe zdarzenia przez dedykowany native-messaging host, który łączy się z collectorem. Proces uruchamiany przez przeglądarkę nie zostaje naszym głównym daemonem. Chrome i Firefox używają JSON z czterobajtową długością; manifesty, identyfikatory rozszerzeń i zasady dostępu różnią się. Host musi sprawdzać schemat i mieć własny limit komunikatu. Rozłączenie przeglądarki oznacza utratę tego źródła, nie awarię całego collectora. [Chrome](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging), [Firefox](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Native_messaging).

Raporty otrzymują agregaty, próbki i stronicowane szczegóły. Milion zapisanych obserwacji nie oznacza miliona elementów DOM/QML. Dla szerokiego zakresu czasu używamy agregacji dobranej do szerokości wykresu; przy zbliżeniu pobieramy szczegóły. React nie powinien wykonywać aktualizacji stanu per obserwacja, a QML nie powinien tworzyć delegata per rekord bazy. Canvas/WebGL lub własny element sceny Qt są ścieżkami dla gęstej osi czasu; dostępny opis i nawigacja klawiaturą pozostają osobnymi wymaganiami. Próba Canvas nie jest testem kompletnego dashboardu ani wyborem biblioteki wykresów.

## Dystrybucja i aktualizacje

- **Tauri:** instalator Windows/WebView2; dla Arch pakiet z jawnymi zależnościami, opcjonalnie AppImage. Aktualizacje muszą być podpisane i obejmować kompatybilność protokołu UI/collector oraz migracji bazy. Wbudowany updater nie projektuje za nas atomowej aktualizacji kilku procesów. AppImage nie znosi ograniczeń glibc; release Linux budować na najstarszym wspieranym środowisku, nie uznawać binarki z bieżącego Arch za uniwersalną. [Updater](https://v2.tauri.app/plugin/updater/), [AppImage](https://v2.tauri.app/distribute/appimage/), [AUR](https://v2.tauri.app/distribute/aur/).
- **Electron:** własny runtime daje większą kontrolę wersji renderera, ale trzeba dostarczać jego poprawki. Oficjalny `autoUpdater` nie obsługuje Linux; tam dokumentacja zaleca mechanizm dystrybucji. [autoUpdater](https://www.electronjs.org/docs/latest/api/auto-updater).
- **Qt:** narzędzia do pakowania PySide istnieją; dobór modułów ma znaczenie dla licencji. Nie wolno traktować całego Qt jako jednolicie LGPL — np. Qt Graphs jest GPLv3/commercial. Własna oś czasu nie wymaga zakupu tego modułu. Nie wyliczano kosztu komercyjnej licencji bez konkretnej oferty. [PySide deployment](https://doc.qt.io/qtforpython-6/deployment/index.html), [licencje Qt](https://doc.qt.io/qt-6/licensing.html), [Qt Graphs](https://doc.qt.io/qt-6/qtgraphs-index.html).

## Adaptery i granice obietnic platformowych

| Platforma | Metadane i tło | Media oraz dobrowolne ograniczenia | Status |
| --- | --- | --- | --- |
| Windows 11 | Win32 `SetWinEventHook(EVENT_SYSTEM_FOREGROUND)` z message loop; identyfikacja procesu/okna, osobne sygnały idle/lock. Obsługa braku dostępu, znikających okien i sesji. | Browser bridge oraz opcjonalny GSMTC dla aplikacji publikujących sesje multimedialne. Blokowanie wymaga własnego mechanizmu/reguł i czasem uprawnionego helpera. | Pierwsza platforma; w tym badaniu dokumentacja, brak wykonania Windows. |
| Arch/dwm/X11 | Stałe połączenie X11, EWMH `_NET_ACTIVE_WINDOW`, właściwości okna i zdarzenia zmian. Obsługa niepełnego EWMH/WM_CLASS/tytułu oraz restartu X. | MPRIS przez D-Bus tylko dla aplikacji, które je publikują; rozszerzenie dla tabów. Helper do blokad systemowych osobno. | Pierwsza platforma; syntetyczny Xvfb pozwala zbadać mechanikę, nie dowodzi zgodności konkretnej konfiguracji dwm. |
| Wayland | Brak obietnicy jednolitego odpowiednika X11. Dostęp do listy okien i stanu aktywacji zależy od protokołów wystawionych przez compositor oraz uprawnień/integracji. | Browser bridge i MPRIS nadal użyteczne. Widoczność UI w Wayland nie oznacza możliwości obserwowania innych aplikacji. | Osobna macierz obsługiwanych compositorów, później. |
| macOS | `NSWorkspace` dla zmian aktywnej aplikacji; tytuły/kontekst przez jawnie przyznane Accessibility tam, gdzie potrzebne. Agent sesji, osobne decyzje o dystrybucji/uprawnieniach. | Integracje i rozszerzenie przeglądarki; blokowanie wymaga specyficznych API/uprawnień. | Później; Tauri/Qt/Electron UI nie przyznają tych uprawnień. |
| Android | Usage Access/UsageStats po zgodzie; ograniczenia działania w tle i polityk dystrybucji. To nie przeniesiony desktopowy daemon. | Mechanizm blokowania i zakres Accessibility/VPN wymagają osobnego projektu oraz oceny uprawnień. | Osobny companion. |
| iOS | Screen Time/Family Controls/Device Activity z autoryzacją i entitlementami; zakres danych i eksport nie jest odpowiednikiem desktopu. | Managed Settings do dozwolonych osłon aplikacji/stron, zgodnie z uprawnieniami. | Osobny companion; nie obiecujemy globalnego ciągłego foreground feed. |

Źródła pierwotne: [WinEventHook](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwineventhook), [GSMTC](https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssessionmanager?view=winrt-26100), [EWMH](https://specifications.freedesktop.org/wm/latest-single/), [MPRIS Player](https://specifications.freedesktop.org/mpris/latest/Player_Interface.html), [NSWorkspace](https://developer.apple.com/documentation/appkit/nsworkspace/didactivateapplicationnotification), [Android UsageStats](https://developer.android.com/reference/android/app/usage/UsageStatsManager), [Apple Screen Time](https://developer.apple.com/documentation/screentimeapidocumentation).

Wayland: oficjalny model protokołu opisuje obiekty udostępniane przez compositor i izolację powierzchni innych klientów. Wspierane rozszerzenia trzeba wykrywać i badać osobno; nie deklarujemy konkretnej listy zgodnych compositorów ani gwarancji dostępu do stanu aktywacji. Próby pobrania pierwotnych XML rozszerzeń foreign-toplevel z GitLab freedesktop były zablokowane przez serwer, a testu Wayland nie wykonano. [Oficjalny model Wayland](https://wayland.freedesktop.org/docs/book/Protocol.html).

Model zachowuje równoległe obserwacje: edytor na foreground, grający tab w tle, inne aktywne urządzenie. `active`, `audible`, `muted`, stan odtwarzania i widoczność są osobnymi polami. Tab aktywny w oknie nie dowodzi skupienia przeglądarki, a `audible` nie dowodzi słuchania. Sugestie opierają się na hipotezach z pochodzeniem danych i możliwością korekty. [Chrome tabs](https://developer.chrome.com/docs/extensions/reference/api/tabs).

## Reprodukowalne próby

Pliki `scripts/research/desktop_*` zawierają trzy niezależne eksperymenty:

1. **UI:** wspólny produkcyjny bundle React 19.3.0 w Tauri 2.12.0 i Electron 42.3.0; nowy PySide6 6.10.2/Qt Quick Canvas rysuje te same dane. Osobne serie **1000 segmentów jako widoku po agregacji** i **10 tys. jako próby obciążeniowej**, po trzy uruchomienia każdego runtime. Oddzielny Xvfb i D-Bus, programowe renderowanie, nowe profile. Pomiar startu do wysłania pierwszych poleceń Canvas, 5 sekund idle, 60 odrysowań, PSS/RSS drzewa procesów. Kolejność runtime zmienia się między powtórzeniami. Nie jest to przeglądarkowy zamiennik Tauri: uruchamiany jest faktyczny proces Tauri/WebKitGTK.
2. **Collector:** mały program Rust ze standardowej biblioteki, osobny klient udający UI, kontrolowana awaria klienta i collectora, restart z niepełną końcówką syntetycznego dziennika. Sprawdzenie ciągłości numeracji, niezależności od UI oraz równoległego stanu foreground/media. Framing native messaging sprawdzany w pamięci, bez instalowania rozszerzenia.
3. **X11:** ten sam Python, jedna ścieżka uruchamia dwa `xdotool` na snapshot, druga korzysta ze stałego Xlib. Własny Xvfb i własne okno; 5 partii po 100 odczytów; identyczność wyników sprawdzana przed i w czasie pomiaru.

Odczyt istniejących wyników nie wymaga uruchamiania tych prób. [Instrukcja przejęcia badań](../../../scripts/research/README.md) zawiera lekką kontrolę integralności, wymagania środowiska i luki odtwarzalności. Poniższe kroki są opcjonalnym ponownym pomiarem na Linux, w osobnym checkoutcie; najpierw przygotować opisane tam środowisko Python z PySide6 i psutil. Uzupełnić rzeczywistą ścieżkę do samodzielnie pozyskanego zipa Electron:

```sh
FOCUSWATCH_ELECTRON_ZIP='/absolute/path/to/electron-v42.3.0-linux-x64.zip'
build/research/venv/bin/python scripts/research/desktop_probe.py --prepare --electron-zip "$FOCUSWATCH_ELECTRON_ZIP"
build/research/venv/bin/python scripts/research/desktop_probe.py --run --segments 1000 --repeats 3 --output build/research/replay-results/desktop-results-1000.json
build/research/venv/bin/python scripts/research/desktop_probe.py --run --segments 10000 --repeats 3 --output build/research/replay-results/desktop-results-10000.json
```

Przygotowanie pobiera zależności npm/Cargo i kompiluje Tauri w `build/research/desktop`; używa też cache narzędzi i nie instaluje niczego systemowo. `cargo +stable` wybiera istniejący toolchain bez zmiany globalnego defaultu, ale nie zamraża jego wersji. Zależności główne są przypięte, a grafy użyte w próbie zachowano w `scripts/research/desktop_cargo.lock` i `desktop_npm.lock`; kolejne przygotowanie wykorzystuje te lockfile. Zip Electron, jego historyczna suma kontrolna i biblioteki systemowe nie są dostarczane przez repo. Nowe wyniki UI powyżej trafiają do ignorowanego katalogu, bez zastępowania historycznych JSON.

`desktop_collector_probe.py` i `desktop_x11_probe.py` nie przyjmują `--output` i nadpisują odpowiadające im pliki w `docs/research/2026-09`; uruchamiać je tylko w checkoutcie przeznaczonym do nowej próby. Polecenia i wymagania podaje instrukcja badań. Żaden z tych kroków nie jest potrzebny do odczytania zapisanych wyników na Windows lub macOS.

**Ograniczenia:** Xvfb/software rendering nie mierzy prawdziwego GPU, Wayland, Windows ani responsywności w dwm. Canvas w Qt i HTML ma różne implementacje. Czasy poleceń rysowania nie oznaczają zakończonej prezentacji klatki. PSS jest bardziej miarodajne niż suma RSS, ale obejmuje badane drzewo procesów, nie cały koszt systemu; osobno daemonizowane usługi portalu mogą pozostać poza tym drzewem. Próba nie modeluje kompletnej aplikacji. Idle ma krótki horyzont; nie dowodzi braku wycieku. Nie porównano natywnego C++ scene graph. Syntetyczny dziennik nie jest produkcyjnym mechanizmem crash recovery, synchronizacji ani autoryzacji IPC.

## Trzy warunki utrzymania rekomendacji

To **proponowane budżety inżynierskie dla pionowego prototypu**, nie zmierzone parametry istniejącej aplikacji ani arbitralna punktacja frameworków:

1. **Dystrybucja i adaptery:** czysty Windows 11 i Arch/dwm, instalacja/odinstalowanie oraz aktualizacja UI+collector; poprawne foreground/lock/idle/browser disconnect, jawne braki uprawnień i brak konieczności utrzymywania otwartego UI. Electron wymaga własnego rytmu aktualizacji Chromium. Tauri dodatkowo wymaga kontroli zgodności WebKitGTK/WebView2. Testy aktualizacji mogą zmienić rekomendację mimo dobrego wyniku renderowania.
2. **Rzeczywisty raport:** na docelowym laptopie proponujemy p95 otwarcia rozgrzanego UI do 2 s, p95 filtrowania/panowania po otrzymaniu agregatów do 200 ms i idle UI do 300 MiB PSS na Linux. To budżet do oceny produktowej, a nie spełniony warunek: Electron w najnowszej małej próbie przekracza 300 MiB i wymaga świadomego zaakceptowania kosztu lub wyboru lżejszego wariantu. Windows wymaga osobnego pomiaru pamięci prywatnej/working set; tych metryk nie porównujemy 1:1 z PSS. Mierzyć co najmniej 20 otwarć i 15 minut idle na prawdziwym pulpicie; osobno zimny start i pierwszy odczyt z bazy. Jeżeli niski koszt UI jest wymaganiem twardym, pierwszą alternatywą jest Qt Quick; dla utrzymania Reacta porównać Tauri.
3. **Collector bez UI:** proponujemy do 50 MiB PSS oraz średnio do 0,5% jednego logicznego CPU w ustalonym scenariuszu metadanych, z osobnym pomiarem wzrostu bazy/energii. Zamknięcie UI nie zatrzymuje collectora; restart nie duplikuje zatwierdzonych zdarzeń; luki podczas awarii/suspend są oznaczone, a nie przedstawione jako pewna aktywność. Testować też brak sieci i niezgodne wersje IPC. Nowy collector Python albo C++ spełniający te same wymagania pozostaje prawidłową alternatywą; wynik X11 nie stanowi argumentu przeciw tym językom.

Wyniki wykonanych prób i dokładna interpretacja: [desktop-results.md](desktop-results.md). Dane źródłowe: [UI 1000](desktop-results-1000.json), [UI 10000](desktop-results.json), [X11](desktop-results-x11.json), [lifecycle](desktop-results-lifecycle.json).
