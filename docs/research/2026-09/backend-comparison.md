# FocusWatch: wybór technologii backendu

**Rekomendacja robocza: jeśli collector i lokalny rdzeń powstaną w Rust, pierwszy backend zbudować jako jeden modułowy serwis Rust + Axum + SQLx + PostgreSQL.** Przemawia za tym ograniczenie liczby stosów utrzymywanych w małym projekcie i możliwość współdzielenia części kontraktów. Nie wykazano, że taki backend będzie szybszy lub tańszy od Go, Pythona, TypeScriptu czy .NET. **Go + pgx jest najbliższą alternatywą**, szczególnie gdy chmura ma głównie synchronizować zaszyfrowane paczki, obsługiwać konta i urządzenia.

To rekomendacja dotycząca implementacji przyszłego serwera, nie powód do uzależnienia pierwszego lokalnego raportu od wdrożenia chmury. Wybór Rust dla collectora również wymaga odrębnego uzasadnienia: omówiono go w [ocenie przebudowy](rewrite-assessment.md).

Stan źródeł: 27.09.2026. Poniżej oddzielono udokumentowane możliwości bibliotek od naszej oceny dopasowania. Nie wykonano porównawczego benchmarku serwerów HTTP w tych pięciu stosach.

## Najpierw zakres odpowiedzialności serwera

W obu modelach prywatności serwer może potrzebować kont, rejestru urządzeń, autoryzacji, ograniczania rozmiaru paczek, trwałego przyjęcia danych, wznowienia synchronizacji, eksportu, usuwania danych i rozliczeń. Żaden z rozpatrywanych języków nie usuwa konieczności zaprojektowania tych mechanizmów.

| Model chmury | Rzeczywiste zadania serwera | Znaczenie wspólnego rdzenia z desktopem |
| --- | --- | --- |
| **Chmura może czytać obserwacje** | Walidacja treści, zapytania i projekcje wielu urządzeń; ewentualnie zadania klasyfikacji oraz raportowania | Wspólny czysty silnik przedziałów, reguł i wersjonowanych interpretacji może mieć wartość. PostgreSQL nadal wymaga własnego schematu i zapytań |
| **Chmura przechowuje zaszyfrowane paczki bez kluczy treści** | Uprawnienia, dostarczenie, limity, potwierdzenia, wersje i usunięcia na podstawie jawnej koperty; analityka treści na urządzeniach | Serwer nie może wykonać wspólnego klasyfikatora na zaszyfrowanym payloadzie. Pozostaje współdzielenie protokołu i części walidacji koperty, więc argument za Rust jest słabszy |

To konsekwencje rozpatrywanych architektur, nie deklaracja, że FocusWatch ma już gotowe szyfrowanie end-to-end. Wariant drugi wymaga osobnego projektu kluczy, dołączania urządzeń i odzyskiwania dostępu. Jawne metadane paczek również trzeba zdefiniować. Backend, który nie zna treści, nie wygeneruje sam szczegółowego raportu z całej historii; wyniki muszą powstawać na uprawnionym kliencie lub być przez niego świadomie udostępnione.

## Pięć realnych wariantów

### Rust: Axum + SQLx

**Udokumentowane mechanizmy:** Axum dostarcza routing, ekstraktory żądań i integrację z middleware Tower; opiera się na Tokio i Hyper. SQLx obsługuje PostgreSQL i SQLite, pule połączeń oraz migracje. Jego makra mogą sprawdzać SQL względem schematu przy kompilacji; do budowania bez połączenia z bazą służą przygotowane metadane offline. [Axum](https://docs.rs/axum/latest/axum/), [SQLx](https://github.com/transact-rs/sqlx)

**Dopasowanie — nasza ocena:** dobre, gdy już utrzymujemy Rust w collectorze. Mała biblioteka typów protokołu i czystych funkcji może działać w obu procesach. Jawne SQL dobrze pasuje do ograniczonych odczytów, paczek zapisu i agregacji bez materializowania całej historii jako obiektów.

**Koszt i granice:** trzeba zaprojektować błędy, transakcje, anulowanie, limitowanie pracy i własną integrację elementów serwera. Sprawdzanie SQL przy kompilacji nie dowodzi poprawnego naliczania czasu, izolacji kont ani planu zapytania. Jeden toolkit nie oznacza identycznego SQL w SQLite i PostgreSQL. Wspólna biblioteka może też niepotrzebnie związać wersje klienta i serwera, jeżeli zamiast małych kontraktów przeniesiemy do niej całe modele aplikacji.

### Go: net/http + pgx

**Udokumentowane mechanizmy:** biblioteka standardowa zapewnia serwer HTTP i kontekst żądania. pgx jest sterownikiem i zestawem narzędzi PostgreSQL; obejmuje pule połączeń, paczki zapytań, COPY, JSON/JSONB oraz tracing. [net/http](https://pkg.go.dev/net/http), [pgx](https://github.com/jackc/pgx)

**Dopasowanie — nasza ocena:** szczególnie mocny wariant dla niewielkiego serwisu obsługującego I/O, transakcje i protokół synchronizacji. Nie wymaga przekładania domeny na rozbudowany ORM. Kod serwera może pozostać niezależny od integracji systemowych collectora, co jest zaletą, jeżeli wspólna logika ogranicza się do kilku DTO.

**Koszt i granice:** przy collectorze Rust dochodzi dodatkowy toolchain i druga implementacja walidacji. Można ograniczyć rozjazdy przez specyfikację protokołu i wspólne dane testowe; nie trzeba wprowadzać FFI. Ocena, że Go będzie dla konkretnego autora prostsze w rozwoju niż Rust, pozostaje hipotezą o pracy zespołu, nie wynikiem pomiaru. Nie znamy przewagi kosztu serwera ani opóźnień w tym projekcie.

### Python: FastAPI + SQLAlchemy + sterownik PostgreSQL

**Udokumentowane mechanizmy:** FastAPI odróżnia asynchroniczne handlery od zwykłych funkcji wykonywanych przez framework w puli wątków; dowolna funkcja pomocnicza wywołana z handlera nie jest automatycznie przenoszona do tej puli. SQLAlchemy oferuje AsyncEngine i AsyncSession; równoległe zadania powinny używać odrębnych sesji. Można uruchamiać wiele procesów Uvicorn. [FastAPI async](https://fastapi.tiangolo.com/async/), [SQLAlchemy asyncio](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html), [worker processes](https://fastapi.tiangolo.com/deployment/server-workers/)

**Dopasowanie — nasza ocena:** wiarygodny wybór API, także z dużą historią przechowywaną i agregowaną w SQL. Szczególnie sensowny, jeśli lokalny rdzeń pozostanie w Pythonie lub pierwsza implementacja wykaże wyraźną przewagę tempa zmian. Obecne doświadczenie z Pythonem jest realnym kosztem alternatywnym, ale nie wystarcza jako jedyny argument.

**Koszt i granice:** stare modele lokalnej aplikacji nie są gotowym backendem wielu kont. Trzeba ograniczyć zakres wyników, unikać zapytań w pętlach i blokowania pętli zdarzeń. Długie obliczenia nie powinny wykonywać się bez ograniczeń w ścieżce przyjęcia danych. Python jest niezależnie dobrym kandydatem do prac eksperymentalnych nad AI; wybór takiego workera nie wymusza Pythona w serwerze synchronizacji.

### TypeScript: Fastify + sterownik PostgreSQL

**Udokumentowane mechanizmy:** Fastify używa schematów do walidacji wejścia i serializacji odpowiedzi; type providers pozwalają wyprowadzać typy TypeScript ze schematów. Node udostępnia worker threads do pracy obciążającej CPU; jego dokumentacja odróżnia ten przypadek od zwykłego asynchronicznego I/O. [Walidacja i serializacja](https://fastify.dev/docs/latest/Reference/Validation-and-Serialization/), [type providers](https://fastify.dev/docs/latest/Reference/Type-Providers/), [worker threads](https://nodejs.org/api/worker_threads.html)

**Dopasowanie — nasza ocena:** mocny kandydat, jeśli raporty i rozszerzenie przeglądarki używają TypeScriptu, a backend pozostaje niewielkim API. Wspólne schematy mogą ograniczyć liczbę ręcznych mapowań między klientem i serwerem. To rzeczywista alternatywa dla argumentu „Rust już występuje w projekcie”.

**Koszt i granice:** typy kompilatora nie zastępują walidacji danych przychodzących z urządzeń. Kontrakt musi jawnie określić reprezentację identyfikatorów, liczników i czasu; nie wolno zakładać, że każdy 64-bitowy licznik przejdzie bezstratnie jako JavaScript Number. [Zakres bezpiecznych liczb całkowitych](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/MAX_SAFE_INTEGER) Duże synchroniczne przeliczenia i serializacje wymagają limitów lub wydzielenia. Używanie Reacta nie oznacza potrzeby współdzielenia stanu UI z backendem.

### C#: ASP.NET Core + Npgsql

**Udokumentowane mechanizmy:** ASP.NET Core obejmuje hosting, konfigurację, dependency injection, logging i middleware. API można budować przez Minimal APIs; dostępne jest generowanie OpenAPI. NpgsqlDataSource organizuje dostęp do PostgreSQL i pulę połączeń, z asynchronicznymi komendami oraz transakcjami. [ASP.NET Core fundamentals](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/?view=aspnetcore-10.0), [Minimal APIs](https://learn.microsoft.com/en-us/aspnet/core/tutorials/min-web-api?view=aspnetcore-10.0), [OpenAPI](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/openapi/overview?view=aspnetcore-10.0), [Npgsql](https://www.npgsql.org/doc/basic-usage.html)

**Dopasowanie — nasza ocena:** mocny wariant, gdy cenne są spójne konwencje frameworka i doświadczenie z C#. Backend nie musi działać na Windowsie. Nie ma technicznej przyczyny wykluczania go ze względu na klienta Linux lub Rust.

**Koszt i granice:** przy Rust na desktopie i TypeScript w UI wprowadza kolejny ekosystem, bez bezpośredniego wykorzystania obecnego kodu domeny. EF Core nie jest obowiązkowy; Npgsql i jawne SQL wystarczą dla rozpatrywanego dostępu do danych. Nie ma tu pomiaru uzasadniającego wyższą lub niższą wydajność od pozostałych wariantów.

## Co rzeczywiście warto współdzielić

**Tak:** wersjonowaną kopertę zdarzeń, zasady jednostek czasu, format identyfikatorów, limity i wektory testowe retry/ACK/duplikatów. Przy dostępie obu stron do treści: małe czyste funkcje reguł i przedziałów. **Osobno:** adaptery OS, SQLite i PostgreSQL, autoryzację kont, lifecycle procesów, UI oraz framework HTTP.

Wspólny język pozwala współdzielić kod, lecz zgodność nadal wymaga testów różnych wersji protokołu. Nowy serwer będzie obsługiwał klientów aktualizowanych w różnym czasie. Z kolei różne języki nie wymuszają odmiennych reguł: wspólne przykłady wejścia/wyjścia pozwalają weryfikować równoważność implementacji.

Argument „ten sam klasyfikator na desktopie i serwerze” jest poprawny tylko wtedy, gdy serwer faktycznie będzie klasyfikował dostępne mu dane. Nie należy budować serwera Rust wyłącznie dla hipotetycznego ponownego użycia algorytmu w chmurze pozbawionej kluczy.

## Uzasadnienie wyboru i warunki zmiany

Przy założeniu **Rust collector + mały zespół + brak wykazanej przewagi innego backendu** wybrałbym Axum i SQLx, z wąskim modułem współdzielonego protokołu. Unikamy dokładania Go wyłącznie po to, by przepisać podobne endpointy. Nie oznacza to przenoszenia ML do Rust ani wspólnego ORM klienta i chmury.

Wybrałbym **Go + pgx**, jeśli chmura stanie się przede wszystkim blind-sync/control-plane i rzeczywista implementacja okaże się wyraźnie prostsza do utrzymania w Go, lub pojawi się odpowiednie doświadczenie zespołu. **FastAPI** pozostaje naturalnym kandydatem, gdy rdzeń desktopowy pozostanie Pythonowy; **Fastify** przy silnym skupieniu pracy wokół TypeScriptu; **ASP.NET Core** przy przewadze doświadczenia C# i potrzebie konwencji jego frameworka. To jawne warunki decyzji, nie ranking popularności.

Pierwszy serwis powinien mieć jedną bazę i czytelne moduły. Wybór języka nie wymaga mikroserwisów ani Kubernetes. W żadnym wariancie nie kopiujemy aktualnego wzorca pobierania całej historii do pamięci na potrzeby raportu.

## Co wykazały pomiary, a czego nie wykazały

Próby `data_benchmark.py`, `postgres_benchmark.py` i `sync_semantics_probe.py` sprawdzają wybrane wzorce dostępu do syntetycznych danych i scenariusze semantyki synchronizacji. Klient bazowy napisany w Pythonie nie jest implementacją żadnego z porównywanych serwerów. Te próby nie obejmują HTTP, autoryzacji, wielu równoległych kont, tych samych pul połączeń ani pełnego narzutu protokołu. Z pomiaru SQLite/PostgreSQL/DuckDB nie wynika, który język API zwycięża. Osobna [próba realtime](realtime-design.md) dotyczy małego relay Axum; nie jest porównaniem pięciu języków ani kompletnego serwera.

Jeżeli koszt lub przepustowość backendu stanie się kryterium rozstrzygającym, wystarczy porównać **wybranego kandydata i najbliższą alternatywę**, a nie budować pięć produktów. Warunki muszą być równe: ta sama walidacja, dane i serializacja, schemat i indeksy, trwałość transakcji, rozmiar paczki, retry, równoległość, pula połączeń oraz limit zasobów. Wynik ma obejmować poprawność, błędy i opóźnienia pod obciążeniem oraz pamięć/CPU całego procesu. Rekordy na sekundę z endpointu pomijającego trwały zapis nie odpowiadają zadaniu FocusWatch.

## Dystrybucja i utrzymanie produktu

Każdy wariant potrzebuje odtwarzalnego buildu, aktualizacji zależności i obrazu/runtime, kopii bazy, obserwowalności bez tytułów okien w logach oraz wersjonowania protokołu. Język nie zastępuje tych prac. Kontener jest opakowaniem wdrożenia; IaC opisuje zasoby niezależnie od tego, czy API jest w Rust czy Pythonie.

Przed publikacją należy zinwentaryzować **konkretne wersje i zależności przechodnie**, w tym biblioteki natywne, obrazy bazowe i używane usługi. Licencja głównego frameworka ani repozytorium nie rozstrzyga warunków całego produktu. To zadanie przeglądu zależności, nie stwierdzenie prawne o dozwolonym modelu sprzedaży. Osobno udokumentowany przypadek Qt Charts dotyczy obecnego klienta, nie stanowi argumentu za konkretnym językiem serwera.
