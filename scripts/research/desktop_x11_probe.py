#!/usr/bin/env python3
"""Synthetic X11-only comparison: Python+subprocess vs Python+persistent Xlib.

Always allocates its OWN Xvfb and synthetic window. Never opens inherited DISPLAY.
The fake root property is not a window manager compatibility test. No production
FocusWatch import, private titles, idle input, or user desktop access is involved.
"""
import ctypes as C
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]


def main():
    if not shutil.which("xdotool") or not shutil.which("Xvfb"):
        raise SystemExit("Requires existing xdotool and Xvfb; no package installation performed")
    rd, wr = os.pipe()
    server = subprocess.Popen(["Xvfb", "-displayfd", str(wr), "-screen", "0", "800x600x24", "-nolisten", "tcp"],
                              pass_fds=[wr], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.close(wr)
    with os.fdopen(rd) as stream:
        display = ":" + stream.readline().strip()
    if display == ":":
        raise RuntimeError("private Xvfb allocation failed")
    x = C.CDLL("libX11.so.6")
    ptr, ulong = C.c_void_p, C.c_ulong
    signatures = {
        "XOpenDisplay": ([C.c_char_p], ptr), "XDefaultRootWindow": ([ptr], ulong),
        "XCreateSimpleWindow": ([ptr,ulong,C.c_int,C.c_int,C.c_uint,C.c_uint,C.c_uint,ulong,ulong], ulong),
        "XInternAtom": ([ptr,C.c_char_p,C.c_int], ulong),
        "XChangeProperty": ([ptr,ulong,ulong,ulong,C.c_int,C.c_int,ptr,C.c_int], C.c_int),
        "XGetWindowProperty": ([ptr,ulong,ulong,C.c_long,C.c_long,C.c_int,ulong,C.POINTER(ulong),
          C.POINTER(C.c_int),C.POINTER(ulong),C.POINTER(ulong),C.POINTER(ptr)], C.c_int),
        "XMapWindow": ([ptr,ulong],C.c_int), "XFlush": ([ptr],C.c_int),
        "XFree": ([ptr],C.c_int), "XCloseDisplay": ([ptr],C.c_int),
        "XStoreName": ([ptr,ulong,C.c_char_p],C.c_int),
    }
    for name, (args, result) in signatures.items():
        method = getattr(x,name); method.argtypes=args; method.restype=result
    connection = x.XOpenDisplay(display.encode())
    if not connection: raise RuntimeError("Cannot open owned Xvfb")
    try:
        root = x.XDefaultRootWindow(connection)
        window = x.XCreateSimpleWindow(connection,root,0,0,400,300,0,0,0)
        atoms = {name:x.XInternAtom(connection,name.encode(),0) for name in
                 ["_NET_ACTIVE_WINDOW","_NET_SUPPORTED","_NET_WM_NAME","WM_CLASS","UTF8_STRING","STRING","WINDOW","ATOM"]}
        supported = ulong(atoms["_NET_ACTIVE_WINDOW"])
        x.XChangeProperty(connection,root,atoms["_NET_SUPPORTED"],atoms["ATOM"],32,0,C.byref(supported),1)
        target = ulong(window)
        x.XChangeProperty(connection,root,atoms["_NET_ACTIVE_WINDOW"],atoms["WINDOW"],32,0,C.byref(target),1)
        title = b"FocusWatch SYNTHETIC editor"
        class_value = b"synthetic-editor\0SyntheticEditor\0"
        x.XChangeProperty(connection,window,atoms["_NET_WM_NAME"],atoms["UTF8_STRING"],8,0,C.c_char_p(title),len(title))
        x.XChangeProperty(connection,window,atoms["WM_CLASS"],atoms["STRING"],8,0,C.c_char_p(class_value),len(class_value))
        x.XStoreName(connection,window,title)
        x.XMapWindow(connection,window); x.XFlush(connection)
        def property_value(win, name):
            kind, fmt, count, remaining, data = ulong(), C.c_int(), ulong(), ulong(), ptr()
            code = x.XGetWindowProperty(connection,win,atoms[name],0,1024,0,0,
                                        C.byref(kind),C.byref(fmt),C.byref(count),C.byref(remaining),C.byref(data))
            if code or not data: raise RuntimeError("Synthetic property read failed")
            try:
                if fmt.value == 32: return C.cast(data,C.POINTER(ulong))[0]
                return C.string_at(data,count.value)
            finally: x.XFree(data)
        def persistent():
            active = property_value(root,"_NET_ACTIVE_WINDOW")
            return property_value(active,"_NET_WM_NAME"), property_value(active,"WM_CLASS").split(b"\0")[1]
        env = {**os.environ,"DISPLAY":display}
        def spawned():
            return tuple(subprocess.check_output(["xdotool","getactivewindow",command],env=env,stderr=subprocess.PIPE).strip()
                         for command in ["getwindowname","getwindowclassname"])
        expected = (title,b"SyntheticEditor")
        assert persistent() == spawned() == expected
        repetitions, reads = 5, 100
        result = {"scope":"Both paths Python on same owned Xvfb; compares IPC/subprocess strategy, not Python vs Rust",
                  "iterations_per_batch":reads,"batches":repetitions,"synthetic_values_equal":True,"runs":[],
                  "limitations":["Fake EWMH root property, not real dwm compatibility", "No lock/suspend/Wayland/Windows/idle tests",
                    "Only app title+class snapshot, no event-driven subscription benchmark", "Sequential batch throughput, not resident collector CPU",
                    "Xvfb server work excluded from Python process CPU; subprocess CPU not estimated"]}
        for batch in range(repetitions):
            methods = [("persistent_xlib",persistent),("two_xdotool_processes",spawned)]
            if batch % 2: methods.reverse()
            for name, function in methods:
                samples=[]
                for _ in range(reads):
                    start=time.perf_counter_ns(); values=function(); samples.append((time.perf_counter_ns()-start)/1e6)
                    assert values==expected
                result["runs"].append({"batch":batch+1,"method":name,"median_ms":statistics.median(samples),
                  "p95_ms":sorted(samples)[int(len(samples)*0.95)-1],"samples_ms":samples})
        destination=ROOT / "docs/research/2026-09/desktop-results-x11.json"
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps({**result,"runs":[{k:v for k,v in r.items() if k!="samples_ms"} for r in result["runs"]]},indent=2))
    finally:
        x.XCloseDisplay(connection)
        server.terminate();server.wait(timeout=3)


if __name__ == "__main__": main()
