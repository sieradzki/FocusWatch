#!/usr/bin/env python3
"""Small reproducible fault/lifecycle experiment using only synthetic events.

Not a benchmark or a production IPC implementation. Compiles standalone Rust std
code. Does not connect to X11, the user's browser, FocusWatch or the network.
"""
import io
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "build/research/desktop"


def native_message(data):
    """Chrome/Firefox native-endian 32-bit length framing, own stricter 64KiB cap."""
    head = data.read(4)
    if len(head) != 4:
        raise ValueError("incomplete header")
    length = struct.unpack("=I", head)[0]
    if length > 65536:
        raise ValueError("message exceeds probe limit")
    body = data.read(length)
    if len(body) != length:
        raise ValueError("incomplete body")
    return json.loads(body)


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    binary = WORK / "synthetic-collector"
    subprocess.run(["rustc", "+stable", "--edition=2021", "-C", "opt-level=1",
                    str(Path(__file__).with_suffix(".rs")), "-o", str(binary)], check=True)
    checks = {}
    process = None
    with tempfile.TemporaryDirectory(prefix="collector-", dir=WORK) as directory:
        path = Path(directory)
        socket_path = path / "collector.sock"
        def start():
            p = subprocess.Popen([str(binary), directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            deadline = time.monotonic() + 5
            while not socket_path.exists():
                if p.poll() is not None: raise RuntimeError(p.stderr.read().decode())
                if time.monotonic() > deadline: raise RuntimeError("collector socket timeout")
                time.sleep(0.02)
            return p
        def snapshot(command=b"snapshot\n"):
            with socket.socket(socket.AF_UNIX) as client:
                client.settimeout(2)
                client.connect(str(socket_path))
                client.sendall(command)
                return json.loads(client.recv(4096))
        try:
            process = start()
            before = snapshot()["sequence"]
            time.sleep(0.25)
            checks["collects_without_ui"] = snapshot()["sequence"] > before
            checks["private_socket_mode_0600"] = (socket_path.stat().st_mode & 0o777) == 0o600
            # The UI is an entirely separate client process, intentionally crashes.
            ui = subprocess.run([os.sys.executable, "-c",
                "import socket,sys,os;s=socket.socket(socket.AF_UNIX);s.connect(sys.argv[1]);"
                "s.sendall(b'snapshot\\n');s.recv(4096);s.close();os._exit(23)", str(socket_path)])
            after_ui = snapshot()["sequence"]
            time.sleep(0.25)
            checks["ui_crash_does_not_stop_collector"] = ui.returncode == 23 and snapshot()["sequence"] > after_ui
            checks["unsupported_message_rejected"] = "error" in snapshot(b"unsupported\n")
            state = snapshot()
            checks["snapshot_can_represent_foreground_and_media"] = state["foreground"] == "synthetic-editor" and state["media_playing"]
            process.kill(); process.wait(timeout=3)
            records_before = (path / "synthetic-sequence.log").read_text().splitlines()
            # Simulate an interrupted journal write. Only this isolated test file is touched.
            with (path / "synthetic-sequence.log").open("a") as output:
                output.write("999")
            socket_path.unlink()
            process = start()
            time.sleep(0.25)
            checks["collector_restart_advances_sequence"] = snapshot()["sequence"] > int(records_before[-1])
            process.kill(); process.wait(timeout=3)
            records = [int(x) for x in (path / "synthetic-sequence.log").read_text().splitlines()]
            checks["restart_discards_partial_tail_no_duplicate_sequence"] = records == list(range(1, len(records)+1))
        finally:
            if process and process.poll() is None:
                process.kill(); process.wait(timeout=3)
    payload = json.dumps({"type":"media_state", "playing":True, "tab":"synthetic-tab"}).encode()
    checks["native_message_roundtrip"] = native_message(io.BytesIO(struct.pack("=I",len(payload))+payload))["playing"] is True
    for name, raw in [("reject_oversized_native_message", struct.pack("=I",65537)),
                      ("reject_truncated_native_message", struct.pack("=I",5)+b"{}")]:
        try:
            native_message(io.BytesIO(raw))
            checks[name] = False
        except ValueError:
            checks[name] = True
    result = {"status":"pass" if all(checks.values()) else "fail", "checks":checks,
              "scope":"Synthetic Rust Unix-socket collector + journal + fake UI clients; no actual capture/browser integration",
              "limitations":["No Windows named pipe/permissions test", "No installed autostart or updater",
                "Single synthetic producer, no DB or durable sync protocol", "Native framing tested in memory, no browser extension installed",
                "No production IPC security claim; one-read socket parser intentionally rejects partial requests",
                "Crash test checks sequence consistency, not recording of events during downtime"]}
    destination = ROOT / "docs/research/2026-09/desktop-results-lifecycle.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))
    if not all(checks.values()): raise SystemExit(1)


if __name__ == "__main__": main()
