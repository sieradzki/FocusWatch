import test from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { parseArgs, validateQuery } from '../src/cli.ts';
import { validateCorrection, validateEnvelope, validateReport, type DayReport } from '../src/contract.ts';
const start = Date.parse('2026-11-17T00:00:00Z');
const endpoint = process.platform === 'win32' ? '\\\\.\\pipe\\focuswatch-contract-test' : '/tmp/private/report.sock';
const provenance = { id: 'synthetic-555', device_id: 'device-pc', source_id: 'source-foreground', source_kind: 'foreground',
  app_id: 'synthetic:browser', app_name: 'browser', category: 'unclassified', quality: 'synthetic', corrected: false, correction_revision: 0, received_at_ms: start + 33300000,
  session_id: 'session-fixture', generation: 1, sequence: 555, granularity_ms: 60000, time_uncertainty_ms: 0, boot_id: 'boot-fixture',
  monotonic_start_ms: 33240000, monotonic_end_ms: 33300000, clock_discontinuity: null };
function fixture(): DayReport {
  return { revision: 1, date: '2026-11-17', time_zone: 'UTC', start_ms: start, end_ms: start + 86400000, day_duration_ms: 86400000,
    observed_coverage_ms: 60000, unknown_coverage_ms: 0, unobserved_ms: 86340000, summed_source_ms: 60000,
    intervals: [{ ...provenance, start_ms: start + 33240000, end_ms: start + 33300000, duration_ms: 60000, open: false }],
    aggregates: [{ ...provenance, id: 'phone-day', source_kind: 'other', device_id: 'phone', source_id: 'phone-summary', period_start_ms: start - 86400000,
      period_end_ms: start + 86400000, reported_duration_ms: 1200000, fully_within_day: false }],
    source_totals: [{ device_id: provenance.device_id, source_id: provenance.source_id, source_kind: 'foreground', session_id: provenance.session_id, generation: 1,
      observed_duration_ms: 60000, unknown_duration_ms: 0, aggregate_count: 0, reported_aggregate_duration_ms: 0 }],
    category_totals: [{ category: 'unclassified', duration_ms: 60000 }] };
}
test('CLI defaults to the synthetic seed day; validates calendar dates, zone and explicit local endpoint', () => {
  assert.deepEqual(parseArgs(['--endpoint', endpoint]), { endpoint, date: '2026-11-17', zone: 'UTC', profile: undefined, smokeOutput: undefined, smokeExpectCategory: undefined });
  assert.throws(() => parseArgs(['--endpoint', endpoint, '--endpoint', endpoint]));
  assert.throws(() => validateQuery({ date: '2026-02-31', zone: 'UTC' }));
  assert.throws(() => validateQuery({ date: '2026-11-17', zone: 'not/a/zone' }));
  assert.throws(() => parseArgs(['--endpoint', endpoint, '--profile', 'relative']));
});
test('report validates independent interval and aggregate shapes without placing the aggregate on the timeline', () => {
  const report = fixture();
  assert.deepEqual(validateReport(report, { date: report.date, zone: report.time_zone }), report);
  assert.equal(report.observed_coverage_ms, 60000);
  assert.equal(report.aggregates[0]?.reported_duration_ms, 1200000);
  assert.equal(report.aggregates[0]?.fully_within_day, false);
});
test('report rejects duplicate IDs, stale range, invalid intervals, unsafe revisions and a mismatched requested zone', () => {
  const report = fixture();
  assert.throws(() => validateReport({ ...report, intervals: [report.intervals[0], report.intervals[0]] }));
  assert.throws(() => validateReport({ ...report, end_ms: start }));
  assert.throws(() => validateReport({ ...report, revision: Number.MAX_SAFE_INTEGER + 1 }));
  assert.throws(() => validateReport({ ...report, start_ms: 8700000000000000, end_ms: 8700000086400000 }));
  assert.throws(() => validateReport({ ...report, observed_coverage_ms: 86400001 }));
  assert.throws(() => validateReport(report, { date: report.date, zone: 'Europe/Warsaw' }));
  assert.throws(() => validateReport({ ...report, intervals: [{ ...report.intervals[0], duration_ms: -1 }] }));
});
test('open checkpoint point is valid without fabricating a duration', () => {
  const report = fixture(), row = report.intervals[0]!;
  const changed = { ...report, intervals: [{ ...row, start_ms: row.end_ms, duration_ms: 0, open: true }] };
  assert.equal(validateReport(changed).intervals[0]?.duration_ms, 0);
  assert.throws(() => validateReport({ ...changed, intervals: [{ ...changed.intervals[0], open: false }] }));
});
test('correction validates the separate per-observation revision, stable command ID and Unicode category', () => {
  const correction = { id: 'synthetic-555', category: 'nauka · 日本語', expected_revision: 0, command_id: randomUUID() };
  assert.deepEqual(validateCorrection(correction), correction);
  assert.equal(validateCorrection({ ...correction, id: 'o'.repeat(256) }).id.length, 256);
  assert.throws(() => validateCorrection({ ...correction, id: 'o'.repeat(257) }));
  assert.throws(() => validateCorrection({ ...correction, id: '界'.repeat(86) }));
  for (const change of [{ expected_revision: -1 }, { category: '\u0000' }, { category: '界'.repeat(50) }, { command_id: 'not-a-uuid' }]) assert.throws(() => validateCorrection({ ...correction, ...change }));
});
test('envelope rejects incompatible versions and does not forward arbitrary backend error text', () => {
  assert.deepEqual(validateEnvelope({ version: 1, ok: false, error: 'conflict' }), { version: 1, ok: false, error: 'conflict' });
  assert.deepEqual(validateEnvelope({ version: 1, ok: false, error: 'private_path_or_data' }), { version: 1, ok: false, error: 'agent_error' });
  for (const raw of [{ version: 2, ok: true, data: {} }, { version: 1, ok: true }, { version: 1, ok: 'yes', data: {} }]) assert.throws(() => validateEnvelope(raw));
});
