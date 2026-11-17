"""Small synthetic CI evidence collector. Never reads user activity or credentials."""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

def redact_text(text):
    prefixes = [(os.environ.get(key), replacement) for key, replacement in
                (("GITHUB_WORKSPACE", "<repo>"), ("RUNNER_TEMP", "<temp>"),
                 ("USERPROFILE", "<userprofile>"), ("CARGO_HOME", "<cargo-home>"),
                 ("RUSTUP_HOME", "<rustup-home>"))]
    for prefix, replacement in prefixes:
        if prefix:
            for variant in (prefix, prefix.replace("\\", "/"), json.dumps(prefix)[1:-1]):
                text = text.replace(variant, replacement)
    text = re.sub(r"(?i)\b[A-Z]:[\\/]Users[\\/][^\\/\r\n\"\s]+", "<userprofile>", text)
    text = re.sub(r"(?i)\b[A-Z]:\\\\Users\\\\[^\\\r\n\"\s]+", "<userprofile>", text)
    return text

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def version(command):
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=20)
        return redact_text((result.stdout + result.stderr).strip()) if result.returncode == 0 else "unavailable"
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"

def environment(output):
    output.mkdir(parents=True, exist_ok=True)
    fixture = Path("scripts/research/2026-11-paired/fixture.tsv")
    data = {
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "os": platform.platform(), "machine": platform.machine(),
        "python": sys.version, "pointer_bits": 64 if sys.maxsize > 2**32 else 32,
        "logical_cpu_count": os.cpu_count(),
        "runner_image_os": os.environ.get("ImageOS"),
        "runner_image_version": os.environ.get("ImageVersion"),
        "github_repository": os.environ.get("GITHUB_REPOSITORY"),
        "github_commit": os.environ.get("GITHUB_SHA"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "versions": {name: version(command) for name, command in
                     (("rustc", ["rustc", "--version", "--verbose"]), ("cargo", ["cargo", "--version"]),
                      ("dotnet_sdk", ["dotnet", "--version"]), ("node", ["node", "--version"]),
                      ("npm", ["npm", "--version"]))},
        "fixture_sha256": sha(fixture), "scope": "synthetic CI runner; not owner's hardware, private data or product readiness"
    }
    (output / "environment.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

def collect_egui(log, code, output):
    output.mkdir(parents=True, exist_ok=True)
    text = redact_text(log.read_text(encoding="utf-8-sig", errors="replace"))
    with gzip.open(output / "cargo-test.log.gz", "wt", encoding="utf-8") as stream:
        stream.write(text)
    (output / "cargo-test-tail.log").write_text("\n".join(text.splitlines()[-180:]) + "\n", encoding="utf-8")
    names = ("accesskit_click", "keyboard_ctrl_enter", "keyboard_tab_space")
    states = {}
    for name in names:
        match = re.search(r"test\s+" + name + r"\s+\.\.\.\s+(ok|FAILED)", text)
        states[name] = "pass" if match and match.group(1) == "ok" else ("fail" if match else "not_run")
    base = Path("scripts/research/2026-11-paired/egui")
    data = {
        "status": "pass" if code == 0 and all(value == "pass" for value in states.values()) else "failed_or_incomplete",
        "exit_code": code, "tests": states,
        "probe_result_lines": [line for line in text.splitlines() if "PROBE_RESULT " in line],
        "source_sha256": {str(path.relative_to(base)): sha(path) for path in
                          [base / "Cargo.toml", base / "Cargo.lock", base / "src/lib.rs", base / "tests/semantic.rs"]},
        "fixture_sha256": sha(base.parent / "fixture.tsv"),
        "headless": True, "gpu_rendering_measured": False, "native_uia_measured": False,
        "timing_comparable_to_paired_ui": False
    }
    (output / "result.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

def redact_tree(root):
    if not root.exists():
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8") as stream:
                text = stream.read()
            with gzip.open(path, "wt", encoding="utf-8") as stream:
                stream.write(redact_text(text))
        elif path.suffix.lower() in (".json", ".txt", ".log", ".xml"):
            path.write_text(redact_text(path.read_text(encoding="utf-8-sig", errors="replace")), encoding="utf-8")
    print("Evidence contains only synthetic probe files; operational paths redacted.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("environment", "egui", "redact"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--exit-code", type=int)
    args = parser.parse_args()
    if args.mode == "environment":
        environment(args.output)
    elif args.mode == "egui":
        collect_egui(args.log, args.exit_code, args.output)
    else:
        redact_tree(args.root)

if __name__ == "__main__":
    main()
