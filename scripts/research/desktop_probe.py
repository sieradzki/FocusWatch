#!/usr/bin/env python3
"""Build/run isolated synthetic desktop probes; never open the existing app/db.

Preparation downloads project-local npm/Cargo dependencies, never OS packages.
Run with repository .venv Python (PySide6 + psutil already available).
Every UI runs in a new Xvfb display, with software rendering and private profiles.
No autostart registration, real display inspection, or native capture is performed.
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
import statistics
import struct
import subprocess
import sys
import threading
import time
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
SOURCES = Path(__file__).resolve().parent
WORK = ROOT / "build/research/desktop"
MARKER = "DESKTOP_PROBE "


def write_probe_icon():
    # Tiny synthetic RGBA asset required by Tauri generate_context, no user image.
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB",1,1,8,6,0,0,0))
    png += chunk(b"IDAT", zlib.compress(b"\x00\x46\x77\xbb\xff")) + chunk(b"IEND",b"")
    (WORK / "icons").mkdir(exist_ok=True)
    (WORK / "icons/icon.png").write_bytes(png)


def prepare(electron_zip):
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "src").mkdir(exist_ok=True)
    (WORK / "dist").mkdir(exist_ok=True)
    write_probe_icon()
    for source, target in [("desktop_frontend.jsx", "frontend.jsx"),
                           ("desktop_electron.cjs", "electron.cjs"),
                           ("desktop_tauri_main.rs", "src/main.rs")]:
        shutil.copy2(SOURCES / source, WORK / target)
    (WORK / "preload.cjs").write_text("const {contextBridge,ipcRenderer}=require('electron');\n"
        "contextBridge.exposeInMainWorld('desktopProbe',{config:()=>ipcRenderer.invoke('probe-config'),report:value=>ipcRenderer.send('probe-report',value)});\n")
    (WORK / "package.json").write_text(json.dumps({"private": True, "dependencies": {
        "react": "19.3.0", "react-dom": "19.3.0", "esbuild": "0.28.2"}}, indent=2))
    npm_lock = SOURCES / "desktop_npm.lock"
    if npm_lock.exists(): shutil.copy2(npm_lock, WORK / "package-lock.json")
    subprocess.run(["npm", "ci" if npm_lock.exists() else "install", "--no-audit", "--no-fund"], cwd=WORK, check=True)
    subprocess.run([str(WORK / "node_modules/.bin/esbuild"), "frontend.jsx", "--bundle", "--minify",
                    "--define:process.env.NODE_ENV=\"production\"", "--outfile=dist/app.js"], cwd=WORK, check=True)
    (WORK / "dist/index.html").write_text('''<!doctype html><html><meta charset="utf-8">
      <style>body{margin:0;background:#101820;color:#eef2f7;font:16px sans-serif}main{padding:30px}
      h1{margin:0 0 18px;font-size:26px}p{color:#aebdca;margin:0 0 22px}</style>
      <div id="root"></div><script src="app.js"></script></html>''')
    (WORK / "Cargo.toml").write_text('''[package]
name = "focuswatch-desktop-probe"
version = "0.1.0"
edition = "2021"
[build-dependencies]
tauri-build = "=2.7.0"
[dependencies]
tauri = { version = "=2.12.0", features = ["custom-protocol"] }
[profile.release]
opt-level = 1
debug = false
''')
    (WORK / "build.rs").write_text("fn main() { tauri_build::build() }\n")
    cargo_lock = SOURCES / "desktop_cargo.lock"
    if cargo_lock.exists(): shutil.copy2(cargo_lock, WORK / "Cargo.lock")
    (WORK / "tauri.conf.json").write_text(json.dumps({
        "productName": "FocusWatch Synthetic Probe", "version": "0.1.0",
        "identifier": "dev.focuswatch.syntheticprobe", "build": {"frontendDist": "dist"},
        "app": {"withGlobalTauri": True, "windows": [{"title": "Synthetic desktop probe", "width": 1200, "height": 700}],
                "security": {"csp": "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src ipc: http://ipc.localhost"}},
        "bundle": {"active": False}}, indent=2))
    if electron_zip:
        dest = WORK / "electron-runtime"
        dest.mkdir(exist_ok=True)
        with zipfile.ZipFile(electron_zip) as archive:
            archive.extractall(dest)
            for info in archive.infolist():
                mode = info.external_attr >> 16
                if mode:
                    (dest / info.filename).chmod(mode)
    print("Prepared synthetic UI sources. Building Tauri release opt-level=1, jobs=2.", flush=True)
    command = ["cargo", "+stable", "build", "--release", "-j", "2"]
    if cargo_lock.exists(): command.append("--locked")
    subprocess.run(command, cwd=WORK, check=True)


def proc_snapshot(process):
    import psutil
    members = []
    try:
        members = [psutil.Process(process.pid)] + psutil.Process(process.pid).children(recursive=True)
    except psutil.Error:
        pass
    result = {"rss_bytes": 0, "pss_bytes": 0, "cpu_seconds": 0.0, "process_count": 0, "cpu_by_process":{}}
    for p in members:
        try:
            result["rss_bytes"] += p.memory_info().rss
            result["pss_bytes"] += p.memory_full_info().pss
            cpu = p.cpu_times()
            result["cpu_seconds"] += cpu.user + cpu.system
            result["cpu_by_process"][f"{p.pid}:{p.create_time()}"] = cpu.user + cpu.system
            result["process_count"] += 1
        except (psutil.Error, AttributeError):
            pass
    return result


def stop_tree(process):
    import psutil
    # dbus-run-session can exit before its application. Track each descendant
    # before signalling the wrapper, and reap/kill survivors by process identity.
    try:
        descendants = psutil.Process(process.pid).children(recursive=True)
    except psutil.NoSuchProcess:
        descendants = []
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=3)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=3)
        except ProcessLookupError:
            pass
    _, alive = psutil.wait_procs(descendants, timeout=2)
    for child in alive:
        try:
            if child.status() != psutil.STATUS_ZOMBIE:
                child.kill()
        except psutil.NoSuchProcess:
            pass
    psutil.wait_procs(alive, timeout=2)


def one_run(runtime, iteration, segments):
    run_dir = WORK / f"run-{runtime}-{iteration}-{time.time_ns()}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "runtime").mkdir(mode=0o700, exist_ok=True)
    read_fd, write_fd = os.pipe()
    xvfb = subprocess.Popen(["Xvfb", "-displayfd", str(write_fd), "-screen", "0", "1280x800x24", "-nolisten", "tcp"],
                            pass_fds=[write_fd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True)
    os.close(write_fd)
    with os.fdopen(read_fd) as pipe:
        display = pipe.readline().strip()
    if not display:
        raise RuntimeError("Xvfb did not allocate a display")
    env = {**os.environ, "DISPLAY": ":" + display, "LIBGL_ALWAYS_SOFTWARE": "1",
           "GDK_BACKEND": "x11", "QT_QPA_PLATFORM": "xcb", "QT_QUICK_BACKEND": "software",
           "WEBKIT_DISABLE_DMABUF_RENDERER": "1", "PROBE_PROFILE": str(run_dir / "profile"),
           "PROBE_SEGMENTS":str(segments),
           "XDG_CACHE_HOME": str(run_dir / "cache"), "XDG_DATA_HOME": str(run_dir / "data"),
           "XDG_CONFIG_HOME": str(run_dir / "config"), "XDG_RUNTIME_DIR": str(run_dir / "runtime")}
    env.pop("WAYLAND_DISPLAY", None)
    env.pop("DBUS_SESSION_BUS_ADDRESS", None)
    commands = {
        "qtquick": [sys.executable, str(SOURCES / "desktop_qt_probe.py")],
        "electron": [str(WORK / "electron-runtime/electron"), str(WORK / "electron.cjs"), "--disable-gpu"],
        "tauri": [str(WORK / "target/release/focuswatch-desktop-probe")],
    }
    started = time.perf_counter()
    try:
        process = subprocess.Popen(["dbus-run-session", "--", *commands[runtime]], env=env, cwd=run_dir, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, start_new_session=True)
    except OSError as exc:
        stop_tree(xvfb)
        return {"runtime":runtime,"iteration":iteration,"status":"failed","diagnostic":[str(exc)]}
    lines = queue.Queue()
    def read_output():
        for line in process.stdout:
            lines.put((time.perf_counter(), line.rstrip()))
    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    samples, events, diagnostic = [], [], []
    cumulative_cpu = {}
    done = False
    try:
        while time.perf_counter() - started < 30:
            now = time.perf_counter()
            snap = {"at_s": now - started, **proc_snapshot(process)}
            for pid, cpu in snap.pop("cpu_by_process").items():
                cumulative_cpu[pid] = max(cumulative_cpu.get(pid, 0), cpu)
            snap["cpu_seconds"] = sum(cumulative_cpu.values())
            samples.append(snap)
            while not lines.empty():
                received, line = lines.get_nowait()
                if MARKER in line:
                    item = json.loads(line.split(MARKER, 1)[1])
                    item["received_s"] = received - started
                    events.append(item)
                    if item["event"] == "done": done = True
                else:
                    diagnostic.append(line)
            if done or process.poll() is not None:
                break
            time.sleep(0.1)
        if not done:
            return {"runtime":runtime,"iteration":iteration,"status":"failed", "events":events,
                    "exit_code":process.poll(),"diagnostic":diagnostic[-30:]}
        ready = next(e["received_s"] for e in events if e["event"] == "ready")
        idle_end = next(e["received_s"] for e in events if e["event"] == "idle_end")
        idle_samples = [s for s in samples if ready + 0.5 <= s["at_s"] <= idle_end - 0.2]
        first, last = idle_samples[0], idle_samples[-1]
        result = {"runtime":runtime,"iteration":iteration,"status":"ok", "ready_submission_ms":ready*1000,
                  "idle_cpu_one_core_pct":100*(last["cpu_seconds"]-first["cpu_seconds"])/(last["at_s"]-first["at_s"]),
                  "idle_pss_mib":statistics.median(s["pss_bytes"] for s in idle_samples)/1024**2,
                  "idle_rss_mib":statistics.median(s["rss_bytes"] for s in idle_samples)/1024**2,
                  "idle_process_count":statistics.median(s["process_count"] for s in idle_samples),
                  "events":events,"samples":samples,"diagnostic":diagnostic[-30:]}
        return result
    finally:
        stop_tree(process)
        stop_tree(xvfb)


def run(runtimes, repeats, output, segments):
    import PySide6
    from PySide6.QtCore import qVersion
    import psutil
    electron_version = WORK / "electron-runtime/version"
    versions = {"python":sys.version, "pyside":PySide6.__version__, "qt":qVersion(), "psutil":psutil.__version__,
                "electron":electron_version.read_text().strip() if electron_version.exists() else "unavailable",
                "tauri":"2.12.0", "react":"19.3.0",
                "webkitgtk":subprocess.check_output(["pkg-config","--modversion","webkit2gtk-4.1"],text=True).strip(),
                "rustc":subprocess.check_output(["rustc","+stable","--version"],text=True).strip()}
    cpu_model = next(line.split(":",1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name"))
    memory = next(line for line in Path("/proc/meminfo").read_text().splitlines() if line.startswith("MemTotal"))
    hashes = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SOURCES.glob("desktop_*")) if p.is_file()}
    result = {"captured_at_utc":datetime.now(timezone.utc).isoformat(),
              "host":{"cpu":cpu_model,"memory":memory,"kernel":platform.release(),"load_average_start":os.getloadavg()},"source_sha256":hashes,
              "method":"Xvfb, software rendering; startup ends at first Canvas draw submission, not confirmed presentation",
              "versions":versions,"repeats":repeats,"synthetic_segments":segments,"frames":60,
              "limitations":["No GPU / actual dwm compositor / Windows measurements", "Qt Canvas and HTML Canvas have different implementations",
                "Draw submission uses Date.now() (millisecond resolution), not GPU completion", "RSS includes shared pages; PSS preferred",
                "Idle CPU is sampled across process tree, retaining last observed CPU of departed children, and expressed as percent of one logical CPU; very short-lived children may be missed", "No cold OS-cache reset; fresh private app/cache profile per run", "No DB/collector in UI measurements",
                "Every runtime has an isolated dbus-run-session; its wrapper/daemon are included in process-tree memory and count"],
              "runs":[]}
    for i in range(repeats):
        # Rotate order to avoid always favouring one runtime.
        ordered = runtimes[i % len(runtimes):] + runtimes[:i % len(runtimes)]
        for runtime in ordered:
            item = one_run(runtime, i + 1, segments)
            result["runs"].append(item)
            hidden = {"events","samples","diagnostic"} if item["status"] == "ok" else {"events","samples"}
            print(json.dumps({k:v for k,v in item.items() if k not in hidden}), flush=True)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, indent=2) + "\n")
    result["host"]["load_average_end"] = os.getloadavg()
    output.write_text(json.dumps(result, indent=2) + "\n")
    if any(item["status"] != "ok" for item in result["runs"]):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--electron-zip", type=Path)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--runtimes", nargs="+", default=["tauri", "electron", "qtquick"], choices=["tauri", "electron", "qtquick"])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--segments", type=int, default=10000)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/research/2026-09/desktop-results.json")
    args = parser.parse_args()
    if args.prepare: prepare(args.electron_zip)
    if not 1 <= args.segments <= 100000: parser.error("segments must be between 1 and 100000")
    if args.run: run(args.runtimes, args.repeats, args.output, args.segments)
