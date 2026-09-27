#!/usr/bin/env python3
"""Local synthetic Axum WS memory/latency probe, no cloud capacity claim.

--prepare downloads only dependencies, no compilation. --build compiles jobs=2.
--run launches isolated ephemeral-loopback server and separate Node clients.
Server affinity=one available CPU; clients another. No TLS/auth/PG/source capture.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import queue
import shutil
import signal
import subprocess
import threading
import time
import urllib.request

import psutil

ROOT = Path(__file__).resolve().parents[2]
SOURCES = Path(__file__).parent
WORK = ROOT / 'build/research/realtime'
OUTPUT = ROOT / 'docs/research/2026-09/realtime-results.json'


def prepare():
    (WORK/'src').mkdir(parents=True,exist_ok=True)
    shutil.copy2(SOURCES/'realtime_probe.rs', WORK/'src/main.rs')
    (WORK/'Cargo.toml').write_text('''[package]
name = "focuswatch-realtime-probe"
version = "0.1.0"
edition = "2021"
[dependencies]
axum = { version = "=0.8.9", features = ["ws"] }
tokio = { version = "=1.53.1", features = ["macros", "rt-multi-thread", "net", "sync", "time"] }
serde = { version = "=1.0.229", features = ["derive"] }
serde_json = "=1.0.151"
futures-util = "=0.3.34"
[profile.release]
opt-level = 2
debug = false
''')
    lock=SOURCES/'realtime_probe_cargo.lock'
    if lock.exists(): shutil.copy2(lock,WORK/'Cargo.lock')
    subprocess.run(['cargo','+stable','fetch'],cwd=WORK,check=True)
    shutil.copy2(WORK/'Cargo.lock',lock)


def snapshot(pid):
    p=psutil.Process(pid)
    cpu=p.cpu_times()
    return {'wall':time.monotonic(),'cpu':cpu.user+cpu.system,
            'pss_bytes':p.memory_full_info().pss,'rss_bytes':p.memory_info().rss}


def stop(process):
    if process is None: return
    try:
        os.killpg(process.pid,signal.SIGTERM)
        process.wait(timeout=3)
    except (ProcessLookupError,subprocess.TimeoutExpired):
        try: os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=3)
        except ProcessLookupError: pass


def pinned(cpu):
    return lambda: os.sched_setaffinity(0,{cpu})


def run(count,seconds,server_cpu,client_cpu):
    server=client=None
    records=[];boundaries={};client_result=None
    try:
        server=subprocess.Popen([str(WORK/'target/release/focuswatch-realtime-probe')],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True,
            preexec_fn=pinned(server_cpu))
        line=server.stdout.readline()
        if not line.startswith('READY '): raise RuntimeError(line+server.stderr.read())
        port=int(line.split()[1])
        empty=snapshot(server.pid)
        client=subprocess.Popen(['node',str(SOURCES/'realtime_probe_client.cjs'),str(port),str(count),str(seconds)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True,
            preexec_fn=pinned(client_cpu))
        messages=queue.Queue()
        def reader():
            for line in client.stdout: messages.put(json.loads(line))
        thread=threading.Thread(target=reader,daemon=True);thread.start()
        phase='connecting';deadline=time.monotonic()+seconds+60
        while time.monotonic()<deadline:
            try:
                while True:
                    event=messages.get_nowait()
                    phase=event['phase'];boundaries[phase]=snapshot(server.pid)
                    if phase=='error': raise RuntimeError(event['error'])
                    if phase=='done': client_result=event['result']
            except queue.Empty: pass
            snap=snapshot(server.pid);snap['phase']=phase;records.append(snap)
            if client_result is not None: break
            if client.poll() is not None:
                thread.join(timeout=1)
                if messages.empty(): raise RuntimeError('client ended without result: '+client.stderr.read())
            time.sleep(.05)
        if client_result is None: raise RuntimeError('client timed out')
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/metrics',timeout=2) as response:
            metrics=json.load(response)
        assert metrics['accepted']==client_result['received']==metrics['delivered'],metrics
        assert metrics['rejected']==2,metrics
        assert metrics['latest_records']==count,metrics
        phases={}
        for name,end in [('idle','steady'),('steady','burst'),('burst','done')]:
            first,last=boundaries[name],boundaries[end]
            elapsed=last['wall']-first['wall'];cpu=last['cpu']-first['cpu']
            sample=[r for r in records if r['phase']==name]+[first,last]
            phases[name]={'seconds':elapsed,'server_cpu_seconds':cpu,
                'server_percent_one_cpu':cpu/elapsed*100,
                'server_peak_pss_bytes':max(r['pss_bytes'] for r in sample),
                'server_peak_rss_bytes':max(r['rss_bytes'] for r in sample)}
        print(json.dumps({'connections':count,'phases':phases,'latency':client_result['latency']}),flush=True)
        return {'connections':count,'empty_server':empty,'phases':phases,
                'client_result':client_result,'server_counters':metrics,
                'samples':records}
    finally:
        stop(client);stop(server)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prepare',action='store_true');p.add_argument('--build',action='store_true')
    p.add_argument('--run',action='store_true');p.add_argument('--counts',nargs='+',type=int,default=[250,500,1000])
    p.add_argument('--seconds',type=float,default=15);args=p.parse_args()
    assert all(n>=100 and n%2==0 for n in args.counts)
    assert 0<args.seconds<30
    if args.prepare: prepare()
    if args.build:
        shutil.copy2(SOURCES/'realtime_probe.rs',WORK/'src/main.rs')
        subprocess.run(['cargo','+stable','build','--release','--locked','-j','2'],cwd=WORK,check=True)
    if args.run:
        cpus=sorted(os.sched_getaffinity(0))
        assert len(cpus)>=2,'requires distinct available CPUs'
        result={'measured_at_utc':datetime.now(timezone.utc).isoformat(),
            'environment':{'platform':platform.platform(),'server_cpu_affinity':[cpus[0]],
                'client_cpu_affinity':[cpus[-1]],'node':subprocess.check_output(['node','--version'],text=True).strip(),
                'cpu_accounting_tick_seconds':1/os.sysconf('SC_CLK_TCK'),
                'rustc':subprocess.check_output(['rustc','+stable','--version'],text=True).strip()},
            'sources_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES.glob('realtime_probe*') if p.is_file()},
            'limitations':['localhost synthetic latest-state relay; NOT cloud capacity or SLA',
                'server pinned to one logical CPU, no CPU quota or 512MiB cgroup enforced',
                'shared host without exclusive CPU reservation; no repetition series',
                'clients separate process and CPU; client resource usage excluded from server statistics',
                'no TLS/auth/PG/fanout between instances/encryption/real source capture',
                '2 devices per account, 4KiB socket buffers, one latest-value slot per recipient',
                'fixed cohort only; account/latest maps have no TTL, global account limit or disconnect cleanup',
                'not bounded total service memory under account churn; no authenticated session replacement/reconnect protocol',
                'steady sample shorter than one full30s publication cycle; one100-message burst',
                'PSS excludes kernel socket memory; one run per connection count; no production reconnect/slow-client tests'],
            'runs':[run(n,args.seconds,cpus[0],cpus[-1]) for n in args.counts]}
        OUTPUT.write_text(json.dumps(result,indent=2)+'\n')
        print(f'Wrote {OUTPUT}',flush=True)


if __name__=='__main__': main()
