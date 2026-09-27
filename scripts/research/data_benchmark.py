#!/usr/bin/env python3
"""Reproducible synthetic storage/query experiment; never reads FocusWatch data.

Run with duckdb and psutil installed, from the repository root. Generated databases
belong in ignored build/research on disk (not /tmp, often tmpfs). Timings are warm,
single-user local measurements, NOT cloud capacity or application benchmarks.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import sqlite3
import statistics
import time

import duckdb
import psutil

DAY = 86_400_000
EPOCH = 1_577_836_800_000
PER_DAY = 3840


def timed(query, repeats=7):
    samples = []
    result = None
    for _ in range(repeats):
        start = time.perf_counter()
        result = query()
        samples.append((time.perf_counter() - start) * 1000)
    return {"first_ms": samples[0], "median_ms": statistics.median(samples[1:]),
            "warm_min_ms": min(samples[1:]), "warm_max_ms": max(samples[1:]),
            "samples_ms": samples, "result_rows": len(result)}, result


def qpath(path):
    return "'" + str(path).replace("'", "''") + "'"


def run(count, directory, repeats, reuse=False):
    directory.mkdir(parents=True, exist_ok=True)
    parquet = directory / f"observations-{count}.parquet"
    sqlfile = directory / f"observations-{count}.sqlite"
    if not reuse and (parquet.exists() or sqlfile.exists()):
        raise SystemExit(f"Refusing to overwrite experiment: {parquet} / {sqlfile}")
    if reuse and not (parquet.exists() and sqlfile.exists()):
        raise SystemExit('--reuse requires both complete generated files')
    d = duckdb.connect()
    d.execute("SET threads=2; SET memory_limit='512MB'")
    d.execute(f"SET temp_directory={qpath(directory / 'duckdb-temp')}")
    # Four parallel streams: two devices, each foreground + media. Observations
    # are 30-second checkpoints, NOT four independent slices of a person's time.
    generate = f"""
      SELECT md5('focuswatch-experiment-' || i::VARCHAR) AS event_id,
             (i % 2)::INTEGER AS device_id, ((i // 2) % 2)::INTEGER AS source_id,
             (i // 4)::BIGINT AS seq, 1::INTEGER AS schema_version,
             {EPOCH} + (i // {PER_DAY}) * {DAY} + 28800000
                 + ((i % {PER_DAY}) // 4) * 30000 AS start_ms,
             start_ms + 30000 AS end_ms,
             ((i // 28) % 32)::INTEGER AS app_id,
             ((i // 28) % 8)::INTEGER AS category_id,
             json_object('title', 'Synthetic document ' || (i % 100003)::VARCHAR
                         || ' ' || md5((i % 100003)::VARCHAR),
                         'url', 'https://example.invalid/project/' || (i % 4096)::VARCHAR
                         || '/item/' || md5((i % 100003)::VARCHAR),
                         'project', 'project-' || (i % 16)::VARCHAR,
                         'audible', (i % 4 >= 2), 'visibility', 'unknown',
                         'capture_version', 'experiment-1', 'confidence', 'observed',
                         'timezone', 'Europe/Warsaw')::VARCHAR AS payload
      FROM range({count}) AS t(i)
    """
    generation_s = None
    if not reuse:
        started = time.perf_counter()
        d.execute(f"COPY ({generate}) TO {qpath(parquet)} (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 122880)")
        generation_s = time.perf_counter() - started
    d.execute(f"CREATE VIEW observations AS SELECT * FROM read_parquet({qpath(parquet)})")
    sample = d.execute("SELECT * FROM observations LIMIT 10000").fetchall()
    columns = [x[0] for x in d.description]
    wire_sizes = [len(json.dumps(dict(zip(columns, row)), separators=(',', ':')).encode()) for row in sample]
    nested_wire_sizes = []
    for row in sample:
        obj = dict(zip(columns, row))
        obj['payload'] = json.loads(obj['payload'])
        nested_wire_sizes.append(len(json.dumps(obj, separators=(',', ':')).encode()))

    s = sqlite3.connect(sqlfile)
    s.executescript("""
      PRAGMA journal_mode=WAL;
      PRAGMA synchronous=FULL;
      PRAGMA cache_size=-65536;
      PRAGMA temp_store=FILE;
      CREATE TABLE IF NOT EXISTS observations (
        event_id TEXT NOT NULL PRIMARY KEY, device_id INTEGER NOT NULL,
        source_id INTEGER NOT NULL, seq INTEGER NOT NULL, schema_version INTEGER NOT NULL,
        start_ms INTEGER NOT NULL, end_ms INTEGER NOT NULL,
        app_id INTEGER NOT NULL, category_id INTEGER NOT NULL, payload TEXT NOT NULL,
        UNIQUE(device_id, source_id, seq), CHECK(end_ms >= start_ms)
      );
    """)
    load_s = index_s = None
    if not reuse:
        started = time.perf_counter()
        cursor = d.execute("SELECT * FROM observations")
        while rows := cursor.fetchmany(10000):
            s.executemany("INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
            s.commit()
        load_s = time.perf_counter() - started
        started = time.perf_counter()
        s.execute("CREATE INDEX observation_time ON observations(start_ms, end_ms)")
        s.execute("CREATE INDEX observation_source_time ON observations(source_id, start_ms, app_id, end_ms)")
        s.execute("ANALYZE")
        s.commit()
        index_s = time.perf_counter() - started
    assert s.execute('SELECT COUNT(*) FROM observations').fetchone()[0] == count
    assert d.execute('SELECT COUNT(*) FROM observations').fetchone()[0] == count
    s.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    raw_bytes = s.execute("SELECT SUM(pgsize) FROM dbstat WHERE name='observations' OR name LIKE 'sqlite_autoindex_observations_%' OR name IN ('observation_time','observation_source_time')").fetchone()[0]

    # Use a complete day at both sizes, not a trailing partial day of different size.
    last_day = max(0, count // PER_DAY - 1)
    lo = EPOCH + last_day * DAY
    hi = lo + DAY
    year_lo = max(EPOCH, hi - 365 * DAY)
    common = {
        "day_timeline_page": ("SELECT * FROM observations WHERE start_ms>=? AND start_ms<? ORDER BY start_ms,event_id LIMIT 500", (lo, hi)),
        "day_app_totals": ("SELECT app_id,SUM(end_ms-start_ms) FROM observations WHERE source_id=0 AND start_ms>=? AND start_ms<? GROUP BY app_id ORDER BY app_id", (lo, hi)),
        "year_app_totals": ("SELECT app_id,SUM(end_ms-start_ms) FROM observations WHERE source_id=0 AND start_ms>=? AND start_ms<? GROUP BY app_id ORDER BY app_id", (year_lo, hi)),
        "history_app_totals": ("SELECT app_id,SUM(end_ms-start_ms) FROM observations WHERE source_id=0 GROUP BY app_id ORDER BY app_id", ()),
    }
    measurements = {"sqlite": {}, "duckdb_parquet": {}}
    for name, (query, params) in common.items():
        a, ar = timed(lambda: s.execute(query, params).fetchall(), repeats)
        b, br = timed(lambda: d.execute(query, params).fetchall(), repeats)
        assert ar == br, f"Different query results: {name}"
        a["query_plan"] = s.execute("EXPLAIN QUERY PLAN " + query, params).fetchall()
        measurements["sqlite"][name] = a
        measurements["duckdb_parquet"][name] = b

    # This is a controlled predicate experiment on the SAME table. It is not a
    # timing of the old ORM/UI, which additionally materializes Python objects.
    date = dt.datetime.fromtimestamp(lo / 1000, dt.timezone.utc).date().isoformat()
    measurements["sqlite"]["date_function_day_count"], old = timed(
        lambda: s.execute("SELECT COUNT(*) FROM observations WHERE date(start_ms/1000,'unixepoch')=?", (date,)).fetchall(), repeats)
    measurements["sqlite"]["range_day_count"], new = timed(
        lambda: s.execute("SELECT COUNT(*) FROM observations WHERE start_ms>=? AND start_ms<?", (lo,hi)).fetchall(), repeats)
    assert old == new

    rollup_build_s = None
    if not reuse:
        started = time.perf_counter()
        s.executescript(f"""
      CREATE TABLE daily AS SELECT CAST((start_ms-{EPOCH})/{DAY} AS INTEGER) AS day,
        device_id, source_id, app_id, category_id, SUM(end_ms-start_ms) AS duration_ms
        FROM observations GROUP BY day,device_id,source_id,app_id,category_id;
      CREATE INDEX daily_range ON daily(source_id,day,app_id,duration_ms);
        """)
        s.commit()
        rollup_build_s = time.perf_counter() - started
    s.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    rollup_bytes = s.execute("SELECT SUM(pgsize) FROM dbstat WHERE name IN ('daily','daily_range')").fetchone()[0]
    for name, lower in [("year", (year_lo-EPOCH)//DAY), ("history", 0)]:
        upper = (hi-EPOCH)//DAY if name == 'year' else count//PER_DAY+1
        q = "SELECT app_id,SUM(duration_ms) FROM daily WHERE source_id=0 AND day>=? AND day<? GROUP BY app_id ORDER BY app_id"
        metric, rows = timed(lambda: s.execute(q, (lower,upper)).fetchall(), repeats)
        raw = s.execute(*common[f"{name}_app_totals"]).fetchall()
        assert rows == raw, f"Rollup does not match raw: {name}"
        measurements["sqlite"][f"{name}_rollup_app_totals"] = metric

    result = {
        "rows": count, "days": count/PER_DAY, "years_at_3840_events_per_day": count/PER_DAY/365,
        "generate_parquet_seconds": generation_s, "sqlite_load_seconds": load_s,
        "sqlite_index_build_seconds": index_s, "rollup_build_seconds": rollup_build_s,
        "sqlite_indexed_bytes": raw_bytes, "sqlite_bytes_per_observation": raw_bytes/count,
        "parquet_zstd_bytes": parquet.stat().st_size, "parquet_bytes_per_observation": parquet.stat().st_size/count,
        "rollup_additional_bytes": rollup_bytes, "rollup_rows": s.execute("SELECT COUNT(*) FROM daily").fetchone()[0],
        "sample_json_escaped_payload_wire_bytes_mean": statistics.mean(wire_sizes),
        "sample_json_nested_payload_wire_bytes_mean": statistics.mean(nested_wire_sizes),
        "dataset_reused": reuse, "sqlite_total_file_bytes": sqlfile.stat().st_size,
        "query_window": {"day_start_ms":lo,"day_end_ms":hi,"day_rows":new[0][0],"year_start_ms":year_lo,"year_end_ms":hi},
        "query_timings": measurements,
        "correctness": "exact result equality SQLite vs DuckDB and raw vs daily aggregates",
        "limitations": ["synthetic metadata, no personal data", "warm local disk/cache, no cold-cache control",
                        "fixed 30s spans, no midnight overlaps in performance dataset; semantics tested separately",
                        "totals are source/device exposure, not deduplicated human attention",
                        "load batches 10000, secondary time indexes built afterwards: not production ingestion throughput",
                        "sorted timestamps, fixed spans, correlated categorical fields: compression is not a prediction for real data",
                        "SQLite raw bytes count table+indexes, excluding daily aggregates, catalog and free pages",
                        "no encryption or network costs measured", "no concurrent writer workload in these query timings"],
    }
    s.close()
    d.close()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rows', type=int, nargs='+', default=[1_000_000, 10_000_000])
    parser.add_argument('--data-dir', type=Path, default=Path('build/research/data'))
    parser.add_argument('--output', type=Path, default=Path('docs/research/2026-09/data-results.json'))
    parser.add_argument('--repeats', type=int, default=7)
    parser.add_argument('--reuse', action='store_true', help='Remeasure existing complete synthetic datasets without regenerating')
    args = parser.parse_args()
    assert args.repeats >= 3 and all(x > 0 for x in args.rows)
    report = {"measured_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "environment": {"platform": platform.platform(), "python": platform.python_version(),
                              "sqlite": sqlite3.sqlite_version, "duckdb": duckdb.__version__,
                              "cpu": next((line.strip().split(': ',1)[-1] for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')), 'unknown'),
                              "ram_bytes": psutil.virtual_memory().total, "available_ram_before": psutil.virtual_memory().available,
                              "load_average_before": os.getloadavg(), "duckdb_threads": 2,
                              "duckdb_memory_limit": "512MB", "sqlite_cache": "64MiB", "sqlite_synchronous": "FULL"},
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "datasets": []}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for n in args.rows:
        print(f"START rows={n}", flush=True)
        report['datasets'].append(run(n, args.data_dir, args.repeats, args.reuse))
        report['environment']['load_average_after'] = os.getloadavg()
        args.output.write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({k: v for k,v in report['datasets'][-1].items() if k != 'query_timings'}), flush=True)


if __name__ == '__main__':
    main()
