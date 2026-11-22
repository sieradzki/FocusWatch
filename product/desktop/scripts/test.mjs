import { build } from 'esbuild';
import { readdir, mkdir } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
await mkdir('.test-build', { recursive: true });
const entries = (await readdir('test')).filter(name => name.endsWith('.test.ts'));
await build({ entryPoints: entries.map(name => `test/${name}`), outdir: '.test-build', bundle: true, platform: 'node', target: 'node24', format: 'cjs', outExtension: { '.js': '.cjs' } });
const result = spawnSync(process.execPath, ['--test', ...entries.map(name => `.test-build/${name.replace(/\.ts$/, '.cjs')}`)], { stdio: 'inherit' });
process.exitCode = result.status ?? 1;
