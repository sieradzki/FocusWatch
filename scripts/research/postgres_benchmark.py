#!/usr/bin/env python3
"""Disposable local PostgreSQL probe on the exact synthetic Parquet dataset.

Creates its own cluster, Unix socket only, port54391; no existing PG connections.
Default retained cluster in ignored build/research/pgdata for reproducibility.
It always stops its server in finally. No cloud capacity/latency claims.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

import duckdb
import psycopg

from data_benchmark import EPOCH, DAY, PER_DAY, timed, qpath


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--parquet',type=Path,default=Path('build/research/data/observations-1000000.parquet'))
    parser.add_argument('--cluster',type=Path,default=Path('build/research/pgdata'))
    parser.add_argument('--output',type=Path,default=Path('docs/research/2026-09/postgres-results.json'))
    args=parser.parse_args()
    cluster=args.cluster.resolve()
    if cluster.exists():
        raise SystemExit('Refusing to overwrite an existing cluster; choose another --cluster')
    cluster.parent.mkdir(parents=True,exist_ok=True)
    socket=cluster.parent/'pgsocket'
    socket.mkdir(exist_ok=True,mode=0o700)
    subprocess.run(['initdb','-D',str(cluster),'--auth-local=trust','--auth-host=reject','--no-instructions'],check=True,capture_output=True)
    options=f"-c listen_addresses='' -c unix_socket_directories='{socket}' -p 54391 -c shared_buffers=128MB -c max_connections=10 -c max_parallel_workers_per_gather=2"
    subprocess.run(['pg_ctl','-D',str(cluster),'-l',str(cluster.parent/'postgres-experiment.log'),'-o',options,'-w','start'],check=True,capture_output=True)
    result={"measured_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "environment":{"platform":platform.platform(),"python":platform.python_version()},
            "limitations":["local Unix socket, no cloud network/TLS","one tenant historical dataset, not commercial concurrency capacity",
                           "indexes built after bulk COPY, bulk load is not online ingestion throughput",
                           "warm OS page cache, no cold-cache control","no HA/replica/backup byte multiplier included",
                           "schema uses uuid/jsonb vs SQLite text; physical size is concrete schema-specific, not engine-only ranking"]}
    try:
        con=psycopg.connect(host=str(socket),port=54391,dbname='postgres')
        result['environment']['postgres']=con.execute('SELECT version()').fetchone()[0]
        result['environment']['settings']={name:con.execute('SHOW '+name).fetchone()[0] for name in ['fsync','synchronous_commit','shared_buffers','max_parallel_workers_per_gather']}
        con.execute('''CREATE TABLE observations(
           account_id integer NOT NULL DEFAULT 1, event_id uuid NOT NULL,
           device_id integer NOT NULL, source_id integer NOT NULL, seq bigint NOT NULL,
           schema_version integer NOT NULL, start_ms bigint NOT NULL, end_ms bigint NOT NULL,
           app_id integer NOT NULL, category_id integer NOT NULL, payload jsonb NOT NULL,
           CHECK(end_ms>=start_ms))''')
        con.commit()
        d=duckdb.connect();d.execute("SET threads=2;SET memory_limit='512MB'")
        source=d.execute(f'SELECT * FROM read_parquet({qpath(args.parquet.resolve())})')
        start=time.perf_counter();count=0
        with con.cursor().copy('COPY observations(event_id,device_id,source_id,seq,schema_version,start_ms,end_ms,app_id,category_id,payload) FROM STDIN') as copy:
            while rows:=source.fetchmany(10000):
                for row in rows:
                    copy.write_row(row)
                count+=len(rows)
        con.commit();result['bulk_copy_seconds']=time.perf_counter()-start
        start=time.perf_counter()
        con.execute('ALTER TABLE observations ADD PRIMARY KEY(account_id,event_id)')
        con.execute('CREATE UNIQUE INDEX observation_sequence ON observations(account_id,device_id,source_id,seq)')
        con.execute('CREATE INDEX observation_time ON observations(account_id,start_ms,end_ms)')
        con.execute('CREATE INDEX observation_source_time ON observations(account_id,source_id,start_ms,app_id,end_ms)')
        con.commit();result['index_build_seconds']=time.perf_counter()-start
        con.autocommit=True
        con.execute('VACUUM ANALYZE observations')
        result['rows']=count
        result['storage']={name:con.execute(f"SELECT {fn}('observations')").fetchone()[0] for name,fn in [('table_bytes','pg_table_size'),('indexes_bytes','pg_indexes_size'),('total_bytes','pg_total_relation_size')]}
        result['storage']['total_bytes_per_observation']=result['storage']['total_bytes']/count
        # Compare a complete day, never the short trailing partial day.
        lastday=max(0,(count//PER_DAY)-1);lo=EPOCH+lastday*DAY;hi=lo+DAY;yearlo=max(EPOCH,hi-365*DAY)
        result['query_window']={'day_start_ms':lo,'day_end_ms':hi,'day_rows':min(count,PER_DAY),
                                'year_start_ms':yearlo,'year_end_ms':hi}
        queries={
          'day_timeline_page':('SELECT event_id,device_id,source_id,seq,schema_version,start_ms,end_ms,app_id,category_id,payload FROM observations WHERE account_id=1 AND start_ms>=%s AND start_ms<%s ORDER BY start_ms,event_id LIMIT 500',(lo,hi)),
          'day_app_totals':('SELECT app_id,SUM(end_ms-start_ms) FROM observations WHERE account_id=1 AND source_id=0 AND start_ms>=%s AND start_ms<%s GROUP BY app_id ORDER BY app_id',(lo,hi)),
          'year_app_totals':('SELECT app_id,SUM(end_ms-start_ms) FROM observations WHERE account_id=1 AND source_id=0 AND start_ms>=%s AND start_ms<%s GROUP BY app_id ORDER BY app_id',(yearlo,hi)),
          'history_app_totals':('SELECT app_id,SUM(end_ms-start_ms) FROM observations WHERE account_id=1 AND source_id=0 GROUP BY app_id ORDER BY app_id',())}
        result['query_timings']={}
        for name,(q,params) in queries.items():
            metric,rows=timed(lambda:con.execute(q,params).fetchall())
            metric['query_plan']=con.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+q,params).fetchone()[0]
            expected=d.execute(q.replace('account_id=1 AND ','').replace('%s','?').replace('observations',f'read_parquet({qpath(args.parquet.resolve())})'),params).fetchall()
            if name=='day_timeline_page':
                rows=[(row[0].hex,*row[1:]) for row in rows]
                expected=[(*row[:-1],json.loads(row[-1])) for row in expected]
            assert rows==expected,name
            result['query_timings'][name]=metric
        # Transactional durable batches, eight observations = two devices x two
        # sources x two 30-second checkpoints; sequential single client.
        con.autocommit=False
        ingest=[]
        for batch in range(200):
            start=time.perf_counter()
            for i in range(8):
                number=batch*8+i
                con.execute('''INSERT INTO observations VALUES(2,%s,%s,%s,%s,1,%s,%s,1,1,%s)
                   ON CONFLICT(account_id,event_id) DO NOTHING''',
                   (hashlib.md5(f'network-batch-{number}'.encode()).hexdigest(),i%2,(i//2)%2,number//4,hi+(number//4)*30000,hi+(number//4+1)*30000,json.dumps({'title':'Synthetic ingestion'})))
            con.commit();ingest.append((time.perf_counter()-start)*1000)
        result['durable_ingestion_batches']={'batch_size':8,'batches':len(ingest),'samples_ms':ingest,
          'meaning':'single sequential client, local socket, full durability; not max throughput or WAN latency'}
        assert con.execute('SELECT COUNT(*) FROM observations WHERE account_id=2').fetchone()[0]==1600
        start=time.perf_counter()
        for i in range(8):
            con.execute('''INSERT INTO observations VALUES(2,%s,%s,%s,%s,1,%s,%s,1,1,%s)
               ON CONFLICT(account_id,event_id) DO NOTHING''',
               (hashlib.md5(f'network-batch-{i}'.encode()).hexdigest(),i%2,(i//2)%2,i//4,hi+(i//4)*30000,hi+(i//4+1)*30000,json.dumps({'title':'Synthetic ingestion'})))
        con.commit()
        result['durable_ingestion_batches']['retry_first_batch_ms']=(time.perf_counter()-start)*1000
        assert con.execute('SELECT COUNT(*) FROM observations WHERE account_id=2').fetchone()[0]==1600
        result['correctness']='aggregation exact equality against DuckDB;1600 durable inserted rows; exact retry adds zero rows'
        result['limitations'].append('PG retry uses ON CONFLICT only: conflicting-payload validation is a separate protocol requirement, not implemented in this throughput probe')
        con.close();d.close()
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k not in ['query_timings','durable_ingestion_batches']},indent=2))
    finally:
        subprocess.run(['pg_ctl','-D',str(cluster),'-m','fast','-w','stop'],check=True,capture_output=True)


if __name__=='__main__':
    main()
