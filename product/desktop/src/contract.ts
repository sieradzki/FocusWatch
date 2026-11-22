import { AgentError } from './transport.ts';
import { validateQuery, type Query } from './cli.ts';

export interface ReportInterval {
  id: string; device_id: string; source_id: string; source_kind: string; app_id: string; app_name: string;
  category: string; start_ms: number; end_ms: number; duration_ms: number; quality: string;
  corrected: boolean; correction_revision: number; received_at_ms: number;
  session_id: string; generation: number; sequence: number; granularity_ms: number; time_uncertainty_ms: number;
  boot_id: string | null; monotonic_start_ms: number | null; monotonic_end_ms: number | null; clock_discontinuity: string | null;
  open: boolean;
}
export interface AggregateView {
  id: string; device_id: string; source_id: string; source_kind: string; app_id: string; app_name: string;
  category: string; period_start_ms: number; period_end_ms: number; reported_duration_ms: number;
  quality: string; corrected: boolean; correction_revision: number; fully_within_day: boolean; received_at_ms: number;
  session_id: string; generation: number; sequence: number; granularity_ms: number; time_uncertainty_ms: number;
  boot_id: string | null; monotonic_start_ms: number | null; monotonic_end_ms: number | null; clock_discontinuity: string | null;
}
export interface SourceTotal {
  device_id: string; source_id: string; source_kind: string; session_id: string; generation: number; observed_duration_ms: number;
  unknown_duration_ms: number; aggregate_count: number; reported_aggregate_duration_ms: number;
}
export interface CategoryTotal { category: string; duration_ms: number }
export interface DayReport {
  revision: number; date: string; time_zone: string; start_ms: number; end_ms: number; day_duration_ms: number;
  observed_coverage_ms: number; summed_source_ms: number; unknown_coverage_ms: number; unobserved_ms: number;
  intervals: ReportInterval[]; aggregates: AggregateView[]; source_totals: SourceTotal[]; category_totals: CategoryTotal[];
}
export interface Correction { id: string; category: string; expected_revision: number; command_id: string }
export type Result<T> = { version: 1; ok: true; data: T } | { version: 1; ok: false; error: string };
export interface ReportAPI {
  initialQuery(): Promise<Query>;
  report(query: Query): Promise<Result<DayReport>>;
  correct(correction: Correction): Promise<Result<unknown>>;
}

const ERRORS = new Set(['conflict', 'not_found', 'invalid_request', 'unsupported_version', 'invalid_role', 'report_too_large', 'storage_error']);
const SOURCE_KINDS = new Set(['foreground', 'input', 'lock', 'media', 'other']);
const QUALITIES = new Set(['observed', 'synthetic', 'unknown']);
function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new AgentError('invalid_response');
  return value as Record<string, unknown>;
}
function text(value: unknown, limit = 256): string {
  if (typeof value !== 'string' || !value.length || value.length > limit || /[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(value)) throw new AgentError('invalid_response');
  return value;
}
function integer(value: unknown, min = 0): number {
  if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < min) throw new AgentError('invalid_response');
  return value;
}
function bool(value: unknown): boolean {
  if (typeof value !== 'boolean') throw new AgentError('invalid_response');
  return value;
}
function list<T>(value: unknown, validate: (item: unknown) => T, limit = 10000): T[] {
  if (!Array.isArray(value) || value.length > limit) throw new AgentError('invalid_response');
  return value.map(validate);
}
function provenance(raw: Record<string, unknown>) {
  const source_kind = text(raw.source_kind), quality = text(raw.quality);
  if (!SOURCE_KINDS.has(source_kind) || !QUALITIES.has(quality)) throw new AgentError('invalid_response');
  return { id: text(raw.id), device_id: text(raw.device_id), source_id: text(raw.source_id), source_kind,
    app_id: text(raw.app_id, 1024), app_name: text(raw.app_name, 1024), category: text(raw.category, 128), quality,
    corrected: bool(raw.corrected), correction_revision: integer(raw.correction_revision), received_at_ms: integer(raw.received_at_ms, -8640000000000000),
    session_id: text(raw.session_id), generation: integer(raw.generation), sequence: integer(raw.sequence),
    granularity_ms: integer(raw.granularity_ms), time_uncertainty_ms: integer(raw.time_uncertainty_ms),
    boot_id: raw.boot_id == null ? null : text(raw.boot_id),
    monotonic_start_ms: raw.monotonic_start_ms == null ? null : integer(raw.monotonic_start_ms),
    monotonic_end_ms: raw.monotonic_end_ms == null ? null : integer(raw.monotonic_end_ms),
    clock_discontinuity: raw.clock_discontinuity == null ? null : text(raw.clock_discontinuity) };
}
export function validateReport(value: unknown, query?: Query): DayReport {
  const raw = object(value);
  const date = text(raw.date), time_zone = text(raw.time_zone);
  validateQuery({ date, zone: time_zone });
  if (query && (query.date !== date || query.zone !== time_zone)) throw new AgentError('mismatched_report');
  const start_ms = integer(raw.start_ms, -8640000000000000), end_ms = integer(raw.end_ms, -8640000000000000);
  const day_duration_ms = integer(raw.day_duration_ms);
  if (Math.abs(start_ms) > 8640000000000000 || Math.abs(end_ms) > 8640000000000000 || end_ms <= start_ms || end_ms - start_ms !== day_duration_ms || day_duration_ms > 48 * 3600000) throw new AgentError('invalid_response');
  const intervals = list(raw.intervals, item => {
    const row = object(item), base = provenance(row);
    const start = integer(row.start_ms, -8640000000000000), end = integer(row.end_ms, -8640000000000000), duration = integer(row.duration_ms);
    const open = bool(row.open);
    if (start < start_ms || end > end_ms || start > end || (start === end && !open) || duration !== end - start) throw new AgentError('invalid_response');
    return { ...base, start_ms: start, end_ms: end, duration_ms: duration, open };
  });
  if (new Set(intervals.map(row => row.id)).size !== intervals.length) throw new AgentError('invalid_response');
  const aggregates = list(raw.aggregates, item => {
    const row = object(item), base = provenance(row);
    const start = integer(row.period_start_ms, -8640000000000000), end = integer(row.period_end_ms, -8640000000000000), duration = integer(row.reported_duration_ms);
    if (start >= end || duration > end - start || end <= start_ms || start >= end_ms) throw new AgentError('invalid_response');
    return { ...base, period_start_ms: start, period_end_ms: end, reported_duration_ms: duration, fully_within_day: bool(row.fully_within_day) };
  });
  const source_totals = list(raw.source_totals, item => {
    const row = object(item), source_kind = text(row.source_kind);
    if (!SOURCE_KINDS.has(source_kind)) throw new AgentError('invalid_response');
    return { device_id: text(row.device_id), source_id: text(row.source_id), source_kind, session_id: text(row.session_id), generation: integer(row.generation),
      observed_duration_ms: integer(row.observed_duration_ms), unknown_duration_ms: integer(row.unknown_duration_ms),
      aggregate_count: integer(row.aggregate_count), reported_aggregate_duration_ms: integer(row.reported_aggregate_duration_ms) };
  }, 1000);
  const category_totals = list(raw.category_totals, item => {
    const row = object(item);
    return { category: text(row.category, 128), duration_ms: integer(row.duration_ms) };
  }, 1000);
  const observed_coverage_ms = integer(raw.observed_coverage_ms), unknown_coverage_ms = integer(raw.unknown_coverage_ms), unobserved_ms = integer(raw.unobserved_ms);
  if (observed_coverage_ms > day_duration_ms || unknown_coverage_ms > day_duration_ms || unobserved_ms > day_duration_ms) throw new AgentError('invalid_response');
  return { revision: integer(raw.revision), date, time_zone, start_ms, end_ms, day_duration_ms,
    observed_coverage_ms, summed_source_ms: integer(raw.summed_source_ms), unknown_coverage_ms, unobserved_ms,
    intervals, aggregates, source_totals, category_totals };
}
export function validateCorrection(value: unknown): Correction {
  const raw = object(value);
  const id = text(raw.id, 256), category = text(raw.category, 128), command_id = text(raw.command_id);
  if (new TextEncoder().encode(id).length > 256 || category !== category.trim() || /[\u0000-\u001f\u007f]/.test(category) || new TextEncoder().encode(category).length > 128 || !/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i.test(command_id)) throw new AgentError('invalid_request');
  return { id, category, command_id, expected_revision: integer(raw.expected_revision) };
}
export function validateEnvelope(value: unknown): Result<unknown> {
  const raw = object(value);
  if (raw.version !== 1 || typeof raw.ok !== 'boolean') throw new AgentError('invalid_response');
  if (!raw.ok) return { version: 1, ok: false, error: typeof raw.error === 'string' && ERRORS.has(raw.error) ? raw.error : 'agent_error' };
  if (!Object.hasOwn(raw, 'data')) throw new AgentError('invalid_response');
  return { version: 1, ok: true, data: raw.data };
}

declare global { interface Window { focuswatch: ReportAPI } }
