#!/usr/bin/env python3
"""Generate the human-readable storage evidence from checked-in measured JSON."""
import json
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[2]
DOCS=ROOT/'docs/research/2026-09'


def main():
    data=json.loads((DOCS/'data-results.json').read_text())
    pg=json.loads((DOCS/'postgres-results.json').read_text())
    by_size={d['rows']:d for d in data['datasets']}
    assert set(by_size)=={1_000_000,10_000_000},'Both final dataset sizes required'
    assert all(d['query_window']['day_rows']==3840 for d in by_size.values())
    assert pg['rows']==1_000_000 and pg['query_window']['day_rows']==3840
    lines=['# Wyniki pomiarów danych','',
           'Wygenerowano z `data-results.json` i `postgres-results.json` przez `scripts/research/summarize_data.py`.',
           'Wszystkie czasy poniżej to **mediany sześciu rozgrzanych wykonań**, bez sieci i UI. Pełna metoda i ograniczenia: [data-evaluation.md](data-evaluation.md).','',
           '## Ten sam zbiór i zapytania','',
           '| Zapytanie | SQLite 1 mln | DuckDB/Parquet 1 mln | SQLite 10 mln | DuckDB/Parquet 10 mln |',
           '| --- | ---: | ---: | ---: | ---: |']
    for key,label in [('day_timeline_page','Strona osi dnia, 500 rekordów'),('day_app_totals','Sumy aplikacji, pełny dzień'),
                      ('year_app_totals','Sumy aplikacji, ostatni dostępny rok'),('history_app_totals','Sumy aplikacji, cała historia')]:
        cells=[f"{by_size[n]['query_timings'][e][key]['median_ms']:.2f} ms" for n in [1_000_000,10_000_000] for e in ['sqlite','duckdb_parquet']]
        lines.append('| '+label+' | '+' | '.join(cells)+' |')
    lines+=['','Przy 1 mln dostępnych jest mniej niż 365 dni. Sumy aplikacji dotyczą ekspozycji foreground z urządzeń; nie są miarą ludzkiej uwagi ani czasem osoby po deduplikacji.','',
            '## Kształt zapytań i agregaty SQLite','',
            '| Operacja | 1 mln | 10 mln |','| --- | ---: | ---: |']
    for key,label in [('date_function_day_count','COUNT dnia z funkcją date na kolumnie'),('range_day_count','COUNT dnia przez indeks zakresu'),
                      ('year_rollup_app_totals','Rok z projekcji dziennych'),('history_rollup_app_totals','Historia z projekcji dziennych')]:
        cells=[f"{by_size[n]['query_timings']['sqlite'][key]['median_ms']:.2f} ms" for n in [1_000_000,10_000_000]]
        lines.append('| '+label+' | '+' | '.join(cells)+' |')
    lines+=['','Porównanie predykatów używa tej samej tabeli eksperymentalnej; nie jest uruchomieniem starego FocusWatch. Wyniki projekcji sprawdzono względem zapytań surowych.','',
            '## Rozmiar reprezentacji','',
            '| Reprezentacja | 1 mln | 10 mln |','| --- | ---: | ---: |']
    for key,label in [('sqlite_indexed_bytes','SQLite, tabela i indeksy'),('rollup_additional_bytes','Dodatkowe projekcje dzienne'),('parquet_zstd_bytes','Parquet/ZSTD')]:
        cells=[f"{by_size[n][key]/1e6:.2f} MB" for n in [1_000_000,10_000_000]]
        lines.append('| '+label+' | '+' | '.join(cells)+' |')
    large=by_size[10_000_000]
    lines+=['',f"Przy 10 mln: SQLite **{large['sqlite_bytes_per_observation']:.1f} B/obserwację**, Parquet **{large['parquet_bytes_per_observation']:.1f} B/obserwację**. Próbka JSON z obiektem payload: **{large['sample_json_nested_payload_wire_bytes_mean']:.1f} B/obserwację**.",
            'Wartości nie są zamienne. SQLite ma indeksy potrzebne do małych odczytów; Parquet inną organizację i kompresję. Dane są syntetyczne i uporządkowane, bez szyfrowania. Koszt chmury używa marginesów i analizy wrażliwości, nie kopiuje bezkrytycznie współczynnika kompresji.','',
            '## PostgreSQL, 1 mln tych samych obserwacji','',
            f"Tabela i indeksy: **{pg['storage']['total_bytes']/1e6:.2f} MB**, czyli **{pg['storage']['total_bytes_per_observation']:.1f} B/obserwację**, bez repliki, backupu i zapasu na wzrost/bloat. Schema ma dodatkowe account_id, UUID i JSONB; nie jest identyczna fizycznie z SQLite.",'',
            '| Zapytanie | Mediana lokalnie |','| --- | ---: |']
    for key,label in [('day_timeline_page','Strona osi dnia'),('day_app_totals','Sumy dnia'),('year_app_totals','Dostępny rok'),('history_app_totals','Cała historia')]:
        lines.append(f"| {label} | {pg['query_timings'][key]['median_ms']:.2f} ms |")
    samples=sorted(pg['durable_ingestion_batches']['samples_ms'])
    lines+=['',f"200 sekwencyjnych trwałych transakcji po osiem obserwacji: mediana **{statistics.median(samples):.2f} ms**, empiryczny 95. percentyl **{samples[int(.95*len(samples))-1]:.2f} ms**. Retry pierwszej paczki nie zwiększył liczby zapisów.",
            'To klient przez lokalny Unix socket. Nie ma HTTP/TLS, autoryzacji ani równoległych użytkowników. Nie wolno przeliczać odwrotności tego czasu na obiecaną przepustowość usługi chmurowej.','',
            '## Wniosek','',
            'SQLite z indeksami i odbudowywalnymi projekcjami jest uzasadnioną bazą lokalnego rdzenia. Rozmiar historii sam w sobie nie wymaga DuckDB w każdym kliencie. DuckDB/Parquet ma odrębną rolę w skanach i archiwach; jego wdrożenie należy powiązać z konkretną potrzebą analityczną.',
            'PostgreSQL pozostaje kandydatem operacyjnej chmury dzięki transakcjom, zapytaniom i modelowi wielu kont. Ta próba potwierdza działanie proponowanego wzorca, nie ustala maksymalnej skali komercyjnej ani zwycięzcy języków backendu.','']
    (DOCS/'data-results.md').write_text('\n'.join(lines))


if __name__=='__main__':
    main()
