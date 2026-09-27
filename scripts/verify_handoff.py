#!/usr/bin/env python3
"""Verify the committed handoff snapshot using Python 3.10+ standard library.

Does not install dependencies, contact services, launch FocusWatch, read personal
databases or rerun benchmarks. The cloud calculator writes only to a temporary
directory. Passing checks establish snapshot consistency, not product readiness.
"""

import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/research/2026-09"
SOURCES = ROOT / "scripts/research"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_result(name):
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def check_hash(filename, expected):
    actual = hashlib.sha256((SOURCES / filename).read_bytes()).hexdigest()
    require(actual == expected, f"Recorded source hash differs: {filename}")


def main():
    required = [
        "AGENTS.md", "README.md", "docs/README.md", "docs/HANDOFF.md",
        "docs/PROJECT_BRIEF.md", "docs/architecture/DECISIONS.md",
        "docs/IMPLEMENTATION_PLAN.md", "scripts/research/README.md",
        "docs/research/2026-09/README.md",
        "docs/research/2026-09/desktop-results.md",
    ]
    for filename in required:
        require((ROOT / filename).is_file(), f"Missing handoff file: {filename}")

    json_files = list(REPORTS.glob("*.json"))
    for path in json_files:
        json.loads(path.read_text(encoding="utf-8"))
    py_files = [*SOURCES.glob("*.py"), Path(__file__)]
    for path in py_files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"PASS: required context, {len(json_files)} JSON and {len(py_files)} Python files")

    hashes = 0
    for result, source in [
        ("data-results.json", "data_benchmark.py"),
        ("postgres-results.json", "postgres_benchmark.py"),
        ("sync-semantics-results.json", "sync_semantics_probe.py"),
    ]:
        check_hash(source, read_result(result)["script_sha256"])
        hashes += 1
    for result, key in [
        ("desktop-results.json", "source_sha256"),
        ("desktop-results-1000.json", "source_sha256"),
        ("realtime-results.json", "sources_sha256"),
    ]:
        for source, expected in read_result(result)[key].items():
            check_hash(source, expected)
            hashes += 1
    print(f"PASS: {hashes} recorded source-hash references")

    datasets = read_result("data-results.json")["datasets"]
    require(sorted(d["rows"] for d in datasets) == [1_000_000, 10_000_000],
            "Missing expected data scale")
    require(all(d["query_window"]["day_rows"] == 3840 for d in datasets),
            "Data results do not use the recorded complete-day workload")
    pg = read_result("postgres-results.json")
    require(pg["rows"] == 1_000_000, "Unexpected PostgreSQL data scale")
    require(pg["durable_ingestion_batches"]["batches"] == 200
            and pg["durable_ingestion_batches"]["batch_size"] == 8,
            "Unexpected PostgreSQL transaction sample")
    sync = read_result("sync-semantics-results.json")
    require(sync["run"] == len(sync["tests"]) == 10
            and sync["failures"] == sync["errors"] == 0,
            "Stored semantic checks are incomplete or failed")
    lifecycle = read_result("desktop-results-lifecycle.json")
    require(lifecycle["status"] == "pass" and len(lifecycle["checks"]) == 10
            and all(v is True for v in lifecycle["checks"].values()),
            "Stored lifecycle checks are incomplete or failed")
    for name, segments in [("desktop-results-1000.json", 1000),
                           ("desktop-results.json", 10000)]:
        ui = read_result(name)
        require(ui["synthetic_segments"] == segments and ui["repeats"] == 3
                and len(ui["runs"]) == 9, f"Incomplete UI cohort: {name}")
        require(all(r["status"] == "ok" for r in ui["runs"]),
                f"Stored UI failures: {name}")
        for runtime in ["tauri", "electron", "qtquick"]:
            require(sum(r["runtime"] == runtime for r in ui["runs"]) == 3,
                    f"Missing runtime repetitions: {name}/{runtime}")
    x11 = read_result("desktop-results-x11.json")
    require(x11["synthetic_values_equal"] is True and len(x11["runs"]) == 10,
            "Incomplete X11 comparison")
    realtime = read_result("realtime-results.json")["runs"]
    require(sorted(r["connections"] for r in realtime) == [250, 500, 1000],
            "Incomplete realtime cohorts")
    for run in realtime:
        client, server = run["client_result"], run["server_counters"]
        require(not client["failures"] and client["received"] > 0
                and client["received"] == server["accepted"] == server["delivered"]
                and server["rejected"] == 2, "Stored realtime delivery failure")
    print("PASS: recorded data scales, 20 semantic/lifecycle checks, 18 UI runs and 3 WS cohorts")

    markdown = [ROOT / "README.md", ROOT / "AGENTS.md", SOURCES / "README.md",
                *(ROOT / "docs").rglob("*.md")]
    for path in markdown:
        for target in re.findall(r"\]\(([^()\n]+)\)", path.read_text(encoding="utf-8")):
            if target.startswith(("http:", "https:", "#", "mailto:", "app:")):
                continue
            relative = unquote(target.split("#", 1)[0].strip("<>"))
            require((path.parent / relative).exists(),
                    f"Missing local link in {path.relative_to(ROOT)}: {target}")
    print(f"PASS: local link targets in {len(markdown)} Markdown documents")

    with tempfile.TemporaryDirectory(prefix="focuswatch-handoff-") as directory:
        output = Path(directory) / "cloud-cost-results.json"
        subprocess.run([
            sys.executable, "-X", "utf8", str(SOURCES / "cloud_costs.py"),
            "--input", str(REPORTS / "cloud-cost-inputs.json"),
            "--output", str(output),
        ], check=True, capture_output=True, text=True, encoding="utf-8", timeout=30, cwd=ROOT)
        actual = json.loads(output.read_text(encoding="utf-8"))
        require(actual == read_result("cloud-cost-results.json"),
                "Cloud calculator differs from the recorded result")
    print("PASS: offline cloud calculator reproduces the recorded JSON")
    print("Handoff snapshot is consistent. Benchmarks and application tests were not rerun.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, SyntaxError, subprocess.SubprocessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
