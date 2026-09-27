#!/usr/bin/env python3
"""Executable architecture experiments, not production sync implementation.

Uses only temporary synthetic databases. Process exits model process crashes;
they do not simulate power loss, filesystem corruption or network transport.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from zoneinfo import ZoneInfo


def connect(path):
    con = sqlite3.connect(path)
    con.executescript('''
      PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA foreign_keys=ON;
      CREATE TABLE IF NOT EXISTS observation(id TEXT PRIMARY KEY, body TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY REFERENCES observation(id));
    ''')
    return con


def receive(con, event_id, body):
    """Serial exact retry only; concurrent ingestion needs atomic conflict handling."""
    prior = con.execute('SELECT body FROM observation WHERE id=?', (event_id,)).fetchone()
    if prior:
        if prior[0] != body:
            raise ValueError('Same identity with different immutable payload')
        return
    con.execute('INSERT INTO observation VALUES (?,?)', (event_id, body))


def union_duration(spans):
    end = None
    total = 0
    for start, stop in sorted(spans):
        if stop < start:
            raise ValueError('Negative interval')
        total += max(0, stop - max(start, end if end is not None else start))
        end = max(stop, end if end is not None else stop)
    return total


def clipped_duration(spans, lower, upper):
    return union_duration([(max(s,lower), min(e,upper)) for s,e in spans if e>lower and s<upper])


class ArchitectureExperiments(unittest.TestCase):
    def test_parallel_foreground_and_stream_preserve_both_without_double_person_time(self):
        foreground = [(0,1800), (600,1200)]  # second device overlaps first
        media = [(0,1800)]
        self.assertEqual(sum(e-s for s,e in foreground+media), 4200)
        self.assertEqual(union_duration(foreground), 1800)
        self.assertEqual(union_duration(media), 1800)
        self.assertEqual(union_duration(foreground+media), 1800)
        # This says presence/exposure, not attention or productivity.

    def test_nested_intervals_and_gaps(self):
        self.assertEqual(union_duration([(0,100),(10,20),(30,50),(110,120)]),110)

    def test_midnight_split_without_loss(self):
        spans = [(86300,86500)]
        self.assertEqual(clipped_duration(spans,0,86400),100)
        self.assertEqual(clipped_duration(spans,86400,172800),100)

    def test_local_report_days_can_have_23_or_25_hours(self):
        zone = ZoneInfo('Europe/Warsaw')
        for date, hours in [(dt.date(2026,3,29),23),(dt.date(2026,10,25),25)]:
            lower = dt.datetime.combine(date,dt.time(),zone).timestamp()
            upper = dt.datetime.combine(date+dt.timedelta(days=1),dt.time(),zone).timestamp()
            self.assertEqual(upper-lower,hours*3600)

    def test_backward_wall_clock_does_not_make_negative_elapsed(self):
        wall_start, wall_end = 1000, 900
        mono_start, mono_end = 40, 70
        elapsed = mono_end-mono_start
        clock_discontinuity = abs((wall_end-wall_start)-elapsed)>5
        self.assertEqual(elapsed,30)
        self.assertTrue(clock_discontinuity)
        # Collector must expose uncertainty: monotonic time is not comparable
        # across devices, nor does it provide portable suspend semantics alone.

    def test_process_crash_keeps_observation_and_outbox_atomic(self):
        with tempfile.TemporaryDirectory(prefix='focuswatch-sync-experiment-') as folder:
            for commit in [False,True]:
                db = Path(folder)/f'crash-{commit}.sqlite'
                connect(db).close()
                code = '''import sqlite3,os,sys
c=sqlite3.connect(sys.argv[1]);c.execute('PRAGMA synchronous=FULL')
c.execute("INSERT INTO observation VALUES ('a','synthetic')")
c.execute("INSERT INTO outbox VALUES ('a')")
if sys.argv[2]=='commit': c.commit()
os._exit(17)
'''
                done = subprocess.run([sys.executable,'-c',code,str(db),'commit' if commit else 'rollback'],check=False)
                self.assertEqual(done.returncode,17)
                con = connect(db)
                self.assertEqual(con.execute('PRAGMA integrity_check').fetchone()[0],'ok')
                expected = int(commit)
                self.assertEqual(con.execute('SELECT COUNT(*) FROM observation').fetchone()[0],expected)
                self.assertEqual(con.execute('SELECT COUNT(*) FROM outbox').fetchone()[0],expected)
                con.close()

    def test_lost_ack_retry_is_idempotent_and_mismatched_duplicate_rejected(self):
        with tempfile.TemporaryDirectory(prefix='focuswatch-sync-experiment-') as folder:
            server = connect(Path(folder)/'server.sqlite')
            receive(server,'device1:stream1:1','synthetic');server.commit()
            # ACK lost: reconnect and resend same observation after durable commit.
            server.close();server=connect(Path(folder)/'server.sqlite')
            receive(server,'device1:stream1:1','synthetic');server.commit()
            self.assertEqual(server.execute('SELECT COUNT(*) FROM observation').fetchone()[0],1)
            with self.assertRaises(ValueError):
                receive(server,'device1:stream1:1','different')
            server.close()

    def test_out_of_order_delivery_does_not_ack_missing_sequence(self):
        received = {1,3,4}
        acknowledged = 0
        while acknowledged+1 in received:
            acknowledged += 1
        self.assertEqual(acknowledged,1)
        received.add(2)
        while acknowledged+1 in received:
            acknowledged += 1
        self.assertEqual(acknowledged,4)

    def test_concurrent_wal_reader_sees_snapshot_while_writer_commits(self):
        with tempfile.TemporaryDirectory(prefix='focuswatch-sync-experiment-') as folder:
            db=Path(folder)/'concurrent.sqlite'
            writer=connect(db);reader=connect(db)
            reader.execute('BEGIN')
            self.assertEqual(reader.execute('SELECT COUNT(*) FROM observation').fetchone()[0],0)
            receive(writer,'a','synthetic');writer.commit()
            self.assertEqual(reader.execute('SELECT COUNT(*) FROM observation').fetchone()[0],0)
            reader.commit()
            self.assertEqual(reader.execute('SELECT COUNT(*) FROM observation').fetchone()[0],1)
            reader.close();writer.close()

    def test_deleted_generation_is_not_resurrected_by_offline_queue(self):
        # Minimal proof of epoch precondition, not a complete selective deletion
        # protocol. Never silently re-label queued events with the current epoch.
        server_epoch=2
        queued_event={'id':'a','collection_epoch':1}
        self.assertNotEqual(queued_event['collection_epoch'],server_epoch)
        accepted=[]
        if queued_event['collection_epoch']==server_epoch:
            accepted.append(queued_event)
        self.assertEqual(accepted,[])


def main():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ArchitectureExperiments)
    names=[test.id().split('.')[-1] for test in suite]
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    output=Path('docs/research/2026-09/sync-semantics-results.json')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'measured_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
      'tests':names,'run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
      'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'limitations':['architecture experiments, no production transport/authentication',
                    'process crashes, not power failure','epoch test covers full collection reset only',
                    'serial retry; concurrent requests and deletion races are not exercised',
                    'no AI accuracy, attention or productivity validation']},indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())


if __name__=='__main__':
    main()
