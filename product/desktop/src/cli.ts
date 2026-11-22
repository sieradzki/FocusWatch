import path from 'node:path';
import { AgentError, validateEndpoint } from './transport.ts';

export interface Query { date: string; zone: string }
export interface Options extends Query { endpoint: string; profile?: string; smokeOutput?: string; smokeExpectCategory?: string }

export function validateQuery(value: unknown): Query {
  if (!value || typeof value !== 'object') throw new AgentError('invalid_request');
  const { date, zone } = value as Record<string, unknown>;
  if (typeof date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(date) || !Number.isFinite(Date.parse(`${date}T00:00:00Z`)) || new Date(`${date}T00:00:00Z`).toISOString().slice(0, 10) !== date) throw new AgentError('invalid_request');
  if (typeof zone !== 'string' || !zone.length || zone.length > 100) throw new AgentError('invalid_request');
  try { new Intl.DateTimeFormat('en', { timeZone: zone }).format(); } catch { throw new AgentError('invalid_request'); }
  return { date, zone };
}

export function parseArgs(args: string[]): Options {
  const flags = new Set(['--endpoint', '--date', '--zone', '--profile', '--smoke-output', '--smoke-expect-category']);
  const values = new Map<string, string>();
  for (let i = 0; i < args.length; i += 2) {
    const flag = args[i], value = args[i + 1];
    if (!flag || !flags.has(flag) || !value || value.startsWith('--') || values.has(flag)) throw new AgentError('invalid_arguments');
    values.set(flag, value);
  }
  const endpoint = validateEndpoint(values.get('--endpoint') ?? '');
  const query = validateQuery({ date: values.get('--date') ?? '2026-11-17', zone: values.get('--zone') ?? 'UTC' });
  const profile = values.get('--profile'), smokeOutput = values.get('--smoke-output');
  for (const value of [profile, smokeOutput]) if (value && !path.isAbsolute(value)) throw new AgentError('invalid_arguments');
  const smokeExpectCategory = values.get('--smoke-expect-category');
  if (smokeExpectCategory && (!smokeOutput || smokeExpectCategory.length > 64)) throw new AgentError('invalid_arguments');
  return { endpoint, ...query, profile, smokeOutput, smokeExpectCategory };
}
