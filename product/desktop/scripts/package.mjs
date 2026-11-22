// Electron's manual app-directory distribution. Only the current host platform is staged.
import { cp, mkdir, readFile, rename, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const output = process.argv[2];
if (!output || !path.isAbsolute(output) || !['win32', 'linux'].includes(process.platform)) throw new Error('Usage: npm run package -- <new absolute output directory>, on Windows or Linux.');
try { await stat(output); throw new Error('Output already exists; choose a new directory.'); }
catch (error) { if (error.code !== 'ENOENT') throw error; }
await stat('dist/main.cjs');
const runtime = path.dirname(require('electron'));
await mkdir(output, { recursive: true, mode: 0o700 });
await cp(runtime, output, { recursive: true, errorOnExist: true });
const executable = process.platform === 'win32' ? 'FocusWatchReport.exe' : 'focuswatch-report';
await rename(path.join(output, process.platform === 'win32' ? 'electron.exe' : 'electron'), path.join(output, executable));
const app = path.join(output, 'resources', 'app');
await mkdir(app, { recursive: true });
await cp('dist', path.join(app, 'dist'), { recursive: true });
const source = JSON.parse(await readFile('package.json', 'utf8'));
await writeFile(path.join(app, 'package.json'), JSON.stringify({ name: source.name, productName: 'FocusWatch Report', version: source.version, main: 'dist/main.cjs' }, null, 2));
await writeFile(path.join(output, 'focuswatch-package.json'), JSON.stringify({ version: source.version, electron: source.devDependencies.electron, platform: process.platform, architecture: process.arch, executable, signing: 'not signed by this script; P0 local validation only' }, null, 2));
process.stdout.write(`Staged ${executable}\n`);
