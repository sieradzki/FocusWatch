# FocusWatch: rozwiązania porównawcze i wnioski produktowe

Stan źródeł: **27 września 2026**. Dokument uzupełnia ocenę technologii i system design; nie jest rankingiem skuteczności produktów. Zbadano oficjalną dokumentację, polityki i wybrane źródła ActivityWatch. Nie zakładano kont, nie uruchamiano prób komercyjnych produktów i nie przekazywano im danych użytkownika.

## Zakres i standard dowodów

Rize i ActivityWatch były przykładami, nie granicą rynku. Porównanie obejmuje sześć narzędzi pomiarowych oraz pięć rozwiązań sąsiednich: blokery, planowanie i pamięć kontekstu. Nie są to produkty wzajemnie zastępowalne.

- **Udokumentowane zachowanie**: opis producenta wyjaśnia mechanizm; nadal nie jest to nasz pomiar niezawodności ani jakości.
- **Sprawdzone w kodzie**: podano repozytorium i gałąź; `master` nie oznacza automatycznie bieżącego wydania.
- **Hipoteza dla FocusWatch**: proponowana wartość, wymagająca walidacji z użytkownikiem.
- **Nieustalone**: brak danych w sprawdzonych źródłach; nie oznacza braku funkcji.

Zebrane źródła nie dostarczają porównywalnych testów wieloletniej historii, baterii, trafności rekomendacji i kosztu utrzymania. Deklaracji „AI”, „privacy-first”, niskiego CPU czy wzrostu produktywności nie traktujemy jako wyników własnych badań. Dobór obejmuje mechanizmy przydatne dla FocusWatch, nie pełny przegląd wszystkich produktów na rynku.

## Narzędzia porównywane w zakresie pomiaru

| Produkt | Sprawdzone mechanizmy | Znaczenie dla FocusWatch i ograniczenia porównania |
| --- | --- | --- |
| **ActivityWatch** | Niezależne watchery → lokalny serwer → UI. Bucket identyfikuje źródło/host; zdarzenie zawiera czas, długość i dane. Heartbeaty scalają sąsiednie identyczne obserwacje. Typy obejmują okno, AFK, kartę z `audible` oraz edytor. | Dobry wzorzec oddzielania pomiaru od interpretacji i oszczędnego zapisu. Nie wymusza jednego rodzaju obserwacji. Źródła: [architektura](https://docs.activitywatch.net/en/latest/architecture.html), [model](https://docs.activitywatch.net/en/latest/buckets-and-events.html). |
| **Rize** | Domyślnie aktywne okno: aplikacja, tytuł, URL i czas. Reguły, korekty, integracje projektowe, raporty CSV/PDF. FAQ deklaruje kilka komputerów bez podwójnego naliczania. | Multi-device i ręczne korekty istnieją już w innych produktach; nie wystarczą jako samodzielny wyróżnik. Publiczne źródła nie ujawniają algorytmu łączenia ani schematu backendu. Źródła: [tracking](https://docs.rize.io/automatic-tracking/tracking-overview), [FAQ](https://www.rize.io/guides/faq), [raporty](https://www.rize.io/guides/reports-and-exports). |
| **RescueTime** | Jedna aktywna aplikacja/witryna, wysyłanie na serwer co kilka minut, krótkie okresy offline. Dokumentacja wprost dopuszcza sumę większą niż czas zegarowy przy równoczesnej pracy na dwóch komputerach; brak rozbicia na konkretny komputer. | Trzeba odróżnić sumę czasu urządzeń od czasu osoby. Pięć edytowalnych poziomów produktywności i kontekst subaktywności istnieją już w produkcie. Źródła: [mechanizm](https://help.rescuetime.com/article/245-how-rescuetime-works), [klasyfikacja](https://help.rescuetime.com/article/456-managing-your-activities-categories-and-productivity-levels). |
| **ManicTime** | Windows może działać samodzielnie; Linux jest trackerem z raportami w Cloud/własnym Server. Offline zbiera i później wysyła dane. Pomiar aplikacji dotyczy foreground. Osobne osie pokazują obecność, aplikacje, dokumenty i tagi. | Wspólna marka cross-platform nie oznacza równoważnych klientów. Źródła: [Linux](https://docs.manictime.com/linux/installation), [serwer](https://docs.manictime.com/server/on-premise-installation/faq/quick-installation), [oś dnia](https://docs.manictime.com/win-client/overview). |
| **Timing** | Tracker macOS zapisuje foreground, tytuł i ścieżkę/URL. Opcjonalny sync pokazuje osobne urządzenia; ręczne wpisy mogą usuwać podwójne naliczanie równoczesnej aktywności. | Rozróżnienie źródła i przypisania do projektu jest użyteczne. Nie udowodniono automatycznego rozstrzygania wszystkich konfliktów. Źródła: [FAQ](https://timingapp.com/help/faq), [sync](https://timingapp.com/help/sync), [time entries](https://timingapp.com/help/time-entries). |
| **Memtime** | Historia pomiaru pozostaje lokalna na każdym urządzeniu i nie synchronizuje się automatycznie. Wspólne projekty/zadania i wyeksportowane wpisy czasu mogą przepływać przez integracje; raporty można scalać ręcznie. | Lokalna historia i wspólne timesheety to różne funkcje. FocusWatch potrzebuje świadomie zaprojektowanej wspólnej historii obserwacji. Źródła: [wiele urządzeń](https://knowledgebase.memtime.com/en/using-memtime-on-multiple-devices), [przetwarzanie danych](https://www.memtime.com/security). |

### Równoległość: istotniejsza od liczby wspieranych urządzeń

W przejrzanym `master` ActivityWatch `canonicalMultideviceEvents` korzysta z `union_no_overlap` z pierwszeństwem według kolejności hostów. `browserEvents` przycina dane kart do foreground przeglądarki; dopiero tak przygotowane `audible` wpływa na AFK. To analiza kodu konkretnej gałęzi, nie test wszystkich wydań ani rozszerzeń ekosystemu. [Kod zapytań](https://github.com/ActivityWatch/aw-webui/blob/master/src/queries.ts)

Z tego wynika konkretne rozróżnienie dla FocusWatch: jedna godzina pracy w VSCode i odtwarzania streamu to **jedna godzina czasu osoby, dwie nakładające się obserwacje oraz nieustalony podział uwagi**. Nie trzeba odrzucać streamu, żeby nie dublować czasu. Stan odtwarzacza, `audible`, widoczność, interakcje i kategoria treści powinny być osobnymi sygnałami. Żaden z nich sam nie dowodzi uważnego oglądania, rozproszenia ani regeneracji.

### Reguły i poprawianie historii: dwa sprawdzone podejścia

**ManicTime** przelicza autotagi z aktualnych reguł, także dla dawnych dni. Użytkownik może utrwalić wynik jako ręczne tagi. Heurystyka `absorb` przypisuje krótkie czynności pomocnicze do otaczającego kontekstu; dokumentacja zaznacza możliwość błędu. **Timing** domyślnie stosuje reguły projektów tylko do nowych obserwacji; ponowne zastosowanie do historii jest osobną operacją. Projekty są rozłączne, ale filtry mogą się nakładać. [ManicTime autotagi](https://docs.manictime.com/win-client/autotagging), [Timing reguły](https://timingapp.com/help/rules)

Wniosek: nie wystarczy mieć „reguły + AI”. Potrzebna jest jawna semantyka zmian: potwierdzona korekta użytkownika, wersja reguły, interpretacja przeliczana oraz raport utrwalony na dany moment. Domyślnego automatycznego przepisywania całej historii nie należy dziedziczyć z obecnego FocusWatch.

### Historia, prywatność i eksport

| Produkt | Udokumentowana granica | Wniosek |
| --- | --- | --- |
| ActivityWatch | SQLite lokalnie; `aw-sync` beta używa osobnych baz pośrednich i zewnętrznego transportu plików. Dokumentacja ostrzega o braku uwierzytelnienia lokalnego API. | Lokalność nie zastępuje kontroli dostępu; samodzielne ustawianie synchronizatora podnosi próg wejścia. [Sync](https://docs.activitywatch.net/en/latest/syncing.html), [security](https://docs.activitywatch.net/en/latest/security.html) |
| Rize | Usuwanie surowych metadanych może zachować projekty/metryki. Infrastruktura GCP w USA, TLS i szyfrowanie spoczynkowe kluczami Google według producenta. | Rozdzielenie retencji szczegółów i podsumowań jest użyteczne; opis szyfrowania nie oznacza E2EE. [Tracking](https://docs.rize.io/automatic-tracking/tracking-overview), [security](https://rize.io/security) |
| RescueTime | Płatne raporty zapewniają widoczność historii przez okres subskrypcji i CSV. Bezpłatna historia starsza niż 15 miesięcy jest usuwana, a widok obejmuje dwa tygodnie. | Retencja, prawo odczytu i eksport to trzy różne decyzje produktu. [Raporty](https://help.rescuetime.com/article/96-premium-reports), [polityka](https://help.rescuetime.com/article/163-rescuetimes-privacy-policy) |
| ManicTime | Core jest źródłem do odtworzenia Reports. Retencja usuwa automatyczne dane także u klientów przy synchronizacji, zachowując ręczne tagi. Kopie i eksporty wymagają odrębnych zasad. | Odtwarzalne projekcje i propagacja usunięcia obejmują urządzenia offline. [Bazy](https://docs.manictime.com/server/on-premise-installation/setup/before-installing), [retencja](https://docs.manictime.com/server/administration/data-retention) |
| Timing | Bez Sync obserwacje nie są wysyłane do dostawcy. Sync jest opcjonalny; polityka opisuje szyfrowanie transportu i przechowywania, ale nie potwierdza E2EE. Raporty eksportują m.in. CSV/JSON. | Tryb lokalny i tryb z chmurą wymagają osobnych, czytelnych przepływów. [Polityka](https://timingapp.com/privacy?lang=en), [eksport](https://timingapp.com/help/reports) |
| Memtime | Pomiar lokalny; konto/licencja i część autoryzacji integracji używają chmury. Wsparcie może otrzymać bazę wyłącznie po dobrowolnym przekazaniu przez użytkownika. | „Local-first” trzeba rozbić na capture, auth, integracje, diagnostykę i kopie. [Przetwarzanie](https://www.memtime.com/security) |

Rize ma niespójne sformułowania dokumentacji: FAQ twierdzi kategorycznie, że nie odczytuje zawartości, podczas gdy aktualna polityka i osobny przewodnik opisują opcjonalne Screen Text/OCR z retencją 30 dni. W porównaniu obowiązuje precyzyjne „metadata domyślnie, opcjonalny odczyt treści”, nie „nigdy treści”. [Polityka](https://rize.io/privacy-policy), [OCR](https://www.rize.io/guides/privacy-and-security)

## Produkty sąsiednie: blokowanie, planowanie, pamięć kontekstu

| Produkt i rola | Udokumentowany mechanizm | Co przenieść jako zasadę; czego nie zakładać |
| --- | --- | --- |
| **Cold Turkey — blokowanie** | Windows/macOS, uprawnienia administratora i rozszerzenia przeglądarkowe. Blokady można zamknąć na czas, hasłem lub wyzwaniem tekstowym. Brak Linux/mobile w przewodniku. | Blokowanie to osobny adapter systemowy z własnym modelem uprawnień i obejść. Cross-platform UI nie daje równoważnej siły blokady. Nie obiecujemy „niemożliwe do obejścia”. [Przewodnik](https://getcoldturkey.com/support/user-guide/) |
| **Freedom — blokowanie wielu urządzeń** | Locked Mode utrudnia przerwanie sesji; na iOS nadal istnieje ścieżka odebrania uprawnienia Screen Time. Windows potrzebuje połączenia, aby odebrać start zaplanowanej sesji; przerwa w sesji jest lokalna dla urządzenia. | Wspólny zamiar i lokalnie egzekwowany stan wymagają określenia offline, opóźnień i manualnego override. [Locked Mode](https://support.freedom.to/en/articles/1802927-locked-mode), [Windows](https://support.freedom.to/en/articles/4529922-ensuring-freedom-is-active-on-windows), [przerwy](https://support.freedom.to/en/articles/15170482-how-to-use-session-breaks) |
| **Reclaim 2.0 — planowanie kalendarza** | Agent zarządza elastycznymi nawykami, blokami focus i buforami według konfiguracji. Zmiany AI chat/MCP trafiają do Preview Mode. W 2.0 zadania są sugerowane podczas focus, a nie każde automatycznie planowane. | Plan nie jest dowodem wykonania. Przydatna granica: intencja → propozycja → przegląd skutków → zastosowanie; autonomię można przyznawać per rodzaj działania. Nie przenosimy bez weryfikacji opisów starszego Reclaim. [2.0 overview](https://help.reclaim.ai/en/articles/14846468-reclaim-ai-2-0-overview), [FAQ](https://help.reclaim.ai/en/articles/15280604-reclaim-2-0-faq) |
| **Screenpipe — zbieranie i wyszukiwanie kontekstu** | Whitepaper opisuje Rust/Tauri, lokalne SQLite/FTS5 i pliki mediów, przechwytywanie wyzwalane zdarzeniami, OCR/accessibility, deduplikację, lokalne wyszukiwanie oraz opcjonalne ścieżki cloud AI/sync. | Bogaty kontekst ma odrębny koszt przechowywania, uprawnień i ochrony treści. To przykład wykonalności stosu, nie pomiar jego przewagi. Screenshoty/audio są poza pierwszym zakresem FocusWatch. [Architektura producenta](https://screenpipe.com/security/architecture) |
| **Microsoft Recall — pamięć aktywności ekranu** | Lokalna analiza zapisanych obrazów, opcjonalne przechwytywanie, filtrowanie i kontrola usuwania. Ochrona wiąże się z zabezpieczeniami urządzenia, TPM/Windows Hello i izolacją. Retencja ma limit czasu i miejsca. | Bezpieczna historia wymaga także odzyskiwania, rotacji urządzeń i usuwania pochodnych kopii. Recall nie jest dowodem działania pomiaru uwagi ani planera. [Prywatność](https://support.microsoft.com/en-us/windows/privacy/privacy-and-control-over-your-recall-experience), [retencja](https://support.microsoft.com/en-us/windows/ai/ai-features/manage-your-recall-snapshots-and-disk-space) |

Whitepaper Screenpipe opisuje wszystkie sekrety jako lokalne. Nowsza polityka prywatności z 24.09.2026 wskazuje serwerowe tokeny Calendar oraz zewnętrzny Composio dla autoryzacji Gmail/Zoom. To **niespójność zakresu deklaracji**, nie samodzielnie potwierdzona luka bezpieczeństwa. Nie przenosimy twierdzenia „wszystko zostaje lokalnie” na opcjonalne konektory. [Polityka](https://screenpipe.com/privacy)

Recall dokumentuje eksport w EOG jako zaszyfrowane archiwum obrazów i JSON oraz osobny kod eksportu; reset lokalnej historii nie usuwa wcześniejszych eksportów. Jest to dobry przypadek testowy granic usuwania i odzyskiwania, nie propozycja narzucenia identycznego mechanizmu FocusWatch. [Eksport Recall](https://support.microsoft.com/en-us/windows/ai/ai-features/export-recall-snapshots)

## Konkretne rekomendacje dla projektu

1. **Pierwszy produkt: sprawdzalne pomiary i raporty bez LLM.** Zakres pomiaru obejmuje już nakładające się metadane systemu i przeglądarki; nie ograniczamy schematu do jednego foreground. Wyłączony LLM nie może wyłączać podstawowej wartości.
2. **Osobne warstwy obserwacji, interpretacji i korekt.** Reguły są pełnoprawnym mechanizmem; zachowujemy pochodzenie i możliwość przeliczenia. Nowy model nie przechowuje trwałego osądu „produktywne/nieproduktywne” jako faktu źródłowego.
3. **Dwa rodzaje raportu czasu.** Czas osoby bez dublowania oraz współwystępujące konteksty/urządzenia. Użytkownik może zejść z agregatu do źródeł i zobaczyć braki lub niepewność.
4. **Wieloletnia historia jako zarządzany zbiór.** Oddzielamy surowe dane od odbudowywalnych projekcji, retencję od limitu raportowania, a synchronizację od backupu. Usunięcia mają dotrzeć do klientów offline i wyników pochodnych.
5. **Spójny produkt Windows/Linux.** Pełne lokalne raporty na obu systemach są konkretną różnicą względem ograniczonego klienta Linux ManicTime i braku wspieranego Linuxa w aktualnej liście RescueTime. Nie jest to twierdzenie o całym rynku. [RescueTime platformy](https://help.rescuetime.com/article/56-what-operating-systems-does-rescuetime-support)
6. **Web nie jest wymaganiem pierwszej wersji.** Przykład Timing uzasadnia opcjonalny dostęp do raportu/timera bez instalacji, ale nie dowodzi potrzeby osobnego pełnego klienta dla FocusWatch. Wspólny React może służyć tylko desktopowi; warstwa API pozostaje niezależna od decyzji o webie. [Timing web](https://timingapp.com/help/web)
7. **Blokowanie i planowanie później, na osobnych granicach.** Zarejestrowany kontekst nie uruchamia samowolnie systemowej blokady. Polityka działania, dostępne możliwości OS i decyzja użytkownika to oddzielne dane.

## Hipotezy wyróżnienia i próby, które mogą je obalić

| Hipoteza | Minimalne sprawdzenie | Co obala lub osłabia hipotezę |
| --- | --- | --- |
| Równoległy kontekst daje lepszy obraz dnia niż foreground | Scenariusze: edytor + stream, spotkanie + dokument, telefon + komputer; porównać raport z ręcznie opisanym przebiegiem | Rejestrowanie dodatkowych sygnałów nie zmienia interpretacji lub tworzy więcej szumu niż wartości |
| Jasne źródła i reguły zwiększają zaufanie | Użytkownik potrafi wyjaśnić skąd wynik i poprawić błędne przypisanie bez znajomości modelu | Korekty są pracochłonne, odtwarzane błędy wracają, raporty zmieniają się bez zrozumiałej przyczyny |
| Prywatna wspólna historia jest wystarczającym wyróżnikiem | Porównać rzeczywistą konfigurację, odzyskiwanie i używanie dwóch urządzeń z istniejącymi produktami | Użytkownicy nie odczuwają różnicy lub koszt/obsługa kluczy niweluje korzyść |
| Kontekst rozrywki może pomagać długoterminowo | Zachować sygnały i dobrowolne informacje o samopoczuciu/rezultatach; badać wzorce bez stwierdzania przyczynowości | Efekty są niestabilne, nie da się oddzielić zmęczenia i trudności zadania albo pomiar jest zbyt intruzywny |

Nie stwierdzono unikalności kombinacji na całym rynku ani wpływu streamów na burnout. Raport wyznacza konkretne mechanizmy do zaprojektowania i sprawdzenia; nie stanowi dowodu skuteczności przyszłego companiona.
