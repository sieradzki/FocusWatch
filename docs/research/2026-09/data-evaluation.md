# FocusWatch: dane, raporty i synchronizacja — zakres dowodów

Badanie na lokalnym komputerze użytkownika, 27.09.2026. Skrypty i wyniki są eksperymentami architektonicznymi; nie stanowią gotowego collectora ani protokołu produkcyjnego. Aplikacja, jej schemat i dane nie zostały zmienione.

## Jakie decyzje można podjąć z tych pomiarów

1. Rozdzielić zapis obserwacji od obliczania raportów. Sprawdzić, czy SQLite z indeksami i małymi projekcjami dziennymi wystarcza do lokalnych raportów z lat.
2. Porównać operacyjne zapytania o dzień z analitycznym skanem historii. DuckDB/Parquet nie musi być dobrym zamiennikiem SQLite, nawet gdy szybciej agreguje długą historię.
3. Zmierzyć fizyczne rozmiary przykładowych reprezentacji i podać je do analizy kosztów, z zakresem zmienności. Rozmiar JSON w transmisji, rekord SQL z indeksami i skompresowane archiwum to różne wielkości.
4. Ustalić minimalne zasady czasu i przesyłania, które można sprawdzić niezależnie od języka, frameworka i LLM.

Nie mierzymy maksymalnej liczby klientów chmury, baterii, jakości rekomendacji, wydajności Windows ani zdolności klasyfikatora do ustalania intencji użytkownika. Wyniki silników wywoływanych przez Pythona nie są porównaniem Python/Rust/Go.

## Scenariusz i metodologia

Skrypt [data_benchmark.py](../../../scripts/research/data_benchmark.py) generuje deterministyczne metadane: dwa urządzenia, foreground i media na każdym, po osiem godzin na dobę i checkpointy co 30 sekund. Daje to **3840 obserwacji dziennie**; 1 mln rekordów reprezentuje około 0,71 roku, a 10 mln około 7,13 roku tego scenariusza. To jawny scenariusz obciążenia, nie zmierzona średnia przyszłych użytkowników.

Identyfikatory mają zmienną treść, tytuły 100003 warianty, ścieżki 4096 wariantów, aplikacje 32, kategorie 8. Generator nie dotyka prywatnych tytułów/URL. Dane są ułożone czasowo, przedziały mają stałą długość, a kategorie są skorelowane z aplikacjami. Sprzyja to kompresji; nie ekstrapolujemy współczynnika kompresji bez marginesu na inne metadane. Nie ma screenshotów, audio, embeddingów ani pełnej treści stron.

- **SQLite:** WAL, `synchronous=FULL`, cache 64 MiB; stabilne ID, unikalna sekwencja źródła, indeksy czasu i źródła/czasu; dzienne agregaty w osobnej tabeli.
- **DuckDB:** dwa wątki, limit pamięci 512 MB, ten sam zbiór Parquet/ZSTD, row group 122880; zapytania o te same kolumny i zakresy.
- **PostgreSQL:** osobny lokalny klaster, wyłącznie Unix socket, `fsync=on`, `synchronous_commit=on`; 128 MB shared buffers; tenant + UUID + JSONB i indeksy. Test ma jednego historycznego tenanta, a osobnego syntetycznego tenanta używa do małych batchy.
- **Timingi:** siedem wykonań; pierwszy wynik osobno, mediana i zakres następnych sześciu. Pamięć podręczna OS jest rozgrzana; nie czyszczono globalnych cache ani nie zatrzymywano aplikacji użytkownika. To użytkowany laptop, nie izolowany serwer laboratoryjny.
- **Dzień:** ostatni kompletny dzień z 3840 obserwacjami w obu dużych zbiorach. Rok jest przycięty do dostępnej historii; przy 1 mln nie ma pełnych 365 dni.
- **Poprawność:** te same wyniki zapytań SQLite i DuckDB; sumy z projekcji równe surowym sumom; PostgreSQL porównuje wyniki z tym samym Parquet po normalizacji UUID/JSON.

Pomiar `date_function_day_count` i `range_day_count` używa **tej samej nowej tabeli**. Pokazuje koszt kształtu predykatu SQL, a nie kompletną wydajność starej aplikacji. Stary ORM i Qt nie są tu uruchamiane.

Ładowanie milionów rekordów ma duże batche i dodatkowe indeksy budowane później. **Nie jest pomiarem produkcyjnego ingestu.** Oddzielny eksperyment PostgreSQL mierzy małe, trwałe transakcje i powtórzenie batcha, nadal lokalnie i przez jednego klienta.

Surowe wyniki: [SQLite/DuckDB](data-results.json), [PostgreSQL](postgres-results.json), [semantyka i awarie](sync-semantics-results.json). Wersje bibliotek, parametry i hash skryptu znajdują się w JSON. `dataset_reused=true` oznacza ponowny pomiar gotowych syntetycznych plików; czasy ich utworzenia mają wtedy wartość `null`.

## Co jest czasem osoby, a co kontekstem

Raport sumowania aplikacji w benchmarku mierzy **czas źródeł/urządzeń**, nie uwagę człowieka. Osoba może jednocześnie pracować w edytorze, mieć otwarte drugie urządzenie i słuchać streamu. Model zachowuje wszystkie obserwacje; miara łącznego czasu wykorzystuje unię przedziałów. Współwystępowanie jest oddzielną cechą kontekstu. Nie przypisujemy automatycznie 50% uwagi do każdego źródła ani negatywnej oceny rozrywce.

Obserwacja powinna określać źródło, urządzenie, wersję schematu, przedział lub punkt czasu i jakość pomiaru. Interpretacja wskazuje wersję reguły/modelu oraz materiał źródłowy. Ręczna korekta pozostaje odrębną decyzją użytkownika; przeliczenie klasyfikacji nie może jej po cichu zastępować. Zamiar, plan i zaobserwowana aktywność to odrębne pojęcia.

Raport dnia używa granic lokalnego dnia przeliczonych na UTC, przecina przedziały i zachowuje strefę raportu. Dni zmiany czasu mogą mieć 23 lub 25 godzin. Czas monotoniczny pomaga w ustalaniu czasu trwania, ale nie porządkuje różnych urządzeń i sam nie rozwiązuje uśpienia; adapter musi zgłaszać nieciągłości, przerwy i niepewność.

## Co sprawdzono w synchronizacji

[sync_semantics_probe.py](../../../scripts/research/sync_semantics_probe.py) uruchamia dziesięć scenariuszy:

- awaria osobnego procesu przed i po wspólnym zatwierdzeniu obserwacji i outbox; integralność bazy po ponownym otwarciu;
- sekwencyjne powtórzenie po utracie ACK bez duplikatu oraz odrzucenie tego samego ID z inną treścią;
- brak potwierdzenia brakującej sekwencji, gdy przyszły późniejsze zdarzenia;
- czytelnik WAL ze stabilnym snapshotem podczas zatwierdzenia przez pisarza;
- równoległe, zagnieżdżone i rozłączne przedziały, granica północy oraz DST;
- wykrycie cofnięcia zegara i minimalny warunek blokujący powrót danych ze starej generacji po resecie.

Próby nie obejmują rzeczywistej utraty zasilania, transportu HTTP, uwierzytelnienia, równoległych retry, selektywnego usuwania, backupów ani wyścigów retencji. Test generacji to demonstracja warunku po resecie całego zbioru. Nie wolno opisać tych wyników jako „gotowy bezpieczny sync”. PostgreSQL `ON CONFLICT` w próbie wydajności również nie zastępuje porównania treści przy konflikcie ID.

Wniosek projektowy: lokalne obserwacje i kolejka wysyłki są zatwierdzane atomowo; ACK następuje po trwałym przyjęciu, a ponowienia są normalną częścią protokołu. Kolekcja działa bez UI i sieci. Błędy zapisu, źródła bez uprawnień i przeterminowany checkpoint muszą być widoczne jako brak danych, nie jako zerowa aktywność. Nie ma potrzeby obiecywania transportu „exactly once”.

## Wieloletnia historia i prywatność

Zarchiwizowanie szczegółów nie oznacza ich usunięcia. Projekcje mogą zapewniać natychmiastowe raporty, a szczegóły być pobierane na żądanie. Przeliczenie wieloletniej klasyfikacji działa w tle i ma wersję wyniku; nie blokuje collectora ani renderera.

Istnieją dwa różne warianty chmury:

1. **Serwer może analizować obserwacje:** operacyjne rekordy w PostgreSQL, starsze szczegóły w Parquet/object storage, projekcje i kontrolowane zadania analityczne. Koszt zależy m.in. od hot retention, indeksów, kopii i odczytów archiwum.
2. **E2EE/blind sync:** szczegóły pozostają nieczytelne dla serwera. Obliczenia i kompresja odbywają się przed szyfrowaniem na uprawnionym urządzeniu; chmura przechowuje zaszyfrowane paczki oraz ograniczone metadane synchronizacji. Serwer nie wykona SQL/LLM nad zaszyfrowaną treścią. Współdzielenie wybranych podsumowań z usługą AI jest osobnym przepływem.

Pomiar Parquet dotyczy jawnych danych syntetycznych. Nie zakłada kompresji ciphertextu ani deduplikacji między użytkownikami. Wybór modelu prywatności nie został narzucony badaniem; pozostaje osobną decyzją przed wdrożeniem przesyłania rzeczywistych danych. Przy każdym wariancie potrzebne są eksport, odwołanie urządzenia, odzyskiwanie dostępu i zasady usunięcia obejmujące pochodne dane oraz backupy.

## Odtworzenie

Uruchomić z katalogu głównego repo. Duże pliki trafiają do ignorowanego `build/research`, nie do repo ani do oryginalnej bazy. Eksperyment wymaga kilku GB wolnego dysku, Pythona oraz lokalnych programów PostgreSQL dla jego części. Nie uruchamiać jednocześnie z pomiarami UI.

```sh
python3 -m venv build/research/venv
build/research/venv/bin/pip install -r scripts/research/requirements.in
build/research/venv/bin/python scripts/research/data_benchmark.py --rows 1000000 10000000
build/research/venv/bin/python scripts/research/postgres_benchmark.py
build/research/venv/bin/python scripts/research/sync_semantics_probe.py
```

Ponowny pomiar istniejących kompletnych danych: `data_benchmark.py --reuse`. Skrypt PostgreSQL odmawia nadpisania klastra; do nowego przebiegu podać inny `--cluster` i `--output`. Klaster jest zatrzymywany po próbie. Żaden skrypt nie wymaga dostępu do konta chmurowego.

Źródła techniczne: [SQLite WAL — współbieżność, trwałość i checkpoint](https://www.sqlite.org/wal.html), [DuckDB — strojenie obciążeń](https://duckdb.org/docs/current/guides/performance/how_to_tune_workloads), [Parquet w DuckDB](https://duckdb.org/docs/current/data/parquet/overview), [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html), [PostgreSQL partycjonowanie](https://www.postgresql.org/docs/current/ddl-partitioning.html). Partycjonowanie chmury należy ocenić przy rzeczywistym wielotenanckim obciążeniu; lokalny test miliona wierszy go nie wymaga i nie dowodzi jego przydatności przy każdej skali.
