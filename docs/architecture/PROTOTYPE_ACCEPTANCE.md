# Odbiór pierwszego prototypu FocusWatch

Data: 03.10.2026. **Wszystkie poniższe scenariusze są zaplanowane, nie wykonane.** Nie należy przepisywać tu zaliczeń ze wrześniowych mikrobenchmarków. [Plan](../IMPLEMENTATION_PLAN.md), [baseline](REBUILD_BASELINE_2026-10-03.md).

## Cel przekroju

Agent działa samodzielnie, zapisuje poprawną historię, raport ujawnia jej znaczenie i niepewność, a ręczna korekta przetrwa restart i przeliczenie. Działa to bez LLM i sieci. Płatny produkt pozostaje założeniem biznesowym; testowa baza nie potrzebuje prawdziwego operatora płatności.

## Macierz scenariuszy

| ID | Etap | Wejście lub awaria | Oczekiwany wynik |
| --- | --- | --- | --- |
| T01 | P0 | Edytor i stream równocześnie przez 60 min | Dwa źródła po 60 min, unia pokrycia 60 min; brak wniosku o uwadze 50/50 |
| T02 | P0 | Obecność 10–11, stream 10–12 | Media 120 min; potwierdzone przez zadaną regułę pokrycie obecnością 60 min; brak automatycznego zaliczenia 120 min pracy |
| T03 | P0 | Dwa urządzenia: 10–12 i 11–13 | Suma czasów urządzeń 4 h, unia tych przedziałów 3 h; zachowane źródła; brak uniwersalnej etykiety uwagi |
| T04 | P0 | `[10:00,11:00)` i `[11:00,12:00)` | Brak podwójnego naliczenia wspólnej granicy |
| T05 | P0 | Przedział przecina północ raportu | Podział według granic lokalnej doby przeliczonych na UTC; suma zachowana |
| T06 | P0 | Doby zmiany czasu Europe/Warsaw | Wektory obejmują dobę 23 h i 25 h; nie dodawać stałych 24 h do każdej północy |
| T07 | P0 | Cofnięcie wall clock i restart procesu | Brak ujemnych długości; monotonic/boot/session nie udają globalnego zegara; nieciągłość widoczna |
| T08 | P0 | Ten sam ID/payload powtórzony; potem ten sam ID z inną treścią | Retry idempotentny; konflikt danych jawny, nie ciche nadpisanie |
| T09 | P0 | Sekwencja 1,3, potem 2 | Brak ACK ciągłego prefiksu obejmującego lukę; po uzupełnieniu prawidłowy postęp |
| T10 | P0 | Korekta kategorii, potem zmiana reguł i rebuild | Korekta zachowana z pochodzeniem i priorytetem; zmiana reguły nie zmienia surowej obserwacji |
| T11 | P1 | Kill przed i po commit obserwacji+outbox | Albo oba wpisy trwałe, albo żaden; brak podwójnego czasu po restarcie; luka nie jest wypełniana domysłem |
| T12 | P1 | Zamknięcie/awaria GUI lub browser hosta | Agent i niezależne źródła działają dalej; browser source oznaczony jako niedostępny |
| T13 | P1 | Suspend/resume, lock, brak uprawnienia | Źródła opisują rzeczywisty zakres możliwości; nieznany okres nie staje się bezczynnością ani pracą |
| T14 | P1 | Pełny dysk, write error, powiększający się WAL | Widoczny błąd, brak fałszywego ACK; ograniczone kolejki; udokumentowane odzyskanie i checkpoint |
| T15 | P1 | Obcy lokalny klient IPC, zbyt duża ramka, zalew wiadomości | Odrzucenie według uprawnień/limitów; brak dowolnego shell i nieograniczonej pamięci |
| T16 | P2 | Duża historia, filtr, zoom, przewijanie | Ograniczone zapytania i liczba elementów; poprawność agregatu wyjaśnialna szczegółami |
| T17 | P2 | Korekta, usunięcie zakresu, eksport i rebuild | Korekta zachowana; skasowane dane nie wracają z projekcji; eksport ma jednostki i wersję |
| T18 | P2 | Windows/Arch, klawiatura, skalowanie, długie idle | Osobne wyniki platformowe, czas query/render osobno, mierzone drzewo procesów; brak udawanego testu GPU w Xvfb |
| T19 | P3 | Czysta i przerwana aktualizacja agent/UI/schema | Zgodność wersji albo bezpieczna odmowa; backup przed nieodwracalną migracją; brak rollbacku binarki do niezgodnego schematu |
| T20 | P3 | Offline/licencja wygasła, spóźniony webhook | Zachowanie zgodne z wybraną polityką; dane nie są kasowane przez błąd rozliczeń; dostęp do eksportu/odzyskania według jawnych zasad |
| T21 | P4 | Payload zapisany, manifest niedostępny; potem retry | Brak finalnego ACK przed odnajdywalnym trwałym przyjęciem; retry/reconciliation nie gubi danych |
| T22 | P4 | Reconnect, stary snapshot, TTL, wolny peer | Najnowszy stan lub unknown; bez odtwarzania starych sugestii; ograniczony bufor |
| T23 | P4 | Odwołane/stare urządzenie po usunięciu historii | Brak dostępu do nowych danych, brak przywrócenia usunięć starym uploadem; nie obiecywać odebrania już pobranych kopii |
| T24 | P4 | Nowy klient, utrata urządzenia, izolacja dwóch kont | Odtworzenie według modelu kluczy i manifestów; brak dostępu między kontami; export/restore sprawdza niezależność od jednego serwera |

## Jak zapisywać wyniki

Każdy wynik zawiera ID testu, commit, wersje, OS, sprzęt, fixture, komendę, oczekiwany wynik, rzeczywisty wynik i ograniczenia. Statusy wykonania: `pass`, `fail`, `not_run`, `blocked`. Liczba zaplanowanych przypadków nie jest liczbą zaliczonych testów.

Testy czystej domeny mogą działać w CI bez OS collectorów. Test adaptera wymaga odpowiedniego systemu. Emulator/syntetyczne okno nie zastępują zwykłej sesji użytkownika. Nie używać osobistej bazy lub tytułów jako domyślnego fixture.

Pomiary: agent bez UI, UI otwarte, UI zamknięte, normalna praca i większa historia. CPU raportować względem jednego logicznego rdzenia; pamięć całego własnego drzewa procesów i metodę rozliczenia stron współdzielonych. Mierzyć startup, query, render, interakcje i długie idle osobno. Bateria wymaga własnej metody; procent CPU nie jest pomiarem energii.

## Warunek przejścia dalej

P0 zamyka kontrakt na syntetycznych danych, nie gotowość platformy. P1/P2 wymagają rzeczywistych Windows 11 i Arch/dwm/X11. Cloud/privacy nie blokuje tych etapów. T21–T24 wymagają wybranego modelu prywatności oraz osobnego testu serwera; localhost nie daje wyniku chmurowego.

Budżety CPU/RAM/baterii i sprzęt odniesienia ustalić przed oceną porównawczą. Wcześniejsze 300 MiB i 1/5 s nie są wymaganiami użytkownika. Gdy pomiar nie mieści się w przyjętym budżecie, nie przesuwać progu bez jawnego uzasadnienia; poprawić przyczynę lub porównać najbliższą alternatywę.

Przed zewnętrzną sprzedażą potrzebne są także testy podpisów, kluczy/sejfów OS, backupu/odtworzenia, usuwania, prywatności logów i rozliczeń; ta macierz nie jest pełnym audytem bezpieczeństwa.
