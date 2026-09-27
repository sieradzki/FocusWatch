# Wyniki pomiarów danych

Wygenerowano z `data-results.json` i `postgres-results.json` przez `scripts/research/summarize_data.py`.
Wszystkie czasy poniżej to **mediany sześciu rozgrzanych wykonań**, bez sieci i UI. Pełna metoda i ograniczenia: [data-evaluation.md](data-evaluation.md).

## Ten sam zbiór i zapytania

| Zapytanie | SQLite 1 mln | DuckDB/Parquet 1 mln | SQLite 10 mln | DuckDB/Parquet 10 mln |
| --- | ---: | ---: | ---: | ---: |
| Strona osi dnia, 500 rekordów | 1.61 ms | 16.47 ms | 2.41 ms | 31.63 ms |
| Sumy aplikacji, pełny dzień | 1.01 ms | 5.08 ms | 1.26 ms | 8.81 ms |
| Sumy aplikacji, ostatni dostępny rok | 242.32 ms | 24.70 ms | 330.30 ms | 36.48 ms |
| Sumy aplikacji, cała historia | 243.67 ms | 19.92 ms | 3282.43 ms | 184.19 ms |

Przy 1 mln dostępnych jest mniej niż 365 dni. Sumy aplikacji dotyczą ekspozycji foreground z urządzeń; nie są miarą ludzkiej uwagi ani czasem osoby po deduplikacji.

## Kształt zapytań i agregaty SQLite

| Operacja | 1 mln | 10 mln |
| --- | ---: | ---: |
| COUNT dnia z funkcją date na kolumnie | 296.57 ms | 2189.66 ms |
| COUNT dnia przez indeks zakresu | 0.17 ms | 0.16 ms |
| Rok z projekcji dziennych | 5.62 ms | 8.69 ms |
| Historia z projekcji dziennych | 5.68 ms | 120.73 ms |

Porównanie predykatów używa tej samej tabeli eksperymentalnej; nie jest uruchomieniem starego FocusWatch. Wyniki projekcji sprawdzono względem zapytań surowych.

## Rozmiar reprezentacji

| Reprezentacja | 1 mln | 10 mln |
| --- | ---: | ---: |
| SQLite, tabela i indeksy | 481.94 MB | 4827.12 MB |
| Dodatkowe projekcje dzienne | 1.19 MB | 12.55 MB |
| Parquet/ZSTD | 52.02 MB | 520.27 MB |

Przy 10 mln: SQLite **482.7 B/obserwację**, Parquet **52.0 B/obserwację**. Próbka JSON z obiektem payload: **486.7 B/obserwację**.
Wartości nie są zamienne. SQLite ma indeksy potrzebne do małych odczytów; Parquet inną organizację i kompresję. Dane są syntetyczne i uporządkowane, bez szyfrowania. Koszt chmury używa marginesów i analizy wrażliwości, nie kopiuje bezkrytycznie współczynnika kompresji.

## PostgreSQL, 1 mln tych samych obserwacji

Tabela i indeksy: **563.72 MB**, czyli **563.7 B/obserwację**, bez repliki, backupu i zapasu na wzrost/bloat. Schema ma dodatkowe account_id, UUID i JSONB; nie jest identyczna fizycznie z SQLite.

| Zapytanie | Mediana lokalnie |
| --- | ---: |
| Strona osi dnia | 6.54 ms |
| Sumy dnia | 0.88 ms |
| Dostępny rok | 111.48 ms |
| Cała historia | 61.22 ms |

200 sekwencyjnych trwałych transakcji po osiem obserwacji: mediana **6.42 ms**, empiryczny 95. percentyl **9.43 ms**. Retry pierwszej paczki nie zwiększył liczby zapisów.
To klient przez lokalny Unix socket. Nie ma HTTP/TLS, autoryzacji ani równoległych użytkowników. Nie wolno przeliczać odwrotności tego czasu na obiecaną przepustowość usługi chmurowej.

## Wniosek

SQLite z indeksami i odbudowywalnymi projekcjami jest uzasadnioną bazą lokalnego rdzenia. Rozmiar historii sam w sobie nie wymaga DuckDB w każdym kliencie. DuckDB/Parquet ma odrębną rolę w skanach i archiwach; jego wdrożenie należy powiązać z konkretną potrzebą analityczną.
PostgreSQL pozostaje kandydatem operacyjnej chmury dzięki transakcjom, zapytaniom i modelowi wielu kont. Ta próba potwierdza działanie proponowanego wzorca, nie ustala maksymalnej skali komercyjnej ani zwycięzcy języków backendu.
