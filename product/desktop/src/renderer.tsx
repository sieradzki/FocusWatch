import { StrictMode, useEffect, useRef, useState, type FormEvent } from 'react';
import { createRoot } from 'react-dom/client';
import type { Correction, DayReport, ReportInterval } from './contract.ts';
import type { Query } from './cli.ts';

const PAGE_SIZE = 50;
const COLORS = ['#315dc9', '#7851aa', '#287a65', '#b27924', '#566779', '#9a4c5b'];
const MESSAGES: Record<string, string> = {
  conflict: 'This observation changed since it was opened. The report has been refreshed. Review its category before saving again.',
  not_found: 'This observation is no longer available. Refresh the report.',
  invalid_request: 'Check the date, time zone or category and try again.',
  unsupported_version: 'The agent and report versions do not match. Update both together.',
  invalid_role: 'The agent refused this report connection.',
  report_too_large: 'This day exceeds the report limit. No partial result is shown.',
  agent_timeout: 'The agent did not respond in time. A correction might have been saved. Refresh before retrying.',
  agent_unavailable: 'The local agent is unavailable. Start it, then refresh the report.',
  busy: 'A request is already in progress. Try again when it finishes.',
};
function message(code: string) { return MESSAGES[code] ?? 'The report could not be read or confirmed. Refresh and try again.'; }
export function duration(ms: number): string {
  const seconds = Math.floor(ms / 1000), hours = Math.floor(seconds / 3600), minutes = Math.floor(seconds % 3600 / 60);
  return hours ? `${hours}h ${minutes}m` : minutes ? `${minutes}m${seconds % 60 ? ` ${seconds % 60}s` : ''}` : `${seconds}s`;
}
function time(ms: number, zone: string) { return new Intl.DateTimeFormat('en-GB', { timeZone: zone, hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(ms); }
function localDate(ms: number, zone: string) { return new Intl.DateTimeFormat('en-GB', { timeZone: zone, dateStyle: 'medium', timeStyle: 'short' }).format(ms); }
function Timeline({ report }: { report: DayReport }) {
  const sourceKey = (row: ReportInterval) => JSON.stringify([row.device_id, row.source_id, row.session_id, row.generation]);
  const sources = [...new Set(report.intervals.map(sourceKey))];
  const categories = [...new Set(report.intervals.map(row => row.category))].sort();
  const color = (category: string) => COLORS[categories.indexOf(category) % COLORS.length] ?? COLORS[0];
  return <section className="panel" aria-labelledby="timeline-title">
    <h2 id="timeline-title">Observed intervals</h2>
    <p className="muted">One lane per source. Overlap is preserved; it does not measure shared attention. Select an interval in the table to correct it.</p>
    {sources.length ? <svg className="timeline" viewBox={`0 0 1000 ${Math.max(sources.length, 1) * 26}`} preserveAspectRatio="none" aria-hidden="true">
      {sources.map((source, lane) => <g key={source}>
        <rect x="0" y={lane * 26 + 2} width="1000" height="20" fill="#edf0f5" />
        {report.intervals.filter(row => sourceKey(row) === source).map(row => <rect key={row.id} data-observation={row.id}
          x={(row.start_ms - report.start_ms) / report.day_duration_ms * 1000} y={lane * 26 + 2}
          width={Math.max((row.end_ms - row.start_ms) / report.day_duration_ms * 1000, .3)} height="20" fill={row.quality === 'unknown' ? '#8b98ab' : color(row.category)} />)}
      </g>)}
    </svg> : <p>No exact intervals were received for this day.</p>}
    <div className="axis"><span>{localDate(report.start_ms, report.time_zone)}</span><span>{localDate(report.end_ms, report.time_zone)} (exclusive)</span></div>
    <div className="legend">{categories.map(category => <span key={category}><svg width="10" height="10" aria-hidden="true"><rect width="10" height="10" fill={color(category)} /></svg>{category}</span>)}{report.intervals.some(row => row.quality === 'unknown') && <span><svg width="10" height="10" aria-hidden="true"><rect width="10" height="10" fill="#8b98ab" /></svg>Unknown observation</span>}</div>
  </section>;
}

function App() {
  const [query, setQuery] = useState<Query>({ date: '', zone: 'UTC' });
  const [report, setReport] = useState<DayReport>();
  const [selectedId, setSelectedId] = useState<string>();
  const [category, setCategory] = useState('');
  const [filter, setFilter] = useState('');
  const [page, setPage] = useState(0);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [fieldError, setFieldError] = useState('');
  const [status, setStatus] = useState('');
  const categoryInput = useRef<HTMLInputElement>(null);
  const pendingCommand = useRef<Correction | undefined>(undefined);
  const selected = report?.intervals.find(row => row.id === selectedId);

  async function read(next: Query): Promise<DayReport | undefined> {
    const result = await window.focuswatch.report(next);
    if (!result.ok) { setError(message(result.error)); return; }
    setReport(result.data);
    return result.data;
  }
  useEffect(() => {
    let live = true;
    (async () => {
      setPending(true);
      try {
        const initial = await window.focuswatch.initialQuery();
        if (!live) return;
        setQuery(initial);
        const result = await window.focuswatch.report(initial);
        if (!live) return;
        if (result.ok) setReport(result.data); else setError(message(result.error));
      } catch { if (live) setError('The local report bridge is unavailable. Close and reopen this window.'); }
      finally { if (live) setPending(false); }
    })();
    return () => { live = false; };
  }, []);

  async function load(event: FormEvent) {
    event.preventDefault();
    if (pending) return;
    setPending(true); setError(''); setFieldError(''); setStatus('');
    try {
      const next = await read(query);
      if (next) { setPage(0); setSelectedId(undefined); pendingCommand.current = undefined; setStatus('Report refreshed.'); }
    } catch { setError('The report could not be refreshed.'); }
    finally { setPending(false); }
  }
  function select(row: ReportInterval) {
    setSelectedId(row.id); setCategory(row.category); setFieldError(''); setError(''); setStatus('');
    pendingCommand.current = undefined;
    // Move to the editor after its native input is rendered, for pointer and keyboard users alike.
    requestAnimationFrame(() => { categoryInput.current?.focus(); categoryInput.current?.select(); });
  }
  async function correct(event: FormEvent) {
    event.preventDefault();
    if (!selected || !report || pending) return;
    const nextCategory = category.trim();
    if (!nextCategory || new TextEncoder().encode(nextCategory).length > 128 || /[\u0000-\u001f\u007f]/.test(nextCategory)) {
      setFieldError('Enter a category of up to 128 UTF-8 bytes, without control characters.'); categoryInput.current?.focus(); return;
    }
    setPending(true); setError(''); setFieldError(''); setStatus('');
    // Reuse the command ID when the outcome was uncertain, never blindly resend after a timeout.
    const previous = pendingCommand.current;
    const command: Correction = previous?.id === selected.id && previous.category === nextCategory ? previous : {
      id: selected.id, category: nextCategory, expected_revision: selected.correction_revision, command_id: crypto.randomUUID(),
    };
    pendingCommand.current = command;
    try {
      const result = await window.focuswatch.correct(command);
      const refreshed = await read({ date: report.date, zone: report.time_zone });
      if (!result.ok) {
        setError(message(result.error));
        if (result.error === 'conflict' || result.error === 'not_found' || result.error === 'invalid_request') pendingCommand.current = undefined;
      } else if (refreshed) {
        pendingCommand.current = undefined;
        const saved = refreshed.intervals.find(row => row.id === selected.id);
        if (saved?.category === nextCategory && saved.corrected) setStatus(`Saved category “${saved.category}”. Report refreshed from the agent.`);
        else setError('The correction was accepted, but the refreshed report does not confirm it. Refresh before retrying.');
      }
    } catch { setError('The correction could not be confirmed. Refresh before retrying.'); }
    finally { setPending(false); requestAnimationFrame(() => categoryInput.current?.focus()); }
  }

  const filtered = report?.intervals.filter(row => !filter || [row.id, row.app_name, row.category, row.source_id].some(value => value.toLowerCase().includes(filter.toLowerCase()))) ?? [];
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const visible = filtered.slice(Math.min(page, pageCount - 1) * PAGE_SIZE, (Math.min(page, pageCount - 1) + 1) * PAGE_SIZE);
  return <>
    <a className="skip" href="#main">Skip to report</a>
    <header><div className="brand">FocusWatch</div><span className="local">Local report · separate agent</span></header>
    <main id="main" data-report-state={report ? 'ready' : pending ? 'loading' : 'error'} aria-busy={pending}>
      <h1>Daily report</h1>
      <p className="muted">Your observations, with their sources and gaps.</p>
      <form className="query" onSubmit={load} aria-label="Report range">
        <label htmlFor="report-date">Day<input id="report-date" type="date" required value={query.date} onChange={event => setQuery({ ...query, date: event.target.value })} disabled={pending} /></label>
        <label htmlFor="report-zone">Time zone<input id="report-zone" value={query.zone} required maxLength={128} onChange={event => setQuery({ ...query, zone: event.target.value })} disabled={pending} autoComplete="off" spellCheck={false} /></label>
        <button type="submit" disabled={pending}>{pending ? 'Working…' : 'Refresh report'}</button>
      </form>
      <div className="status" id="report-status" role="status">{status || (pending ? 'Loading from the local agent…' : '')}</div>
      {error && <p className="error" id="report-error" role="alert">{error}</p>}
      {report && <>
        <p className="muted range" id="displayed-range">Displayed: {report.date} · {report.time_zone} · {new Date(report.start_ms).toISOString()} to {new Date(report.end_ms).toISOString()} (end exclusive) · snapshot {report.revision}</p>
        <div className="stats">
          <div className="stat"><span>Observed coverage</span><strong id="observed-coverage">{duration(report.observed_coverage_ms)}</strong><span>Union of observed intervals, across sources.</span></div>
          <div className="stat"><span>Unknown coverage</span><strong id="unknown-coverage">{duration(report.unknown_coverage_ms)}</strong><span>Explicit intervals marked as unknown.</span></div>
          <div className="stat"><span>No observations</span><strong id="unobserved-coverage">{duration(report.unobserved_ms)}</strong><span>No exact source interval. Not a measurement of inactivity.</span></div>
        </div>
        <Timeline report={report} />
        <section className="panel" aria-labelledby="category-title"><h2 id="category-title">Categories · source time</h2>
          <p className="muted">{duration(report.summed_source_ms)} summed across sources. Overlapping observations can contribute more than once; these totals are not time spent paying attention.</p>
          <ul className="category-totals" id="category-totals">{report.category_totals.map(row => <li key={row.category} data-category={row.category} data-duration-ms={row.duration_ms}><span>{row.category}</span><strong>{duration(row.duration_ms)}</strong></li>)}</ul>
        </section>
        <div className="layout">
          <section className="panel" aria-labelledby="interval-title"><h2 id="interval-title">Interval details</h2>
            <label htmlFor="observation-filter">Find an observation<input id="observation-filter" type="search" value={filter} onChange={event => { setFilter(event.target.value); setPage(0); }} placeholder="Application, category, source or ID" /></label>
            <div className="toolbar"><span className="muted" id="result-count">{filtered.length} intervals · page {Math.min(page + 1, pageCount)} of {pageCount}</span><div className="actions"><button disabled={page === 0} onClick={() => setPage(value => Math.max(0, value - 1))}>Previous</button><button disabled={page + 1 >= pageCount} onClick={() => setPage(value => value + 1)}>Next</button></div></div>
            <div className="table-wrap"><table><caption>Exact intervals in {report.time_zone}</caption><thead><tr><th scope="col">Time</th><th scope="col">Application / source</th><th scope="col">Category</th><th scope="col">Action</th></tr></thead><tbody>
              {visible.map(row => <tr key={row.id} data-observation-id={row.id} aria-selected={row.id === selectedId}>
                <td className="cell-time">{time(row.start_ms, report.time_zone)}<br />{time(row.end_ms, report.time_zone)}<br /><span className="muted">{duration(row.duration_ms)}</span></td>
                <td>{row.app_name}<br /><span className="muted">{row.source_kind} · {row.source_id}</span><br /><span className="badge">{row.quality}{row.open ? ' · open to last checkpoint' : ''}</span></td>
                <td>{row.category}{row.corrected && <><br /><span className="badge">Manual correction</span></>}</td>
                <td><button data-edit-id={row.id} aria-label={`Correct ${row.app_name} at ${time(row.start_ms, report.time_zone)}, ${row.id}`} disabled={pending} onClick={() => select(row)}>Correct</button></td>
              </tr>)}
              {!visible.length && <tr><td colSpan={4}>No matching exact intervals.</td></tr>}
            </tbody></table></div>
          </section>
          <section className="panel" aria-labelledby="correction-title"><h2 id="correction-title">Category correction</h2>
            {selected ? <>
              <dl id="selected-observation" data-selected-id={selected.id} data-selected-category={selected.category} data-correction-revision={selected.correction_revision}>
                <dt>Application</dt><dd>{selected.app_name}</dd><dt>Interval</dt><dd>{time(selected.start_ms, report.time_zone)}–{time(selected.end_ms, report.time_zone)} · {duration(selected.duration_ms)}</dd>
                <dt>Current category</dt><dd id="selected-category">{selected.category}{selected.corrected ? ' · manual correction' : ' · rule result'}</dd>
              </dl>
              <form className="correction-form" onSubmit={correct}>
                <label htmlFor="category">New category<input ref={categoryInput} id="category" value={category} onChange={event => setCategory(event.target.value)} autoComplete="off" spellCheck={false} maxLength={128} aria-invalid={!!fieldError} aria-describedby={fieldError ? 'category-error category-hint' : 'category-hint'} disabled={pending} /></label>
                <span id="category-hint" className="muted">A manual correction survives rule recalculation.</span>
                {fieldError && <p id="category-error" className="error">{fieldError}</p>}
                <button id="save-category" className="primary" type="submit" disabled={pending}>{pending ? 'Saving…' : 'Save category'}</button>
              </form>
              <details><summary>Source and timing details</summary><dl>
                <dt>Provenance</dt><dd>{selected.device_id}<br />{selected.source_id} · {selected.source_kind}<br />{selected.quality}</dd>
                <dt>Session / generation / sequence</dt><dd>{selected.session_id} / {selected.generation} / {selected.sequence}</dd>
                <dt>Resolution / time uncertainty</dt><dd>{selected.granularity_ms} ms / ±{selected.time_uncertainty_ms} ms</dd>
                <dt>Clock / interval state</dt><dd>{selected.clock_discontinuity ?? 'No discontinuity reported'}<br />{selected.open ? 'Open; ends at last confirmed checkpoint.' : 'Closed interval.'}</dd>
                <dt>Boot / monotonic scope</dt><dd>{selected.boot_id ?? 'Unavailable'}<br />{selected.monotonic_start_ms ?? 'Unknown'}–{selected.monotonic_end_ms ?? 'Unknown'} ms</dd>
                <dt>Observation ID</dt><dd>{selected.id}</dd><dt>Correction revision</dt><dd>{selected.correction_revision}</dd>
              </dl></details>
            </> : <p className="muted">Choose Correct on an interval. Enter opens its category field; Tab then Enter saves it.</p>}
          </section>
        </div>
        <section className="panel" aria-labelledby="source-title"><h2 id="source-title">Source coverage</h2><div className="table-wrap"><table><caption>Independent source durations</caption><thead><tr><th scope="col">Device / source</th><th scope="col">Observed</th><th scope="col">Unknown</th><th scope="col">Reported aggregates</th></tr></thead><tbody>
          {report.source_totals.map(row => <tr key={JSON.stringify([row.device_id, row.source_id, row.session_id, row.generation])}><td>{row.device_id}<br />{row.source_id} · {row.source_kind}<br /><span className="muted">{row.session_id} · generation {row.generation}</span></td><td>{duration(row.observed_duration_ms)}</td><td>{duration(row.unknown_duration_ms)}</td><td>{row.aggregate_count} · {duration(row.reported_aggregate_duration_ms)}</td></tr>)}
        </tbody></table></div></section>
        <section className="panel" aria-labelledby="aggregate-title"><h2 id="aggregate-title">Aggregates without an exact timeline</h2>
          <p className="muted">These are reported totals within a period. Their overlap with exact intervals is unknown, so they are excluded from the timeline and exact category totals.</p>
          {report.aggregates.length ? <div className="table-wrap"><table><caption>Period totals, shown without proportional splitting</caption><thead><tr><th scope="col">Application / source</th><th scope="col">Period</th><th scope="col">Reported duration</th><th scope="col">Coverage note</th></tr></thead><tbody>
            {report.aggregates.map(row => <tr key={row.id}><td>{row.app_name}<br />{row.device_id} / {row.source_id}<br />{row.category} · {row.quality}</td><td>{localDate(row.period_start_ms, report.time_zone)}–{localDate(row.period_end_ms, report.time_zone)}</td><td>{duration(row.reported_duration_ms)}</td><td>{row.fully_within_day ? 'Period lies within this day.' : 'Period extends beyond this day; total is not allocated to this day.'}</td></tr>)}
          </tbody></table></div> : <p>No period aggregates were received for this day.</p>}
        </section>
        <footer>Agent owns the local history. Closing this report leaves the agent running. Basic reports and corrections use no cloud or AI.</footer>
      </>}
    </main>
  </>;
}

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);
