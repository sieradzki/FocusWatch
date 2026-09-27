# FocusWatch: refaktor, przebudowa rdzenia czy nowa implementacja

**Rekomendacja: nowa implementacja docelowej aplikacji w tym samym repozytorium, z obecnym kodem jako źródłem wiedzy, reguł i scenariuszy testowych.** To pełnoprawny rewrite: nowy rdzeń i UI nie muszą zachowywać struktur ani kontraktów poprzednika. Drobne fragmenty czystej logiki można przenieść, jeśli pasują do wybranego stosu, ale ponowne użycie kodu nie jest wymaganiem. Nie ma podstaw, by wymagać równoległego utrzymywania starej aplikacji, zgodności starego API, migracji całej historii lub odtworzenia Kanbana przed dostarczeniem pierwszego użytecznego rezultatu.

To decyzja o granicach systemu i zakresie wykorzystania kodu. **Nie jest automatycznie decyzją o Rust ani Tauri.** Przebudowa w Pythonie z poprawną bazą i oddzielonym procesem pomiaru pozostaje wiarygodnym wariantem kontrolnym.

## Podstawa oceny i ograniczenia

Inspekcja 27.09.2026, commit `dc251ba1b02e108f61d97e382991e7f7223495aa`, przed dodaniem dokumentów badawczych. Odczytano kod źródłowy, testy, zależności, specyfikację PyInstaller i jedyny śledzony workflow CI. Ta ocena wykorzystania kodu jest statyczna. Odrębne próby syntetyczne opisują [porównanie desktopu](desktop-comparison.md) i [ocena danych](data-evaluation.md); nie są pomiarem czasu dostarczenia rewrite lub refaktoru.

Poprzedni raport [gotowości brancha](../../review-projects-readiness.md) dotyczy naprawionych modeli i migracji. Udokumentowane tam testy nie dowodzą niezawodności trackera Windows/Linux, wydajności raportów wieloletnich ani gotowości do dystrybucji konsumenckiej.

Brak wymogu zachowania kompatybilności zmniejsza koszt nowego rdzenia. Nie oznacza automatycznej zgody na usunięcie danych użytkownika: obecne pliki są materiałem źródłowym, a ewentualny import do nowego formatu może być niezależną decyzją produktu.

## Co faktycznie jest rozdzielone, a co sprzężone

1. **Warstwa usług istnieje i nie zależy powszechnie od Qt.** `ClassifierService`, `ActivityService`, `CategoryService`, `KeywordService`, `ProjectService` i `TaskService` są zwykłymi klasami Pythona; serwisy bazy przyjmują opcjonalnie połączenie do wstrzyknięcia. Stwierdzenie „cały projekt to nierozdzielny UI” byłoby błędne.
2. **Nie ma jednak niezależnego, trwałego rdzenia pomiarowego.** `__main__.py:97` kończy aplikację bez traya; `:120` tworzy serwisy i UI; `:166` uruchamia watcher jako wątek daemon tego samego procesu. Błąd lub zakończenie procesu GUI kończy także pomiar. Nie znaleziono odrębnego cyklu życia, kontroli stanu ani kolejki zapisu agenta.
3. **Watcher łączy kilka odpowiedzialności.** `watcher_service.py:278` odpytuje platformę i reaguje na zmianę tytułu; klasyfikuje, odczytuje kategorię i tworzy rekord ORM. Przedział zapisuje przy zmianie, z końcowym zapisem w `__del__`, a nie z jawnym checkpointem. Tytuł, aplikacja, obecność i ocena skupienia nie są niezależnymi obserwacjami. Istniejące wywołania WinAPI/X11 są użytecznymi wskazówkami integracyjnymi, nie gotowym kontraktem nowego agenta.
4. **Model `Activity` zawiera interpretację jako część pomiaru.** `database/models/activity.py:16` ma lokalny licznik ID, tekstowe czasy, okno, kategorię i `focused`; mapowanie `project_id` jest zakomentowane. Nie ma stabilnego źródła/urządzenia, wersji obserwacji, pochodzenia interpretacji ani mechanizmu niezależnych strumieni.
5. **Klasyfikator jest mały i możliwy do wydzielenia.** `classifier_service.py:39` pobiera słowa kluczowe przy każdym wywołaniu, a dla dopasowań odczytuje głębokość kategorii. Sama reguła substring/case/depth jest prosta; potrzebuje jawnego rozstrzygania remisów, snapshotu reguł i oddzielenia I/O. Zmiana języka nie jest konieczna do tych poprawek.
6. **Raportowanie jest częściowo w SQL, częściowo w Qt viewmodelach.** `activity_service.py:181` pobiera przedziały według daty ich rozpoczęcia i materializuje ORM; `timeline_viewmodel.py:72` iteruje przedziały i koszyki czasu w `QObject`; `period_summary_viewmodel.py:117` ponownie pobiera przedziały i sumuje zapisane `focused`. To problemy modelu zapytań, granic czasu i powtarzanego odczytu, nie dowód niewydolności Pythona lub SQLite.
7. **Rekategoryzacja jest operacją na całej historii.** `categorization_service.py:20` wczytuje wszystkie obserwacje, grupuje je i nadpisuje kategorię. Brakuje pochodzenia oraz pierwszeństwa korekt. `bulk_update_category` nie aktualizuje `focused`, choć raport korzysta z tego pola. Przeniesienie takiego algorytmu 1:1 do Rust zachowałoby semantyczny problem.

Powyższe punkty są inspekcją statyczną. Nie ustalają, jak często problem występuje w używanej obecnie bazie.

## Macierz wykorzystania istniejącej implementacji

| Podsystem | Wartość do zachowania | Decyzja dla nowego rdzenia | Zależności i zakres prac |
| --- | --- | --- | --- |
| Kontrakty czasu i obserwacji | Scenariusze aktywności, AFK, przedziałów i przekroczenia północy | **Nowy model** niezależnych źródeł, przedziałów i interpretacji | Wspólna semantyka UTC, czasu monotonicznego, przerw, nakładania i korekt; potrzebna w każdym języku |
| Zbieranie Windows/X11 | Wiedza, jakie APIs/narzędzia odczytywać; przypadki błędów | **Nowy komponent/lifecycle**, adaptery platformowe | Snapshot aplikacji/okna, brak uprawnień, suspend/resume, restart, checkpoint, błędy zapisu; UI i tray opcjonalne |
| Słowa kluczowe i kategorie | Użytkowe pojęcia, case matching, hierarchia, przykłady | **Wydzielić lub przepisać mały silnik**, zależnie od wybranego języka | Snapshot reguł bez zapytań w pętli, jawna kolejność, pochodzenie i wynik „nieustalone” |
| Przechowywanie lokalne | SQLite, wzorce transakcji, doświadczenie naprawy schematu | **Zachować SQLite jako kandydata; nowy schemat i właściciel zapisu** | Indeksy, kolejka synchronizacji, trwałe ACK, retencja, projekcje; SQLAlchemy może pozostać przy Pythonie |
| Zapytania i agregacje | Lista potrzeb użytkownika: top apps/titles/categories, oś dnia | **Nowe API raportowe i projekcje** | Przecinanie zakresów, union czasu osoby, odrębny kontekst równoległy, ograniczone wyniki; testować bez GUI |
| Qt Widgets/viewmodele | Koncepcje widoków, próbki UI i słownictwo | **Nie narzucać zachowania kodu**; wybrany UI konsumuje nowe DTO | Jeśli pozostaje Qt, część kontrolek można wykorzystać; Qt Quick lub React oznacza nowe widoki, bez portowania logiki raportów do UI |
| Projekty/Kanban/zadania | Scenariusze archiwizacji, statusu, historii czasu i plan/wykonanie | **Odroczyć lub wykorzystać selektywnie po ustaleniu zakresu produktu** | Nie odtwarzać całego modułu wyłącznie dlatego, że istnieje; nie uzależniać pomiaru od natywnego task managera |
| Migracje starego schematu | Testy rollback, indeksów, triggerów, wartości enum i własności czasu | **Zachować jako wiedzę/testowe przykłady; nie wymagać migracji v1** | Jeśli import stanie się celem, traktować go jako jednokierunkowy adapter z walidacją, nie ograniczenie nowego modelu |
| Testy modeli i konfiguracji | Konkretne przypadki danych i regresji | **Przenieść zachowania, nie mechanicznie wszystkie asercje** | Testy ORM/Qt mają wartość bezpośrednią tylko przy zachowaniu tych bibliotek; test keyword nie dowodzi kompletności klasyfikatora |
| Autostart i pakowanie | Istniejący spec PyInstaller i rozpoznane platformy | **Przeprojektować instalację i start agenta** | Obecny Linux service ma `DISPLAY=:0` i plik systemowy; instalacja użytkownika/sesja graficzna powinny być świadomą decyzją. Windows musi obsłużyć poprawną ścieżkę startu i sesję użytkownika |
| Chmura, sync, urządzenia, konto | Brak gotowej implementacji do przeniesienia | **Nowy podsystem** | Koszt ponoszony przy refaktorze i przy rewrite; obejmuje identyfikację, uprawnienia, duplikaty, spóźnienia, usunięcia i obserwowalność |

## Trzy warianty i realne kompromisy

| Wariant | Co zyskujemy | Koszt i ryzyko | Ocena dla obecnego celu |
| --- | --- | --- | --- |
| **Refaktor w miejscu: Python/PySide + obecna aplikacja** | Można poprawiać raporty, wydzielać funkcje i bezpośrednio wykorzystać obecne testy/model CRUD | Stopniowe zmiany nadal obejmą rdzeń, schemat, query API i lifecycle. Zachowanie UI może utrwalać kształt starego modelu. Kompatybilność kosztuje, choć nie jest wymagana | Dobre przy celu usprawnienia starej aplikacji. Słabsze jako domyślna droga do wieloźródłowego produktu, gdy nie trzeba utrzymywać feature parity; nie zmierzono różnicy czasu dostarczenia |
| **Nowy rdzeń + ponowne użycie istniejących GUI/CRUD przez adaptery** | Nowa semantyka pomiaru i osobny agent przy wcześniejszym dostępie do obecnych ekranów kategorii/projektów; bezpośrednie wykorzystanie części kodu i testów | Potrzebne adaptery między nowym modelem i starymi viewmodelami, nowe granice błędów oraz utrzymanie zgodności wewnętrznej. Oszczędność zależy od faktycznego wykorzystania ekranów w pierwszym zakresie | Wiarygodny wariant, jeśli zachowanie konkretnych istniejących ekranów istotnie skraca drogę do wartości. Obecny cel nie uzasadnia ponoszenia kosztu adapterów tylko dla zachowania kodu |
| **Pełna nowa implementacja, stary projekt jako materiał referencyjny** | Nowe kontrakty danych, lifecycle, raporty i UI bez długu adapterów. Można zachować wiedzę domenową i przepisać użyteczne scenariusze testowe, nie przenosząc starego kodu | Trzeba ponownie zbudować wszystkie funkcje wybranego pierwszego zakresu i zaakceptować odroczenie reszty. Złożoność platform i domeny nie znika; nowe założenia wymagają walidacji | **Rekomendowany dla obecnego zakresu.** Nowy przekrój pomiar → agregacja → raport jest centralnym celem, a kompatybilność i parity nie są wymagane. Ten sam Git zachowuje historię i materiał porównawczy |

Nie podano kosztu w osobotygodniach: brak pomiaru tempa pracy w nowym stosie, finalnego zakresu UI i decyzji o dystrybucji. Największe zależności są znane: model czasu → trwały agent → API raportowe → UI; osobno urządzenia/sync i dystrybucja. Liczba linii starego kodu nie jest wiarygodnym estymatorem.

## Krytyczny przegląd rekomendacji Rust/Tauri

Poniższa sekcja ocenia wcześniejszą propozycję; aktualny, warunkowy wybór Electron + React oraz porównanie z Qt Quick i Tauri przedstawia [porównanie desktopu](desktop-comparison.md).

**Co przemawia za Rust:** długo działający agent z natywnymi integracjami, jawna kontrola zasobów, możliwość budowania tej samej biblioteki reguł/czasu dla różnych procesów. Jest to argument utrzymaniowy i systemowy. Kod FFI, błędne jednostki czasu, niepoprawne SQL, zgubione ACK i zbyt szerokie uprawnienia nadal wymagają testów; Rust ich sam nie rozwiązuje.

**Co przemawia za Pythonem:** istniejące serwisy są w dużej części niezależne od Qt i można wydzielić agent bez zmiany języka. SQLite, DuckDB czy biblioteki numeryczne wykonują ciężkie obliczenia w kodzie natywnym. Natywne APIs są dostępne przez bindingi. Nie wykonano równoważnego benchmarku poprawnie zaprojektowanego agenta Python vs Rust, więc nie wolno uzasadniać rewrite twierdzeniem „Python nie obsłuży tylu rekordów”.

**Warunek uczciwego porównania:** ta sama semantyka, liczba procesów, zapis/flush, indeksy i dane wejściowe. Porównanie starego ORM + pełnego skanu do nowego Rust + indeksów mierzy przede wszystkim zmianę modelu dostępu. Wyniki testów silnika SQL nie są wynikami języka, a benchmark headless nie jest pomiarem renderowania GUI.

**Tauri + React:** dobry kandydat do atrakcyjnych raportów, ale korzysta z różnych webview OS. Na Linuxie zależności i WebKitGTK zwiększają macierz testową. Osobny collector musi mieć własny lifecycle; dołączenie sidecara nie zapewnia automatycznie pracy po zamknięciu UI. Nie uzasadniamy React obowiązkowym webem, bo web nie jest dziś wymaganiem. [Architektura Tauri](https://v2.tauri.app/concept/architecture/), [pakowanie AppImage](https://v2.tauri.app/distribute/appimage/)

**Alternatywy:** Qt Quick daje natywny scene graph i pozwala zachować Python, ale wymaga nowych widoków względem Qt Widgets oraz przeglądu modułów/licencji. Electron zapewnia dostarczany Chromium, kosztem własnego runtime i obowiązku jego aktualizacji. Bez równoważnego widoku i pomiaru nie przyznajemy żadnemu stosowi liczbowej przewagi RAM/startup. [Qt Quick](https://doc.qt.io/qt-6/qtquick-visualcanvas-scenegraph.html), [procesy Electron](https://www.electronjs.org/docs/latest/tutorial/process-model), [aktualizacje Electron](https://www.electronjs.org/docs/latest/tutorial/updates)

**Wniosek:** wcześniejszy Rust/Tauri pozostaje kandydatem, lecz dowody z repo mocniej uzasadniają **nowy podział odpowiedzialności i nowy model danych** niż zmianę języka. Wybór UI, agenta i backendu należy rozstrzygać osobno; „jeden język” nie uzasadnia przenoszenia ML do Rust ani wymuszenia Rust w API chmury.

## Komercyjna dystrybucja: prace niezależne od wariantu

Repo zawiera MIT `LICENSE`, PySide6 6.8.1, PyInstaller spec i CI Ubuntu/Python 3.12 pomijające `test/views`. W śledzonych plikach nie znaleziono pipeline publikującego podpisane wydania, automatycznego updatera, testów instalacji Windows ani odtwarzalnego środowiska dla architektury docelowej. To zakres brakującej implementacji, nie stwierdzenie o pozarepozytoryjnych procesach właściciela.

| Obszar | Konsekwencja dla porównania |
| --- | --- |
| **Zależności i licencje** | MIT repo nie determinuje warunków wszystkich zależności. Obecny `focus_breakdown_view.py` importuje QtCharts; dokumentacja linii Qt 6.8 wskazuje GPLv3 lub licencję komercyjną. PySide nie oznacza, że każdy moduł Qt ma te same warunki. Przed wyborem sposobu dystrybucji trzeba ustalić model produktu i użyte moduły; to nie jest wniosek, że komercyjny produkt musi być zamknięty ani że Qt trzeba porzucić. [Qt Charts 6.8](https://doc.qt.io/qt-6.8/qtcharts-index.html), [Qt for Python commercial use](https://doc.qt.io/qtforpython-6/commercial/index.html) |
| **Pakowanie Pythona** | PyInstaller ma wyjątek pozwalający budować komercyjne aplikacje; nie rozstrzyga licencji pakowanych bibliotek. Trzeba dostarczyć interpreter, natywne biblioteki i właściwe artefakty dla każdego OS. [PyInstaller license](https://pyinstaller.org/en/stable/license.html) |
| **Podpisy i aktualizacje** | Updater Tauri wymaga podpisu artefaktu, ale ten podpis nie zastępuje podpisu systemowego Windows. Dochodzi przechowywanie kluczy, wersjonowanie agenta/IPC, kanał wydania oraz obsługa awarii aktualizacji. Dostępność pluginu nie oznacza gotowego procesu release. [Updater](https://v2.tauri.app/plugin/updater/), [Windows signing](https://v2.tauri.app/distribute/sign/windows/) |
| **Wsparcie Linuxa** | Arch/dwm/X11 to pierwszy jawny cel. Należy sprawdzić brak traya, autostart sesji i instalację zależności. „Linux” nie może od razu oznaczać wszystkich dystrybucji/kompozytorów; dowolny stos ma koszt testów i obsługi zgłoszeń |
| **Bezpieczeństwo UI** | Localhost nie jest granicą uwierzytelnienia; IPC/HTTP agenta ma sprawdzać klienta i zakres operacji. Tytuły stron i dane rozszerzeń są niezaufane. Tauri/Electron wymagają ograniczonych mostów do funkcji systemowych, a nie pełnego dostępu z renderera. [Electron security](https://www.electronjs.org/docs/latest/tutorial/security) |
| **Obsługa danych i incydentów** | Zdiagnozowanie braków pomiaru powinno wymagać liczników/statusu źródeł, nie domyślnego uploadu całej historii. Eksport, reset i logi mają jasne granice prywatności; model subskrypcji nie powinien być ukrytym mechanizmem usuwania wieloletniej historii |

## Decyzja i warunki jej oceny

Przystępując do implementacji, należy budować **nowy mały przekrój produktu**: dwa adaptery desktopowe i źródło przeglądarkowe → trwałe obserwacje → deterministyczne agregaty → lokalny raport. Potrzebne są scenariusze nakładania źródeł, uśpienia, zakończenia UI, awarii agenta, zmiany czasu oraz korekt. Kanban, autonomiczne AI i twarde blokowanie nie są warunkiem tego przekroju.

Rekomendację pełnej nowej implementacji zmieniłby dowód, że adaptery pozwalają szybko wykorzystać istotne dla pierwszego zakresu istniejące ekrany i usługi przy zachowaniu nowej semantyki czasu, źródeł oraz korekt. Obecna inspekcja wskazuje silniejsze dopasowanie starego UI do starego modelu niż do nowego celu. Nie dowodzi, że refaktor jest niemożliwy. Decyzję o **zmianie języka** powinny uzasadnić niezależnie doświadczenie implementacji adapterów, dystrybucja i pomiary równoważnego obciążenia. Nawet jeśli Python wygra to porównanie, nowa implementacja z nowymi granicami pozostaje zasadnym wyborem.

### Self-review

- Nie przyznano nowemu stosowi przewagi wydajności bez pomiaru. Zmiana SQL, indeksów i modelu raportu jest oddzielona od języka.
- Nie przeceniono istniejących testów: przypadki modeli/migracji nie pokrywają capture, IPC, sync, uśpienia i wieloźródłowej semantyki.
- Nie narzucono kosztu zachowania starej aplikacji, zgodności API, migracji ani feature parity.
- Pełny rewrite nie został utożsamiony z ignorowaniem doświadczeń. Różni się od selektywnej przebudowy obowiązkiem utrzymania starego kodu przez adaptery, a nie możliwością korzystania z wiedzy i historii projektu.
- Nie potraktowano braku weba jako argumentu przeciw webowym technologiom UI; ponowne użycie w webie jest opcją, nie obecnym uzasadnieniem.
- Nie uznano wspólnej biblioteki za powód współdzielenia ORM lub całej aplikacji między klientem i serwerem.
- Ujęto dystrybucję, aktualizacje, granice dostępu i zależne od modułu licencje jako realny koszt komercyjnego produktu.
