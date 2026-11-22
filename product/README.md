# FocusWatch P0

A synthetic desktop slice with one local SQLite writer and an independent report. The agent initializes an explicit, empty profile with a made-up day, 2026-11-17 UTC. Starting it does not register autostart or enable data collection. Reports retain independent sources, exact coverage, uncertainty and unattributed period aggregates. Manual corrections are separate from observations.

## Build and verify

From this directory use Rust 1.100.0, a native C toolchain (MSVC x64 and Windows SDK on Windows), Node 24 and npm. Both lockfiles are inputs. Dependency downloads are needed during preparation. The installed app runs offline.

~~~sh
cargo test --locked
cargo build --release --locked --bin focuswatch-agent
cd desktop
npm ci
npm run runtime
npm test
npm run build
cd ..
~~~

On Windows, from a developer PowerShell, assemble and install the package in a new current-user directory:

~~~powershell
$package = Join-Path $env:TEMP ("FocusWatch-package-" + [guid]::NewGuid())
node scripts/package.mjs target/release/focuswatch-agent.exe $package
$install = & (Join-Path $package 'Install-P0.ps1')
~~~

Start the agent in one terminal. Keep the state and endpoint names to reopen the same report. For a fresh demo pick a new state directory.

~~~powershell
$state = Join-Path $env:LOCALAPPDATA 'FocusWatch-Synthetic-P0-Data'
$endpoint = '\\.\pipe\focuswatch-p0-demo'
& (Join-Path $install 'focuswatch-agent.exe') --state $state --endpoint $endpoint
~~~

After READY, open the report from another PowerShell:

~~~powershell
$install = Join-Path $env:LOCALAPPDATA 'FocusWatch-Synthetic-P0'
& (Join-Path $install 'report/FocusWatch-Report.exe') --endpoint '\\.\pipe\focuswatch-p0-demo' --date 2026-11-17 --zone UTC
~~~

Filter for **synthetic-555**, open **Correct**, enter a category and save. Close the report and rerun the last command to read back the correction. Ctrl+C in the agent terminal ends the session. Reuse the same state on restart. This unsigned development package requires a Windows installation that accepts its binaries.

On Linux use a private state directory (0700) and its absolute path followed by /report.sock as the endpoint. For example, in two terminals:

~~~sh
# Terminal A, from product/
./target/release/focuswatch-agent --state "$HOME/focuswatch-synthetic-p0" --endpoint "$HOME/focuswatch-synthetic-p0/report.sock"
# Terminal B, from product/desktop
npm start -- --endpoint "$HOME/focuswatch-synthetic-p0/report.sock" --date 2026-11-17 --zone UTC
~~~

Run the independently framed process/restart check with Node 24:

~~~sh
node tests/process.mjs ./target/release/focuswatch-agent
~~~

On Windows append .exe to the agent path. An optional second argument selects the installed report executable for native keyboard correction and reopening after restart. The harness uses fresh temporary profiles. First-party code is in src (domain, SQLite, versioned protocol and OS-specific listener) and desktop. Client connections send one little-endian u32 length followed by UTF-8 JSON. The server validates the version and role, limits clients, payloads and waiting time, and returns one framed response. Only the agent opens the database.
