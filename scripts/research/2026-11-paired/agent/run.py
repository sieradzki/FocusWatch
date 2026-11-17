#!/usr/bin/env python3
"""Paired synthetic Windows probes, not FocusWatch product code.

Build output, SDK caches and all databases go to a new TEMP directory. Reads only
the supplied synthetic fixture, own databases, own child resource counters and
aggregate OS CPU counters. Never reads window/input/media information.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import queue
import shutil
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import threading
import time

HERE = Path(__file__).resolve().parent
INSERT = "INSERT INTO observations(id,start_s,end_s,app,category) VALUES(?1,?2,?3,?4,?5)"
SUMMARY = "SELECT count(*),coalesce(sum(end_s-start_s),0),coalesce(sum(id),0),coalesce(sum(id*(end_s-start_s)),0) FROM observations"
GROUPS = "SELECT app,category,count(*),sum(end_s-start_s) FROM observations GROUP BY app,category ORDER BY app,category"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(args, env=None):
    return subprocess.check_output([str(a) for a in args], env=env, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace").strip()


def build(args):
    work = Path(tempfile.mkdtemp(prefix="FocusWatchPairedAgent-"))
    cs = work / "csharp"
    rust = work / "rust-agent.exe"
    env = os.environ.copy()
    env.update(DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_SKIP_FIRST_TIME_EXPERIENCE="1", DOTNET_GENERATE_ASPNET_CERTIFICATE="false", DOTNET_CLI_HOME=str(work / "dotnet-home"))
    cs.mkdir()
    # A copied project prevents bin/obj/caches from touching unrelated repo paths.
    project = work / "project"
    project.mkdir()
    for name in ("AgentProbe.csproj", "Program.cs"):
        shutil.copy2(HERE / name, project / name)
    print(command([args.dotnet, "build", project / "AgentProbe.csproj", "-c", "Release", "-o", cs, "--ignore-failed-sources", "--nologo", "-v", "minimal"], env), flush=True)
    rustc = Path(args.rustc)
    rust_version = command([rustc, "--version", "--verbose"])
    env["RUSTC_VERSION"] = rust_version.splitlines()[0]
    subprocess.run([str(rustc), str(HERE / "agent.rs"), "--edition=2024", "-C", "opt-level=3", "-C", "debuginfo=0", "-C", "panic=abort", "-o", str(rust)], env=env, check=True)
    manifest = {
        "work_dir": str(work), "executables": {"csharp": str(cs / "AgentProbe.exe"), "rust": str(rust)},
        "dotnet_sdk": command([args.dotnet, "--version"]), "dotnet_info": command([args.dotnet, "--info"]),
        "rustc": rust_version, "rustc_path": str(rustc), "build_mode": "Release; Rust opt-level=3, panic=abort; C# normal JIT, no AOT",
        "source_sha256": {name: sha(HERE / name) for name in ("AgentProbe.csproj", "Program.cs", "agent.rs", "schema.sql", "run.py")},
        "executables_sha256": {"csharp": sha(cs / "AgentProbe.exe"), "csharp_dll": sha(cs / "AgentProbe.dll"), "rust": sha(rust)},
    }
    if (project / "packages.lock.json").exists():
        manifest["packages_lock"] = json.loads((project / "packages.lock.json").read_text(encoding="utf-8-sig"))
    manifest_path = args.build_manifest or work / "build-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"BUILT {manifest_path}", flush=True)


class FILETIME(C.Structure):
    _fields_ = [("low", W.DWORD), ("high", W.DWORD)]
    def value(self):
        return ((self.high << 32) | self.low) / 10_000_000


class MEMORY(C.Structure):
    _fields_ = [("cb", W.DWORD), ("faults", W.DWORD)] + [(name, C.c_size_t) for name in (
        "peak_working_set", "working_set", "peak_paged_pool", "paged_pool", "peak_nonpaged_pool", "nonpaged_pool", "pagefile", "peak_pagefile", "private_bytes")]


def windows_api():
    kernel = C.WinDLL("kernel32", use_last_error=True)
    psapi = C.WinDLL("psapi", use_last_error=True)
    kernel.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    kernel.OpenProcess.restype = W.HANDLE
    kernel.GetProcessTimes.argtypes = [W.HANDLE] + [C.POINTER(FILETIME)] * 4
    kernel.GetProcessTimes.restype = W.BOOL
    kernel.GetSystemTimes.argtypes = [C.POINTER(FILETIME)] * 3
    kernel.GetSystemTimes.restype = W.BOOL
    kernel.CloseHandle.argtypes = [W.HANDLE]
    psapi.GetProcessMemoryInfo.argtypes = [W.HANDLE, C.POINTER(MEMORY), W.DWORD]
    psapi.GetProcessMemoryInfo.restype = W.BOOL
    return kernel, psapi


def resources(kernel, psapi, handle, started):
    created, exited, kern, user = FILETIME(), FILETIME(), FILETIME(), FILETIME()
    if not kernel.GetProcessTimes(handle, C.byref(created), C.byref(exited), C.byref(kern), C.byref(user)):
        raise C.WinError(C.get_last_error())
    mem = MEMORY()
    mem.cb = C.sizeof(mem)
    ok = psapi.GetProcessMemoryInfo(handle, C.byref(mem), mem.cb)
    return {"t_s": time.perf_counter() - started, "cpu_s": kern.value() + user.value(),
            "private_bytes": mem.private_bytes if ok else None, "working_set_bytes": mem.working_set if ok else None,
            "process_peak_working_set_bytes": mem.peak_working_set if ok else None, "page_faults": mem.faults if ok else None}


def system_cpu(kernel):
    idle, kern, user = FILETIME(), FILETIME(), FILETIME()
    if not kernel.GetSystemTimes(C.byref(idle), C.byref(kern), C.byref(user)):
        raise C.WinError(C.get_last_error())
    return {"idle_s": idle.value(), "kernel_s": kern.value(), "user_s": user.value()}


def fixture_rows(path):
    lines = path.read_text(encoding="ascii").splitlines()
    assert lines[0] == "id\tstart_s\tend_s\tapp\tcategory"
    return [(int(c[0]), int(c[1]), int(c[2]), c[3], c[4]) for c in (line.split("\t") for line in lines[1:])]


def probe_command(name, manifest, args, database, idle_ms, interval_ms):
    prefix = [manifest["executables"][name]]
    if name == "csharp" and args.csharp_host == "dotnet":
        prefix = [args.dotnet, str(Path(prefix[0]).with_suffix(".dll"))]
    return prefix + [str(args.fixture.resolve()), str(HERE / "schema.sql"), str(database), str(idle_ms), str(interval_ms), str(args.batch_size)]


def public_data(data, manifest):
    """Sanitize serialized operational paths before writing repository evidence."""
    prefixes = ((manifest["work_dir"], "<temp>/agent-build"), (str(HERE.parents[3]), "<repo>"),
                (os.environ["TEMP"], "<temp>"), (str(Path.home()), "<profile>"),
                (str(Path(os.environ["WINDIR"]) / "System32"), "<System32>"))
    def scrub(value):
        if isinstance(value, str):
            for prefix, replacement in prefixes:
                for variant in (prefix.replace("\\", "\\\\"), prefix, prefix.replace("\\", "/")):
                    value = value.replace(variant, replacement)
            return value
        if isinstance(value, list):
            return [scrub(item) for item in value]
        if isinstance(value, dict):
            return {key: scrub(item) for key, item in value.items()}
        return value
    return scrub(data)


def smoke(args):
    manifest = json.loads(args.build_manifest.read_text(encoding="utf-8"))
    expected = fixture_rows(args.fixture)
    results = []
    for name in ("rust", "csharp"):
        db = Path(manifest["work_dir"]) / f"smoke-{name}-{time.time_ns()}.sqlite"
        try:
            output = command(probe_command(name, manifest, args, db, 0, 0))
            check = verify_database(db, expected, output.splitlines())
            results.append({"implementation": name, "status": "pass", "validation": check, "stdout": output.splitlines()})
            print(f"SMOKE {name} full_rows/groups/integrity=pass", flush=True)
        except (OSError, subprocess.CalledProcessError, AssertionError) as error:
            output = getattr(error, "output", "") or ""
            blocked = getattr(error, "winerror", None) == 4551 or "Application Control policy" in output
            message = "Probe exited with nonzero status" if isinstance(error, subprocess.CalledProcessError) else str(error)
            results.append({"implementation": name, "status": "blocked" if blocked else "fail", "error_type": type(error).__name__,
                            "winerror": getattr(error, "winerror", None), "exit_code": getattr(error, "returncode", None), "message": message, "error_output": output})
            print(f"SMOKE {name} status={results[-1]['status']}: {message}", flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = public_data({"timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "fixture_sha256": sha(args.fixture), "performance_measured": False,
        "csharp_host": args.csharp_host, "source_sha256": {name: sha(HERE / name) for name in ("Program.cs", "agent.rs", "schema.sql", "run.py")}, "runs": results}, manifest)
    (args.output.parent / "smoke.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if any(run["status"] != "pass" for run in results):
        sys.exit(1)


def verify_database(path, expected, stdout):
    # Independent Python SQLite engine, full ordered comparison, not only a checksum.
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as con:
        actual = con.execute("SELECT id,start_s,end_s,app,category FROM observations ORDER BY id").fetchall()
        assert actual == sorted(expected), "full row comparison failed"
        assert con.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        summary = list(con.execute(SUMMARY).fetchone())
        groups = [list(row) for row in con.execute(GROUPS)]
        assert summary == [len(expected), sum(r[2] - r[1] for r in expected), sum(r[0] for r in expected), sum(r[0] * (r[2] - r[1]) for r in expected)]
        expected_groups = {}
        for _, start, end, app, category in expected:
            count, duration = expected_groups.get((app, category), (0, 0))
            expected_groups[app, category] = (count + 1, duration + end - start)
        assert groups == [[app, category, *expected_groups[app, category]] for app, category in sorted(expected_groups)]
        summary_lines = [line for line in stdout if line.startswith("SUMMARY\t")]
        assert summary_lines == ["SUMMARY\t" + "\t".join(map(str, summary))]
        group_lines = [line for line in stdout if line.startswith("GROUP\t")]
        assert group_lines == ["GROUP\t" + "\t".join(map(str, row)) for row in groups]
        assert summary[1] == 86400
        assert con.execute("SELECT app,category FROM observations WHERE id=555").fetchone() == ("browser", "unclassified")
        return {"full_ordered_rows_equal": True, "integrity_check": "ok", "summary": summary, "groups": groups,
                "id555": ["browser", "unclassified"], "independent_sqlite_version": sqlite3.sqlite_version,
                "db_bytes": path.stat().st_size, "db_sha256": sha(path)}


def phase_summary(start, end, samples):
    wall = end["t_s"] - start["t_s"]
    cpu = end["cpu_s"] - start["cpu_s"]
    included = [s for s in samples if start["t_s"] <= s["t_s"] <= end["t_s"]]
    out = {"wall_s": wall, "cpu_s": cpu, "cpu_pct_one_logical_core": cpu / wall * 100,
           "start_private_bytes": start["private_bytes"], "start_working_set_bytes": start["working_set_bytes"]}
    for field in ("private_bytes", "working_set_bytes"):
        values = [s[field] for s in included if s[field] is not None]
        out["median_" + field] = statistics.median(values)
        out["peak_" + field] = max(values)
    return out


def run_one(name, manifest, args, index, warmup):
    kernel, psapi = windows_api()
    work = Path(manifest["work_dir"])
    db = work / f"{index:02}-{name}-{'warmup' if warmup else 'measured'}.sqlite"
    argv = probe_command(name, manifest, args, db, args.idle_ms, args.interval_ms)
    env = os.environ.copy()
    env.update(DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_SKIP_FIRST_TIME_EXPERIENCE="1", DOTNET_GENERATE_ASPNET_CERTIFICATE="false")
    start_time = time.perf_counter()
    before_system = system_cpu(kernel)
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", env=env)
    handle = kernel.OpenProcess(0x410, False, proc.pid)
    if not handle:
        raise C.WinError(C.get_last_error())
    received = queue.Queue()
    def reader():
        for line in proc.stdout:
            received.put(line.rstrip("\r\n"))
    reading = threading.Thread(target=reader, daemon=True)
    reading.start()
    stdout, samples, boundaries = [], [], {}
    try:
        while proc.poll() is None or not received.empty() or reading.is_alive():
            if time.perf_counter() - start_time > 90:
                proc.kill()
                raise TimeoutError(name)
            sample = resources(kernel, psapi, handle, start_time)
            samples.append(sample)
            try:
                line = received.get(timeout=0.05)
            except queue.Empty:
                continue
            stdout.append(line)
            if line.startswith("PHASE\t"):
                point = resources(kernel, psapi, handle, start_time)
                samples.append(point)
                boundaries[line.split("\t")[1]] = point
        proc.wait()
        stderr = proc.stderr.read()
        if proc.returncode != 0:
            raise RuntimeError(f"{name}: exit={proc.returncode}, stdout={stdout}, stderr={stderr}")
        final = resources(kernel, psapi, handle, start_time)
    finally:
        kernel.CloseHandle(handle)
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    after_system = system_cpu(kernel)
    all_cpu = (after_system["kernel_s"] + after_system["user_s"]) - (before_system["kernel_s"] + before_system["user_s"])
    busy = all_cpu - (after_system["idle_s"] - before_system["idle_s"])
    validation = verify_database(db, fixture_rows(args.fixture), stdout)
    return {"implementation": name, "sequence_index": index, "warmup": warmup, "pid": proc.pid,
            "command": argv, "stdout": stdout, "stderr": stderr, "exit_code": proc.returncode,
            "startup_to_idle_s": boundaries["idle"]["t_s"], "idle": phase_summary(boundaries["idle"], boundaries["active"], samples),
            "active": phase_summary(boundaries["active"], boundaries["verify"], samples), "total_cpu_s": final["cpu_s"],
            "total_wall_s": final["t_s"], "system_busy_pct_all_cores": 100 * busy / all_cpu,
            "phase_boundaries": boundaries, "raw_samples": samples, "validation": validation}


def measure(args):
    assert os.name == "nt", "Windows-only measurement harness"
    assert C.sizeof(C.c_void_p) == 8, "use 64-bit Python with x64 probes"
    manifest = json.loads(args.build_manifest.read_text(encoding="utf-8"))
    for name, expected in manifest["source_sha256"].items():
        if name == "run.py":
            continue  # Harness is interpreted; record its current hash separately.
        assert sha(HERE / name) == expected, f"source changed since build: {name}"
    for name in ("rust", "csharp"):
        assert sha(manifest["executables"][name]) == manifest["executables_sha256"][name], f"binary changed: {name}"
    manifest["work_dir"] = tempfile.mkdtemp(prefix="FocusWatchPairedAgentSeries-")
    native = Path(os.environ["WINDIR"]) / "System32" / "winsqlite3.dll"
    public_build = {key: value for key, value in manifest.items() if key not in ("work_dir", "executables", "dotnet_info", "rustc_path")}
    public_build["build_runner_sha256"] = public_build["source_sha256"].pop("run.py", None)
    public_build["measurement_runner_sha256"] = sha(HERE / "run.py")
    report = {"purpose": "paired synthetic agent resource/correctness probe; no Windows hook/input/media event cost measured",
              "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "os": platform.platform(), "machine": platform.machine(), "logical_cpu_count": os.cpu_count(),
              "processor": platform.processor(), "native_sqlite_path": str(native), "native_sqlite_sha256": sha(native),
              "fixture_path": str(args.fixture), "fixture_sha256": sha(args.fixture), "schema_sha256": sha(HERE / "schema.sql"),
              "build": public_build, "parameters": {"idle_ms": args.idle_ms, "interval_ms": args.interval_ms, "batch_size": args.batch_size, "pairs": args.pairs, "sample_period_s": 0.05, "csharp_host": args.csharp_host},
              "scope": "single application process per run, no child processes by construction; Python harness and kernel/socket/file-cache memory excluded; working set is not PSS",
              "runs": []}
    order = [("rust", True), ("csharp", True)]
    for pair in range(args.pairs):
        order.extend((name, False) for name in (("rust", "csharp") if pair % 2 == 0 else ("csharp", "rust")))
    for index, (name, warmup) in enumerate(order):
        print(f"START {index + 1}/{len(order)} {name} warmup={warmup}", flush=True)
        result = run_one(name, manifest, args, index, warmup)
        report["runs"].append(result)
        write_results(report, manifest, args)
        print(f"DONE {name} correctness=pass idle_cpu={result['idle']['cpu_s']:.6f}s active_cpu={result['active']['cpu_s']:.6f}s active_private_peak={result['active']['peak_private_bytes']}", flush=True)
    report["all_functional_checks_pass"] = True
    measured = [run for run in report["runs"] if not run["warmup"]]
    metrics = ("startup_to_idle_s", "idle.cpu_s", "idle.cpu_pct_one_logical_core", "idle.median_private_bytes",
               "idle.median_working_set_bytes", "active.cpu_s", "active.cpu_pct_one_logical_core", "active.peak_private_bytes", "active.peak_working_set_bytes")
    def value(run, key):
        result = run
        for part in key.split("."):
            result = result[part]
        return result
    report["aggregate"] = {}
    for name in ("rust", "csharp"):
        runs = [run for run in measured if run["implementation"] == name]
        report["aggregate"][name] = {key: {"median": statistics.median(values), "min": min(values), "max": max(values), "values": values}
                                       for key in metrics for values in [[value(run, key) for run in runs]]}
    report["pairs"] = []
    for offset in range(0, len(measured), 2):
        pair = measured[offset:offset + 2]
        by_name = {run["implementation"]: run for run in pair}
        report["pairs"].append({"order": [run["implementation"] for run in pair], "csharp_over_rust": {
            key: value(by_name["csharp"], key) / value(by_name["rust"], key) if value(by_name["rust"], key) else None for key in metrics}})
    write_results(report, manifest, args)
    print(f"RESULTS {args.output}", flush=True)


def write_results(report, manifest, args):
    # Keep the operational manifest (absolute paths and dotnet --info) in TEMP.
    # Published raw evidence uses portable placeholders, never profile names.
    public = public_data(report, manifest)
    text = json.dumps(public, indent=2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.output, "wt", encoding="utf-8") as stream:
        stream.write(text)
    summary = public
    for run in summary["runs"]:
        run.pop("raw_samples", None)
    (args.output.parent / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--measure", action="store_true")
    parser.add_argument("--smoke", action="store_true", help="functional only, no performance sampling")
    parser.add_argument("--dotnet", default="dotnet")
    parser.add_argument("--csharp-host", choices=("apphost", "dotnet"), default="apphost", help="record explicit framework-dependent launch mode")
    parser.add_argument("--rustc", type=Path, default=Path("rustc"))
    parser.add_argument("--fixture", type=Path, default=HERE.parent / "fixture.tsv")
    parser.add_argument("--build-manifest", type=Path, help="operational paths/SDK info; keep this file in TEMP")
    parser.add_argument("--output", type=Path, default=HERE / "results.json.gz")
    parser.add_argument("--pairs", type=int, default=5)
    parser.add_argument("--idle-ms", type=int, default=10000)
    parser.add_argument("--interval-ms", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()
    assert sum((args.build, args.measure, args.smoke)) == 1, "choose exactly one of --build / --measure / --smoke"
    if args.build:
        build(args)
    elif args.smoke:
        assert args.build_manifest, "--build-manifest from the TEMP build directory is required"
        smoke(args)
    else:
        assert args.build_manifest, "--build-manifest from the TEMP build directory is required"
        measure(args)


if __name__ == "__main__":
    main()
