# FocusWatch: architektura referencyjna po doprecyzowaniu modelu płatnego

Data: **03.10.2026**. Status: rekomendacja inżynierska i zakres prototypu, nie wdrożony produkt ani zgoda użytkownika na wszystkie technologie. Baza dokumentacji: `cdd122389904f7449814179a989f53f0a176cb49`. [Brief](../PROJECT_BRIEF.md), [decyzje](DECISIONS.md), [plan](../IMPLEMENTATION_PLAN.md).

## 1. Co zmieniają nowe wymagania

FocusWatch jest z założenia płatny i ma być rozsądnie wyceniony. Nie rozstrzygnięto subskrypcji, licencji jednorazowej, trialu ani konkretnej ceny. Dotychczasowa znajomość stosu przez właściciela ma wagę zero w wyborze; rozwój uwzględnia agentów AI.

Nie wynika z tego zerowy koszt implementacji lub nadzoru nad agentami. Nadal trzeba oceniać sprawdzalność zmian, diagnostykę, zależności, testy platformowe, bezpieczeństwo i utrzymanie wydań. Nie ma tu pomiaru dowodzącego, że agenci są lepsi w Rust niż w C# albo odwrotnie.

Płatny model usuwa freemium jako bazowe założenie ekonomiczne. Nie usuwa kosztów stałych, obsługi klientów, wycofanych kont z archiwum ani intensywnego użycia. Rozsądna cena nie jest licencją na minimalizowanie rachunku infrastruktury kosztem niezawodności.

## 2. Jeden wariant do realizacji, nie sześć równoległych produktów

| Warstwa | Rekomendacja | Uzasadnienie i granica |
| --- | --- | --- |
| Pomiar | Agent sesji użytkownika, oddzielony od UI | Awaria/zamknięcie raportu nie kończy zapisu; nie robić collectora Windows Service |
| Rdzeń | Rust; mała czysta domena i adaptery | Kontrola granic natywnych i zasobów; to wybór inżynierski, nie wynik benchmarku języków |
| Lokalny zapis | SQLite WAL, rusqlite, jeden kontrolowany writer, atomowy outbox | Ograniczone zapytania i projekcje; brak potrzeby ładowania lat danych do RAM [S03] |
| Raporty | React + TypeScript w Electron, statyczny frontend | Kontrolowany dostarczany renderer i oddzielenie kosztu otwartego UI od agenta [S01] |
| IPC | Ograniczony protokół między agentem a uprzywilejowaną częścią UI | Renderer bez dostępu do bazy, sekretów i shell; walidacja danych także przy wspólnych typach [S01] |
| Przeglądarka | Oddzielne rozszerzenie i native-messaging host | Źródło nie zarządza życiem agenta; foreground i media są osobnymi sygnałami |
| Sync | Obserwacje, edycje i kontekst o różnych gwarancjach | Trwała historia/rewizje osobno od aktualnego snapshotu; bez globalnego CRDT dla wszystkiego |
| AI | Opcjonalny worker z kontrolowanymi narzędziami | Nie oblicza podstawowych sum zamiast SQL i nie przyznaje uprawnień |
| Blokowanie | Osobny adapter/helper z minimalnymi uprawnieniami | Nie podnosić uprawnień całego agenta lub UI |

To rekomendacja na podstawie wymagań oraz [historycznych badań](../research/2026-09/README.md), a nie stwierdzenie, że ten produkt jest już przetestowany.

### Dlaczego nie zmieniamy teraz stosu na inny

**Rust kontra Python/Go/C#/C++:** wybór dotyczy długo działającego natywnego collectora, a nie tego, który język wykona SQL nad milionami rekordów. Rust jest wariantem referencyjnym dla kontroli pamięci i granic adapterów. Python i C# pozostają technicznie wykonalne. C++ nie daje tu wykazanej korzyści uzasadniającej przejęcie większej odpowiedzialności za ręczne bezpieczeństwo pamięci; Go nie dostaje osobnego serwera tylko z powodu popularności. Nie ma porównania pełnych implementacji, więc nie przyznajemy fałszywych punktów wydajności.

**Electron kontra Tauri:** Electron dostarcza runtime, a Tauri na Windows używa WebView2 i na Linux WebKitGTK. To koszt aktualizacji własnego runtime kontra różnice systemowych silników, nie oczywiste zwycięstwo jednej technologii [S01–S02]. Wrześniowy test był Xvfb/Canvas bez GPU. Nie dyskwalifikuje Tauri i nie wystarcza do odbioru Electron. Najbliższy test porównawczy zachowuje ten sam frontend.

**Qt Quick i Avalonia:** Qt Quick był najlżejszy w historycznej próbie; to poważna alternatywa przy twardym priorytecie zasobów. C#/Avalonia jest spójną alternatywą całego produktu, ale nie dostaje premii za doświadczenie właściciela. Aktualna macierz Avalonia ma różne poziomy wsparcia, w tym Arch jako Tier 3; to ryzyko wsparcia, nie dowód niedziałania [S04]. Wszystkie warianty wymagają testu docelowego Arch/dwm.

**Flutter/Compose/native UI:** wspólny interfejs mobilny nie jest obecnym wymaganiem i nie usuwa adapterów OS. Nie dokładamy kolejnego modelu UI dla hipotetycznej oszczędności w przyszłości. Ten argument nie wyklucza osobnych companionów mobilnych.

**React kontra Angular/Svelte/Vue:** nie wykazano przewagi renderowania Reacta. Wybieramy jeden istniejący kierunek raportowego frontendu do prototypu; nie dokładamy równoległego porównania frameworków bez konkretnego problemu. Dotychczasowa znajomość Angulara nie jest argumentem ani za, ani przeciw niemu. Dominujące ryzyka to query API, ograniczenie liczby elementów i zachowanie widoku.

## 3. Granice chroniące przed kolejnym rewrite

```text
OS + browser -> agent -> SQLite/outbox/projections
                         |               |
                    query API       history sync
                         |               |
                    Electron UI    optional cloud
                         |
                  correction commands

rules / optional AI -> policy -> notification / restricted helper
```

Agent jest właścicielem lokalnego zapisu. Domena nie zależy od Electron, Cloudflare, Win32, ORM ani modelu AI. Nie wprowadzamy mikroserwisu na każdy moduł. Oddzielne procesy uzasadniają cykl życia, uprawnienia albo ciężka inferencja.

Najdroższe do zmiany są semantyka danych, klucze i prywatność, korekty, format archiwum, protokół starych klientów i uprawnienia. Wspólny język nie zastępuje wersjonowania. Przenośność obejmuje eksport/odtworzenie danych i tożsamości, nie tylko uruchomienie kontenera.

Unia obserwacji to pokrycie, nie automatycznie czas aktywności człowieka. Stream po odejściu od komputera nie przedłuża z definicji pracy. Sumy z osobnych urządzeń nie pozwalają odtworzyć nakładania; potrzebny jest wystarczający opis przedziałów. Korekta musi przetrwać przebudowę projekcji.

## 4. Chmura: rekomendacja z jednym jawnym warunkiem

**Rekomenduję lokalną analitykę i E2EE historii oraz osobne, świadome udostępnianie danych AI.** Dla tego modelu konfiguracją referencyjną jest **Workers/TypeScript + R2 + Durable Objects na konto**, z ograniczonymi metadanymi kontrolnymi. Nie ma potrzeby odczytywalnego wiersza PostgreSQL dla każdej obserwacji.

Warunek: to nie zapewnia serwerowi swobodnej analizy całej prywatnej historii przy wyłączonych urządzeniach. Do takiego celu potrzeba udostępnionych podsumowań albo innej granicy prywatności. E2EE pozostaje rekomendacją, nie zatwierdzoną obietnicą użytkownika.

Cloudflare jest kandydatem ze względu na dopasowanie relaya i storage do blind-sync, nie z powodu darmowego planu. Hibernujące DO mogą zachować WebSockety bez opłat za bezczynny czas obiektu; stan trzeba umieć odbudować [S05–S06]. Cloud Run obsługuje WebSockety, ale otwarte połączenie utrzymuje instancję jako aktywną; timeout i ponowne połączenia należą do projektu [S07]. To różne mechanizmy, nie pełny ranking kosztu dostawców.

Jeżeli wymagany okaże się odczyt historii przez serwer, rekomendacja zmienia się na **jeden modułowy serwis OCI/Axum/SQLx + PostgreSQL + obiekty**. GCP pozostaje poważnym kandydatem; cena oraz region, HA, auth i odzyskanie muszą zostać sprawdzone dla całej usługi. Rust w collectorze nie narzuca stosu chmury.

Nie wdrażamy teraz dwóch pełnych wariantów sync. P0–P2 nie potrzebują żadnego z nich. Przed prawdziwym uploadem trzeba wybrać jedną granicę prywatności, odzyskiwanie kluczy, usuwanie i region.

## 5. Koszt: właściwa skala i brak przedwczesnego komplikowania

Historyczny przykład: 1000 kont, dwa aktywne urządzenia po 8 h/dzień, minuta między paczkami, 30 dni. Daje 28,8 mln PUT/miesiąc, czyli w obecnym cenniku R2 około **126 USD dla całej grupy / 0,126 USD na konto za same zapisy**, po uwzględnieniu puli 1 mln oraz zaokrąglenia jednostek rozliczeniowych [S08]. Jest to obliczenie scenariuszowe, nie wynik wdrożenia ani pełny koszt usługi.

Przy 100 bajtach skompresowanego payloadu na obserwację i 3840 obserwacjach dziennie pięć lat to 700,8 MB payloadu na konto. Kompresja jest założeniem. Nie obejmuje nagłówków, indeksów, kopii i AI. Przeliczeń walutowych i cen detalicznych nie utrwalamy jako wymagań.

Nie przyjmujemy nowego bufora trwałego tylko po to, żeby ograniczyć każdy PUT. Pierwszy wariant powinien mieć prosty, poprawny upload i niezależny aktualny kontekst. Interwał historii porównać w 60/300 s z kosztem i utratą jeszcze niewysłanych danych. To nie narzuca opóźnienia lokalnego pomiaru ani realtime.

Długoterminowo małe paczki wymagają łączenia i manifestów. Przy E2EE można łączyć zaszyfrowane fragmenty, ale nie uzyskuje się w ten sposób kompresji jawnych danych. ACK wymaga trwałego payloadu i odnajdywalnego manifestu. Usunięcie danych nie może być cofnięte przez dawno odłączone urządzenie.

**Pełny rachunek przed uruchomieniem sprzedaży** obejmuje API, koordynację/realtime, operacje i storage, odczyty, auth, kopie/odtworzenie, logi, egress gdzie naliczany i AI. Sprzedaż, obsługa i rozwój mają osobny koszt. Scenariusze: 10/100/1000/10000 płacących, normalne i intensywne użycie, różny wiek historii. Koszt stały nie znika przy małej skali. Składnik niepoliczony nie jest zerem.

## 6. Co płatność wnosi do architektury

Konto, urządzenie, uprawnienie do produktu i klucz historii mają osobne tożsamości. Błąd płatności lub chwilowy brak sieci nie powinien usuwać historii ani uniemożliwiać jej bezpiecznego odzyskania/eksportu. To rekomendacja zasad produktu; zachowanie collectora po wygaśnięciu i długość działania offline pozostają do wybrania.

Dla modelu odnawianego online rozważyć podpisane uprawnienie offline, z okresem ważności i kontrolowanym odnowieniem. Nie budować skomplikowanego DRM przed użytecznym raportem. Ograniczenia chmurowe egzekwować także po stronie serwera. Klient nie otrzymuje operatorowych sekretów płatności ani kluczy dostawcy AI.

Lokalne działanie i opcjonalny sync nie oznaczają darmowego lokalnego planu. Testy syntetyczne nie potrzebują prawdziwego operatora płatności. Przy integracji zdarzenia płatności muszą być idempotentne, a ich kolejność nie może cofać nowszego uprawnienia.

## 7. Następny krok i warunki zmiany

Następny zakres wykonawczy to **P0 w planie: kontrakt, fixtures i szkielet lokalnego przekroju**. Potem jeden rzeczywisty pomiar, SQLite, raport i korekta na Windows oraz Arch/dwm. Przyjęte kryteria jakości sprawdzamy na produkcie, nie ponownym rankingu wszystkich języków.

Jeżeli test ujawni konkretny problem UI, najpierw odróżnić query/rendering, liczbę elementów, lifecycle i bibliotekę od problemu powłoki. Następnie porównać najbliższego kandydata na tej samej pracy. Nie przesuwać budżetu, żeby zaliczyć preferowany framework. Twarde progi CPU/RAM/baterii i profil sprzętu nie zostały jeszcze uzgodnione; pomiary bez nich nie są certyfikatem przyjętego SLA.

**Nie wykonano w tym etapie nowego prototypu, benchmarku, pełnego TCO ani wdrożenia.** Nowa macierz opisuje testy do wykonania. Przy braku Windows/GPU dany wynik pozostaje niewykonany, nie zaliczony.

## Źródła pierwotne sprawdzone 03.10.2026

[S01] Electron: [model procesów](https://www.electronjs.org/docs/latest/tutorial/process-model), [bezpieczeństwo](https://www.electronjs.org/docs/latest/tutorial/security), [context isolation](https://www.electronjs.org/docs/latest/tutorial/context-isolation).

[S02] Tauri: [wersje silników WebView](https://v2.tauri.app/reference/webview-versions/).

[S03] SQLite: [WAL, współbieżność i checkpoint](https://www.sqlite.org/wal.html). Rzeczywisty silnik dołączony do wydania musi zawierać aktualne poprawki; manifest wrappera nie dowodzi wersji SQLite.

[S04] Avalonia: [macierz wspieranych platform](https://docs.avaloniaui.net/docs/supported-platforms).

[S05] Cloudflare: [WebSocket Hibernation](https://developers.cloudflare.com/durable-objects/best-practices/websockets/).

[S06] Cloudflare: [cennik Durable Objects](https://developers.cloudflare.com/durable-objects/platform/pricing/).

[S07] Google Cloud: [WebSockety w Cloud Run](https://docs.cloud.google.com/run/docs/triggering/websockets).

[S08] Cloudflare: [cennik R2](https://developers.cloudflare.com/r2/pricing/), odczytana strona z aktualizacją 01.10.2026. Koszty Workers i DO są osobne.

Wnioski wyboru stosu są oceną dopasowania do briefu. Dokumentacja dostawcy potwierdza mechanizm, nie wydajność przyszłego FocusWatch. Historyczne benchmarki i ich ograniczenia: [badanie z 2026-09](../research/2026-09/README.md).
