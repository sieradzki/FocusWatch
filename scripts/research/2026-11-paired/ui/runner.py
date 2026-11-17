"""Windows-only paired UI probe. Reads synthetic fixture; never starts a tracker.

Launch-to-marker is bounded by 5 ms polling and two UI frame callbacks, not
photon presentation. Process measurements include the root and discovered
descendants; no names/titles/activity from unrelated applications are logged.
"""
from __future__ import annotations
import argparse
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

K = C.WinDLL('kernel32', use_last_error=True)
P = C.WinDLL('psapi', use_last_error=True)
U = C.WinDLL('user32', use_last_error=True)
SZ = C.c_size_t

class Entry(C.Structure):
    _fields_=[('dwSize',W.DWORD),('cntUsage',W.DWORD),('pid',W.DWORD),('heap',SZ),('module',W.DWORD),('threads',W.DWORD),('parent',W.DWORD),('base_priority',W.LONG),('flags',W.DWORD),('exe',W.WCHAR*260)]
class Memory(C.Structure):
    _fields_=[('cb',W.DWORD),('faults',W.DWORD),('peak_ws',SZ),('ws',SZ),('peak_pool_paged',SZ),('pool_paged',SZ),('peak_pool_nonpaged',SZ),('pool_nonpaged',SZ),('pagefile',SZ),('peak_pagefile',SZ),('private_usage',SZ)]
K.CreateToolhelp32Snapshot.argtypes=[W.DWORD,W.DWORD];K.CreateToolhelp32Snapshot.restype=W.HANDLE
K.Process32FirstW.argtypes=[W.HANDLE,C.POINTER(Entry)];K.Process32NextW.argtypes=[W.HANDLE,C.POINTER(Entry)]
K.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];K.OpenProcess.restype=W.HANDLE
K.CloseHandle.argtypes=[W.HANDLE]
K.GetProcessTimes.argtypes=[W.HANDLE,C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME)]
P.GetProcessMemoryInfo.argtypes=[W.HANDLE,C.POINTER(Memory),W.DWORD]
P.QueryWorkingSet.argtypes=[W.HANDLE,C.c_void_p,W.DWORD]
U.IsWindow.argtypes=[W.HWND];U.IsWindowVisible.argtypes=[W.HWND]
U.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)]
U.GetClientRect.argtypes=[W.HWND,C.POINTER(W.RECT)]

def window_proof(ready,pid):
    handle=int(ready['native_handle']);owner=W.DWORD();rect=W.RECT()
    U.GetWindowThreadProcessId(handle,C.byref(owner));U.GetClientRect(handle,C.byref(rect))
    proof={'hwnd':str(handle),'is_window':bool(U.IsWindow(handle)),'visible':bool(U.IsWindowVisible(handle)),'owner_pid':int(owner.value),'expected_pid':pid,'client_width':rect.right-rect.left,'client_height':rect.bottom-rect.top}
    assert proof['is_window'] and proof['visible'] and owner.value==pid,proof
    return proof

def process_table():
    snap=K.CreateToolhelp32Snapshot(2,0)
    if not snap or snap==W.HANDLE(-1).value: raise OSError(C.get_last_error(),'process snapshot')
    try:
        e=Entry();e.dwSize=C.sizeof(e);ok=K.Process32FirstW(snap,C.byref(e));out={}
        while ok:
            out[int(e.pid)]={'pid':int(e.pid),'parent':int(e.parent),'exe':e.exe}
            ok=K.Process32NextW(snap,C.byref(e))
        return out
    finally: K.CloseHandle(snap)

def private_resident(handle):
    size=1024*1024
    for _ in range(3):
        buf=C.create_string_buffer(size)
        ok=P.QueryWorkingSet(handle,buf,size)
        count=SZ.from_buffer(buf).value
        if ok:
            entries=(SZ*count).from_buffer(buf,C.sizeof(SZ))
            return sum(1 for flags in entries if not flags & 0x100)*4096
        size=max(size*2,(count+1)*C.sizeof(SZ)+4096)
        if size>64*1024*1024: return None
    return None

def measure(pid):
    handle=K.OpenProcess(0x0400|0x0010,False,pid)
    if not handle: return {'pid':pid,'error':C.get_last_error()}
    try:
        m=Memory();m.cb=C.sizeof(m)
        if not P.GetProcessMemoryInfo(handle,C.byref(m),C.sizeof(m)): return {'pid':pid,'error':C.get_last_error()}
        created,ended,kernel,user=W.FILETIME(),W.FILETIME(),W.FILETIME(),W.FILETIME()
        if not K.GetProcessTimes(handle,C.byref(created),C.byref(ended),C.byref(kernel),C.byref(user)): return {'pid':pid,'error':C.get_last_error()}
        ft=lambda f:(f.dwHighDateTime<<32)|f.dwLowDateTime
        return {'pid':pid,'cpu_seconds':(ft(kernel)+ft(user))/1e7,'working_set_bytes':int(m.ws),'private_commit_bytes':int(m.private_usage),'nonshareable_resident_bytes':private_resident(handle)}
    finally:K.CloseHandle(handle)

def sample(root,known):
    table=process_table();known.add(root)
    changed=True
    while changed:
        new={p for p,e in table.items() if e['parent'] in known};changed=not new.issubset(known);known.update(new)
    return [dict(measure(pid),exe=table[pid]['exe'],parent=table[pid]['parent']) for pid in sorted(known) if pid in table]

def expected(fixture):
    lines=fixture.read_text(encoding='utf-8-sig').splitlines()
    rows=[line.split('\t') for line in lines[1:] if line]
    assert len(rows)==1440
    chosen=next(r for r in rows if int(r[0])==555)
    assert chosen[1:]==['33240','33300','browser','unclassified'],chosen
    duration=lambda r:int(r[2])-int(r[1])
    return {'row_count':len(rows),'selected_id':555,'selected_category':'learning','learning_seconds':sum(duration(r) for r in rows if r[4]=='learning')+duration(chosen),'unclassified_seconds':sum(duration(r) for r in rows if r[4]=='unclassified')-duration(chosen)}

def command(runtime,work,fixture,output,auto):
    if runtime=='avalonia':cmd=['dotnet',str(work/'avalonia/publish/ReportProbe.dll'),str(fixture),str(output)]
    else:cmd=[str(work/'electron/node_modules/electron/dist/electron.exe'),str(work/'electron'),str(fixture),str(output)]
    return cmd+(['--auto','--capture-surface'] if auto else ['--capture-surface'])

def run(runtime,work,fixture,output,seconds,auto=True):
    output.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1',AVALONIA_TELEMETRY_OPTOUT='1',DOTNET_GENERATE_ASPNET_CERTIFICATE='false')
    cmd=command(runtime,work,fixture,output,auto);known=set();cpu_last={};cpu_cumulative=0.0;samples=[]
    with (output/'stdout.txt').open('w') as stdout,(output/'stderr.txt').open('w') as stderr:
        started=time.perf_counter();p=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,env=env,cwd=str(work),creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            while not (output/'ready.json').exists():
                if p.poll() is not None:raise RuntimeError(f'{runtime} exited {p.returncode}: {(output/"stderr.txt").read_text(encoding="utf-8-sig",errors="replace")}')
                if time.perf_counter()-started>40:raise TimeoutError(f'{runtime}: ready timeout')
                time.sleep(.005)
            detected=time.perf_counter();ready=json.loads((output/'ready.json').read_text(encoding='utf-8-sig'));native_proof=window_proof(ready,p.pid)
            while time.perf_counter()-detected<seconds:
                moment=time.perf_counter();procs=sample(p.pid,known)
                for item in procs:
                    if 'cpu_seconds' in item:
                        cpu_cumulative+=max(0,item['cpu_seconds']-cpu_last.get(item['pid'],0));cpu_last[item['pid']]=item['cpu_seconds']
                good=[x for x in procs if 'cpu_seconds'in x]
                totals={key:(sum(x[key] for x in good) if good and len(good)==len(procs) and all(x.get(key)is not None for x in good) else None) for key in ['working_set_bytes','private_commit_bytes','nonshareable_resident_bytes']}
                samples.append({'since_ready_s':moment-detected,'cpu_cumulative_s':cpu_cumulative,'cpu_coverage_complete':bool(good) and len(good)==len(procs),'processes':procs,**totals})
                time.sleep(max(0,.5-(time.perf_counter()-moment)))
            corrected=json.loads((output/'corrected.json').read_text(encoding='utf-8-sig')) if auto else None
            if corrected:
                exp=expected(fixture)
                for key,value in exp.items():assert corrected[key]==value,(runtime,key,corrected[key],value)
                assert corrected['displayed_text']=='#555 | 09:14–09:15 | browser | category=learning'
                assert 'programmatic Ctrl+Enter' in corrected['activation_mode']
                assert all((output/f'surface-{phase}.png').is_file() for phase in ['before','after'])
            idle=[x for x in samples if x['since_ready_s']>=3]
            safe_cmd=[part.replace(str(work),'$WORK').replace(str(fixture),'$FIXTURE').replace(str(output),'$OUTPUT') for part in cmd]
            result={'runtime':runtime,'pid':p.pid,'command':safe_cmd,'native_window_proof':native_proof,'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'launch_to_ready_marker_ms':(detected-started)*1000,'ready':ready,'corrected':corrected,'samples':samples,'idle_start_s':idle[0]['since_ready_s'] if idle else None,'idle_end_s':idle[-1]['since_ready_s'] if idle else None}
            if len(idle)>1:
                cpu_complete=all(x['cpu_coverage_complete'] for x in samples)
                result['idle_cpu_percent_one_core']=100*(idle[-1]['cpu_cumulative_s']-idle[0]['cpu_cumulative_s'])/(idle[-1]['since_ready_s']-idle[0]['since_ready_s']) if cpu_complete else None
                result['idle_cpu_coverage_complete']=cpu_complete
                result['idle_metric_coverage']={}
                for key in ['working_set_bytes','private_commit_bytes','nonshareable_resident_bytes']:
                    values=[x[key] for x in idle if x[key] is not None]
                    result['idle_median_'+key]=statistics.median(values) if values else None
                    result['idle_metric_coverage'][key]={'valid_samples':len(values),'total_samples':len(idle),'complete':len(values)==len(idle)}
            (output/'close').touch();p.wait(timeout=10);result['exit_code']=p.returncode
            deadline=time.monotonic()+3
            remaining=sample(p.pid,known)
            while remaining and time.monotonic()<deadline:
                time.sleep(.1);remaining=sample(p.pid,known)
            result['remaining_processes']=remaining
            assert p.returncode==0 and not remaining,(p.returncode,remaining)
            for name in ['stdout.txt','stderr.txt']:
                log=output/name
                log.write_text(log.read_text(encoding='utf-8-sig',errors='replace').replace(str(work),'$WORK').replace(str(fixture),'$FIXTURE'),encoding='utf-8')
            (output/'run-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');return result
        finally:
            if p.poll() is None:
                (output/'close').touch()
                try:p.wait(timeout=3)
                except subprocess.TimeoutExpired:subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True)

def main():
    a=argparse.ArgumentParser();a.add_argument('--work',type=Path,required=True);a.add_argument('--fixture',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--pairs',type=int,default=6);a.add_argument('--idle-seconds',type=float,default=11)
    args=a.parse_args();fixture=args.fixture.resolve();expected(fixture);args.output.mkdir(parents=True,exist_ok=False)
    metadata={'python':sys.version,'windows':platform.version(),'logical_cpu_count':os.cpu_count(),'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'poll_seconds':.005,'sample_seconds':.5,'idle_seconds':args.idle_seconds,'pairs':args.pairs,'wall_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    (args.output/'environment.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8');results=[]
    for pair in range(args.pairs):
        order=['avalonia','electron'] if pair%2==0 else ['electron','avalonia']
        for index,runtime in enumerate(order):
            label=f'pair-{pair+1:02d}-{index+1}-{runtime}'
            try:
                result=run(runtime,args.work.resolve(),fixture,args.output/label,args.idle_seconds)
            except (OSError,RuntimeError,TimeoutError,AssertionError) as error:
                result={'runtime':runtime,'status':'blocked_or_failed','error_type':type(error).__name__,'error':str(error).replace(str(args.work.resolve()),'$WORK').replace(str(fixture),'$FIXTURE'),'pair':pair+1,'index':index+1}
                results.append(result)
                for name in ['stdout.txt','stderr.txt']:
                    log=args.output/label/name
                    if log.exists():log.write_text(log.read_text(encoding='utf-8',errors='replace').replace(str(args.work.resolve()),'$WORK').replace(str(fixture),'$FIXTURE'),encoding='utf-8')
                (args.output/'all-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
                print(json.dumps(result),flush=True)
                return 1
            results.append(result)
            print(json.dumps({key:result.get(key) for key in ['runtime','launch_to_ready_marker_ms','idle_cpu_percent_one_core','idle_median_nonshareable_resident_bytes','exit_code']}),flush=True)
    (args.output/'all-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    return 0

if __name__=='__main__':raise SystemExit(main())
