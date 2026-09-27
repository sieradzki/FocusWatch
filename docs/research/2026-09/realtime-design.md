# FocusWatch: bieżący kontekst i synchronizacja historii

**Rekomendacja: dwa niezależne kanały — trwała historia w paczkach oraz natychmiastowe publikowanie zmian bieżącego kontekstu.** Minutowy upload nie zapewnia reakcji między urządzeniami w kilka sekund. Pierwszy przekrój powinien obejmować lokalny silnik reguł i WebSocket z jednym połączeniem na urządzenie, współdzielonym przez jego źródła.

Stan dokumentacji: 27.09.2026. **Proponowane cele p95: lokalne udostępnienie zmiany regułom <1 s; dostarczenie jej drugiemu aktywnemu urządzeniu <5 s**, przy działającej sieci i uruchomionych klientach. To cele do zmierzenia, nie uzyskane wyniki ani obietnica czasu inferencji LLM. Opisana niżej próba transportu używa localhost; próby SQLite i synchronizacji nie testują sieci.

## Kontrakt dwóch kanałów

- **Historia:** najpierw trwały zapis lokalny z outbox; upload np. co 60 s, ponawiany do trwałego ACK. Późniejsza rekonstrukcja raportu nie zależy od dostępności kanału bieżącego.
- **Kontekst:** mały snapshot po zmianie aplikacji, obecności lub mediów; można scalać zmiany przez najwyżej 100–250 ms. Odbiór snapshotu nie jest ACK historii. Po reconnect wysyłamy świeży stan, nie kolejkę dawnych snapshotów.
- **Wersje:** klucz urządzenie/źródło, zatwierdzona sesja producenta i rosnący licznik. Stara sesja zostaje odcięta; spóźniona niższa wersja nie zastępuje nowszej. Zegar ścienny urządzenia nie rozstrzyga kolejności.
- **Świeżość:** propozycja heartbeat co 15 s i TTL 45 s; jawne rozłączenie unieważnia stan wcześniej. Po TTL stan jest „nieznany”, nie „nieaktywny”. Heartbeat odświeża tylko faktycznie odczytane źródła. Zapisujemy wiek i niepewność czasu; transportowe ping nie dowodzi aktualnego odczytu aplikacji.

Nie wybieramy jednego globalnego foreground. VSCode na komputerze i stream na innym urządzeniu pozostają równoległymi faktami. Osobny wybór urządzenia wyświetlającego sugestię — ręczny lub przez krótką dzierżawę koordynowaną przez serwer — zapobiega podwójnym powiadomieniom; nie oznacza ustalenia „gdzie jest uwaga”. Offline lokalne reguły nadal działają, ze zdalnym kontekstem oznaczonym jako nieaktualny. Szyfrowany relay może przekazywać treść klientom bez jej interpretacji; klucze i uprawnienia pozostają osobnym kontraktem.

## Transport i wdrożenie

| Wariant | Konsekwencja |
| --- | --- |
| Mały POST po zmianie + SSE do odbiorcy | Prosty rozdział kierunków, ale SSE pozostaje otwartym żądaniem; nie usuwa kosztu długiego połączenia. [SSE](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) |
| WebSocket | Jedno dwukierunkowe połączenie, snapshot po reconnect, ograniczony bufor najnowszych stanów. Potrzebuje uwierzytelnienia, limitów i kontroli wolnych odbiorców |
| POST + polling | Brak stałego strumienia, ale dużo odczytów bez zmian. Polling co 5 s sam zużywa prawie cały budżet opóźnienia; do celu <5 s potrzebny krótszy interwał i pomiar |

**Cloud Run:** WebSocket ma timeout do 60 minut, maksymalnie 1000 współbieżnych połączeń na instancję, a otwarte połączenie utrzymuje ją jako aktywną i rozliczaną. Reconnect i synchronizacja między instancjami należą do aplikacji; session affinity nie zapewnia wspólnego procesu dla wszystkich urządzeń konta. Limit platformy nie dowodzi pojemności naszego kodu. [Dokumentacja WebSocket](https://docs.cloud.google.com/run/docs/triggering/websockets)

**Scaleway Containers:** dokumentuje maksymalnie 80 współbieżnych żądań na instancję, max-scale 200 i timeout HTTP do 60 minut. CPU/RAM rozlicza według przydziału razy czas działania; FAQ deklaruje darmowy ingress/egress. W przeczytanej dokumentacji nie znaleziono jednoznacznego potwierdzenia WebSocket upgrade i jego zachowania przy bezczynności; sama obsługa HTTP/1.1 nie wystarcza jako dowód. Przed wyborem tego kanału potrzebny jest test wdrożenia. [Limity](https://www.scaleway.com/en/docs/serverless-containers/reference-content/containers-limitations/), [billing i protokoły](https://www.scaleway.com/en/docs/serverless-containers/faq/)

**Cloudflare Workers + Durable Objects:** hibernacja pozostawia klientów WebSocket połączonych, bez naliczania czasu bezczynnego obiektu. Stan RAM może zniknąć; potrzebne są attachments/storage lub odbudowanie snapshotów. Zalecany podział to jeden obiekt na konto, nie jeden obiekt dla wszystkich użytkowników. Timery i trwałe połączenia wychodzące mogą uniemożliwić oszczędności. [Hibernacja](https://developers.cloudflare.com/durable-objects/best-practices/websockets/)

## Fan-out między instancjami

Natywny relay nie może opierać poprawności na RAM jednej instancji. Konkretny wariant początkowy: mała tabela PostgreSQL `latest_state` oraz trwała rewizja konta aktualizowane atomowo; równoległe aktualizacje jednego konta muszą zapewniać kolejność rewizji zgodną z commitami. Klient trzyma kursor ostatniego snapshotu. `NOTIFY` emitujemy w tej samej transakcji co zmianę stanu; PostgreSQL doręcza go po commit. Przenosi jedynie sygnał „sprawdź stan”, nie historię ani tytuły okien. W blind-sync tabela przechowuje zaszyfrowaną treść i jawną kopertę wersji.

Każda instancja ma ograniczoną pulę zapytań i jedno dedykowane połączenie `LISTEN`. Po reconnect: najpierw `LISTEN` i commit, potem ograniczony odczyt snapshotów aktywnych kont, następnie obsługa sygnałów. Utrata powiadomienia oznacza resync z tabeli; wyższa rewizja może zastąpić pośrednie stany. PostgreSQL usuwa rejestracje po zakończeniu sesji; `NOTIFY` nie jest trwałą kolejką dla odłączonych odbiorców. [NOTIFY](https://www.postgresql.org/docs/current/sql-notify.html), [LISTEN i wyścig przy starcie](https://www.postgresql.org/docs/current/sql-listen.html)

Koalescencja zmian ogranicza zapisy i fan-out. Ten wariant kosztuje połączenia oraz operacje bazy; alternatywami są płatny managed pub/sub albo DO na konto. Kafka lub Redis nie są konieczne bez wykazanej potrzeby. DO nie powinno otwierać stałego połączenia PostgreSQL wyłącznie w celu realizacji relay — zmieniłoby to założenie hibernacji.

## Wielkość kosztu połączeń

Założenia wyłącznie ilustracyjne: `U` równocześnie aktywnych użytkowników, dwa urządzenia, 8 h dziennie przez 30 dni; `C=2U`, `T=864000 s`. Przy pojemności `K`:

```text
I = ceil(C / K)
czas instancji = I × T
koszt compute = I × T × (vCPU × stawka_CPU + GiB × stawka_RAM)
```

Cloud Run, świadomie wybrany wariant instance-based, przykładowe stawki Tier 1: 0,000018 USD/vCPU-s i 0,000002 USD/GiB-s; przy 1 vCPU + 0,5 GiB daje **16,416 USD/instancję** za takie 8 h/dzień. Poniżej przed free tier, restartami, czasem pozostawania instancji po ruchu, siecią i fan-out. [Cennik](https://cloud.google.com/run/pricing)

| U | Założone K=100: instancje / USD | Założone K=1000: instancje / USD |
| --- | --- | --- |
| 100 | 2 / 32,83 | 1 / 16,42 |
| 1000 | 20 / 328,32 | 2 / 32,83 |
| 10000 | 200 / 3283,20 | 20 / 328,32 |

**K pełnej usługi w chmurze nie zmierzono**, a autoskalowanie może wymagać zapasu. Dla Scaleway nie wolno użyć tych K: przy limicie 80 wychodzi odpowiednio 3/25/250 instancji; ostatni wariant przekracza max-scale pojedynczego zasobu.

Alternatywne rachunki dla `C=2000`:

```text
polling co 5 s: C × T / 5 = 345,6 mln odczytów/miesiąc + publikacje zmian
heartbeat co 15 s: M = C × T / 15 = 115,2 mln wiadomości + zmiany
DO request units = handshakes + M / 20
DO duration GB-s = 0,128 × suma czasu aktywnych handlerów/obiektów
```

Przy założeniu 60000 handshake i 10 ms czasu handlera na wiadomość, sama część heartbeat to 5,82 mln jednostek DO i 147456 GB-s. W obecnym cenniku oznacza 0,75 USD requests i duration w darmowym limicie. **Nie jest to koszt całego relay:** dochodzą Workers, dodatkowe zmiany, storage, uwierzytelnienie i pozostałe usługi; brak hibernacji radykalnie zmienia rachunek. [Zasady i zaokrąglenia DO](https://developers.cloudflare.com/durable-objects/platform/pricing/)

## Lokalna próba pamięci i transportu

27.09.2026 wykonano po jednej próbie minimalnego relay Axum dla **250, 500 i 1000 połączeń**, zawsze dwa urządzenia na konto. Serwer miał jeden wątek Tokio i przypięcie do jednego logicznego CPU; osobny proces Node generował ruch na innym CPU. Bez limitu pamięci cgroup i bez rezerwacji całego hosta. Wersje: Rust 1.96.0, Node 22.22.0, Axum 0.8.9, Tokio 1.53.1. [Wyniki i środowisko](realtime-results.json)

Po początkowym snapshotcie każdego urządzenia: 5 s bezczynności, 15 s równomiernie rozłożonych publikacji reprezentujących okres 30 s oraz pojedynczy burst od 100 różnych nadawców. Każda publikacja trafiała wyłącznie do drugiego urządzenia tego samego konta. Wiadomości zawierały syntetyczne metadane edytora i mediów oraz 256 znaków wypełnienia. Bufory odczytu/zapisu: 4 KiB, maksymalny bufor zapisu 16 KiB, maksymalna wiadomość 2 KiB; jeden slot `watch` najnowszego stanu na odbiorcę.

| Połączenia / konta | Maks. PSS / RSS serwera, MiB | Średni CPU podczas publikacji, % jednego CPU | p95 publikacji, ms | p95 burstu, ms | Poprawnie doręczone |
| --- | --- | --- | --- | --- | --- |
| 250 / 125 | 3,76 / 6,29 | 0,13 | 3,15 | 23,27 | 475/475 |
| 500 / 250 | 5,69 / 8,18 | 0,20 | 2,06 | 7,34 | 850/850 |
| 1000 / 500 | 9,55 / 12,07 | 0,40 | 1,70 | 11,89 | 1600/1600 |

Sprawdzono konto odbiorcy, treść, wersję i brak dodatkowych dostarczeń; w każdym wariancie odrzucono dwie ponownie wysłane wersje — duplikat i starszą. p95 początkowego jednoczesnego zasilenia wszystkich urządzeń wyniosło odpowiednio 37,17/55,26/129,34 ms. Opóźnienie mierzy zegar monotoniczny procesu klientów od wysłania do odbioru przez peer; obejmuje jego scheduling. Nie obejmuje odczytu systemu operacyjnego, WAN ani reguł produktu. Nieporządkowanie wyników wraz z liczbą połączeń nie dowodzi przewagi większej instancji: wykonano pojedyncze krótkie próby.

**Wniosek: 250–500 połączeń nie stanowiło problemu pamięci dla tego małego relay.** To usuwa jedną przesłankę przeciw sprawdzeniu takiej konfiguracji Cloud Run, ale nie potwierdza pojemności pełnej usługi 1 vCPU/512 MiB ani jej rachunku. PSS procesu nie obejmuje pamięci gniazd w jądrze; zasoby klientów są wyłączone. Nie ma TLS, auth, szyfrowania, PostgreSQL, fan-out między instancjami, rzeczywistych źródeł, testów wolnego odbiorcy ani produkcyjnego reconnect. Zerowy odczyt CPU w fazie idle oznacza brak przyrostu przy rozdzielczości 10 ms, nie dowód zerowego kosztu.

Badamy **stałą populację**, a nie pamięć serwisu przy rotacji kont: mapy kont i ostatnich stanów nie mają TTL, globalnego limitu ani usuwania po disconnect. Slot `watch` ogranicza kolejkę odbiorcy; nie ogranicza całej pamięci procesu przy napływie nowych kont. Nie ma też uwierzytelnionego zastępowania sesji. Licznik 127 połączeń w końcowym snapshotcie wariantu 1000 odczytano podczas zamykania klientów; późniejsza niezależna kontrola procesów potwierdziła zakończenie wszystkich własnych procesów serwera i klienta.

Odtworzenie z katalogu repozytorium (Linux, Rust stable, Node 22 z natywnym WebSocket, Python z `psutil`):

```sh
build/research/venv/bin/python scripts/research/realtime_probe.py --prepare
build/research/venv/bin/python scripts/research/realtime_probe.py --build
build/research/venv/bin/python scripts/research/realtime_probe.py --run
```

Build release używa `--locked -j2`; `prepare` odtwarza projekt pod ignorowanym `build/research/realtime`. Domyślne `run` wykonuje dokładnie trzy powyższe warianty, każdy z nowym serwerem na `127.0.0.1:0`, zapisuje wyniki i kończy własne procesy. [Runner](../../../scripts/research/realtime_probe.py), [serwer](../../../scripts/research/realtime_probe.rs), [klient](../../../scripts/research/realtime_probe_client.cjs), [Cargo.lock](../../../scripts/research/realtime_probe_cargo.lock). Pełne SHA-256 wszystkich czterech plików są w `sources_sha256` wyników; zweryfikowano ich zgodność po wykonaniu próby. To pomiar jednego rozwiązania, nie porównanie języków backendu.

## Wybór początkowy

**Warunkowo rekomenduję Cloud Run + Axum WebSocket + opisany fan-out PostgreSQL** jako pierwszy wariant wdrożenia: jeden dostawca i natywny backend Rust, z jawnym kosztem połączeń. Warunek obejmuje rzeczywistą pojemność instancji z TLS, autoryzacją i bazą, a nie sam limit platformy; pełną decyzję porównuje [ocena chmur](cloud-comparison.md). Workers + hibernujące DO pozostają wariantem optymalizacji relay przy rzadkich zmianach. Korzyść musi uzasadnić dodatkową integrację oraz osobne ustalenia lokalizacji danych i przetwarzania; sama mała opłata za jednostki DO nie wystarcza. Kalkulator historii z modelem połączeń nadal nie wycenia pełnej implementacji realtime.

Odbiór pierwszego przekroju: zmiana → drugi klient, reconnect, out-of-order, utrata sieci i TTL, restart relay, dwa równoległe urządzenia oraz brak powielonych sugestii. Mierzymy p50/p95/p99, odsetek nieaktualnych stanów, RAM na połączenie i koszty czasu aktywnego. Tych wyników nie zastąpią testy lokalnej bazy.
