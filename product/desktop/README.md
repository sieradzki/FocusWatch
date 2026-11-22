# FocusWatch local report (P0)

Separate Electron/React/TypeScript report for the Rust agent in `product/`.
It reads one bounded day projection and sends category corrections over the
agent's private local IPC endpoint. It does not open SQLite, run a watcher,
start the agent, inspect other applications, or call a cloud service.

## Build and run

Node 24+ is required to build. Dependencies are exact versions and the lockfile
must be committed with changes. From this directory:

```sh
npm ci --ignore-scripts --no-audit --no-fund
npm run runtime
npm test
npm run build
npm start -- --endpoint <local-pipe-or-absolute-socket> --date 2026-11-17 --zone UTC
```

`runtime` explicitly downloads the pinned Electron distribution using its
official installer/checksums. No system installation is performed. Windows
uses a local `\\.\pipe\...` endpoint. Unix uses the agent's absolute
`<private state directory>/report.sock`. There is no TCP endpoint or renderer
control over connection paths. Start the agent separately, using a fresh
private state directory for the synthetic P0 fixture; the agent prints `READY`.
The default report day is the fixture's `2026-11-17`, in `UTC`.

Optional `--profile <absolute directory>` isolates Electron's own profile for
tests. The agent's state directory and the report profile are separate.
The product packaging entry point lives in `../scripts/package.mjs` and stages
the agent together with this report; this directory does not provide another
packager. A source build is not an installer or signing acceptance result.

## Interface and transport boundary

The renderer uses native labelled inputs, forms, buttons and tables, visible
keyboard focus and persistent live status/error text. Exact observations are
paged in the table (50 rows); search includes application, category, source and
observation ID. The day and IANA zone are explicit. Coverage, explicit unknown
intervals and periods without any exact observations are distinct. Source
overlap is preserved and never labelled attention or productivity.

Period aggregates are separate from the exact timeline and its category totals.
An aggregate extending outside the selected day is shown in its original scope,
without allocating a proportion to this day. Each interval exposes device,
source, session, generation, sequence, precision, time uncertainty and clock
state. Open observations stop at their last confirmed checkpoint.

Choose **Correct** using Enter or Space; focus moves to **New category**. Edit,
Tab to **Save category**, then press Enter. A correction uses that observation's
correction revision, not the report snapshot revision. On conflict the report
refreshes and the user reviews the latest state. On uncertain failure there is
no automatic correction retry. An explicit identical retry reuses its command
ID. Successful saves are confirmed by a new report from the agent.

Each connection carries one request and one response: 4-byte little-endian byte
length followed by strict UTF-8 JSON. Requests are limited to 4096 bytes,
responses to 4 MiB and each request to eight seconds. The client enforces the
version/role/command allowlist, validates response fields and dates, and rejects
truncated, oversized or malformed frames. It opens at most one request at once.
No arbitrary SQL, filesystem, shell, generic IPC or endpoint API is exposed to
the renderer.

The renderer has Node integration disabled, context isolation, OS sandbox and
web security enabled. The bridge exposes only `initialQuery`, `report` and
`correct`. Main checks the sending window and main frame. Only the three local
renderer resources are allowed through this session's request filter. A strict
CSP disallows inline scripts, connections, frames, objects and form navigation;
permissions, navigation, new windows and webviews are denied. No crash reporter
or telemetry SDK is configured. These controls do not substitute for observing
network traffic in release acceptance. The report profile is not an encrypted
data store.

Electron/Chromium must receive regular security updates. Build dependencies and
the pinned runtime should be reviewed together. Primary implementation guidance:
[Electron security](https://www.electronjs.org/docs/latest/tutorial/security),
[automated testing](https://www.electronjs.org/docs/latest/tutorial/automated-testing),
[webContents](https://www.electronjs.org/docs/latest/api/web-contents).

## Synthetic real-window smoke

Use a fresh agent state, isolated report profile and new evidence directory:

```sh
npm start -- --endpoint <private endpoint> --date 2026-11-17 --zone UTC --profile <absolute isolated profile> --smoke-output <absolute evidence directory>
```

The report must contain only `synthetic` observations/aggregates; smoke mode
rejects any other quality before sending the report to the renderer. It tests
the real UI against the separate real agent:

1. Asserts the sandboxed preload's process state, isolation and absence of Node
   globals in the renderer.
2. Filters to `synthetic-555`, focuses its native Correct button and sends Space
   through **this window's** `webContents.sendInputEvent`. Focus must enter the
   category input.
3. Sends select-all, text insertion, Tab and Enter to the owned webContents.
   Saving must reread `learning`, a manual correction and the incremented
   per-observation revision. Learning increases by exactly 60,000 ms and
   unclassified decreases by the same amount; observed coverage is unchanged.
4. On Windows, enables Chromium accessibility and calls the bundled targeted
   `probe-uia.ps1`. The helper checks HWND ownership/visibility, then uses
   `AutomationElement.FromHandle` and searches **only this report's descendants**
   for Document plus named, enabled, focusable filter/category/Correct/Save
   controls. It does not enumerate the desktop or act on another app.
5. Writes `smoke.json`, own-surface `before.png`/`after.png` using `capturePage`,
   and Windows `uia.json`, then exits 0 only on success. Failure exits 1; no
   partial success is treated as a passed smoke.

Restart the agent using the same state directory and run a second report with
a fresh profile and output directory:

```sh
npm start -- --endpoint <private endpoint> --date 2026-11-17 --zone UTC --profile <another isolated profile> --smoke-output <another evidence directory> --smoke-expect-category learning
```

The second pass checks persisted category/revision/manual-correction text and
does not make a correction. The test driver lives in the main process; no test
privilege or generic automation channel is exposed to the renderer.

Limitations: input is programmatic, scoped to the app, and is not physical
keyboard or global-input testing. UIA proves the inspected names, roles and
states, not screen-reader usability. `capturePage` captures this app surface,
not the private desktop or final monitor presentation. Linux Xvfb proves a
Linux GUI path, not actual Arch/dwm/X11 acceptance. Windows policy blocks must
be reported; do not disable or bypass Smart App Control. P0 does not include a
real collector, personal data trial, updater, signing or store publication.

`npm test` contains independent representative wire fixtures and actual local
pipe/socket tests for fragmented frames, Unicode, length limits, malformed
UTF-8/JSON, truncation, excess data, timeouts, calendar/zone validation,
separate interval/aggregate scopes and correction revision validation. It does
not require a desktop or read personal data. Platform GUI/packaging evidence
is recorded by the product-level verification harness, not inferred from these
unit tests.
