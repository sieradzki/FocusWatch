import { build } from 'esbuild';
import { copyFile, mkdir, rm } from 'node:fs/promises';
await rm('dist', { recursive: true, force: true });
await mkdir('dist', { recursive: true });
await Promise.all([
  build({ entryPoints: ['src/main.ts'], outfile: 'dist/main.cjs', bundle: true, platform: 'node', target: 'node24', format: 'cjs', external: ['electron'] }),
  build({ entryPoints: ['src/preload.ts'], outfile: 'dist/preload.cjs', bundle: true, platform: 'node', target: 'node24', format: 'cjs', external: ['electron'] }),
  build({ entryPoints: ['src/renderer.tsx'], outfile: 'dist/report.js', bundle: true, platform: 'browser', target: 'chrome156', minify: true, define: { 'process.env.NODE_ENV': '"production"' }, legalComments: 'eof' }),
  copyFile('src/index.html', 'dist/index.html'),
  copyFile('src/report.css', 'dist/report.css'),
  copyFile('scripts/probe-uia.ps1', 'dist/probe-uia.ps1'),
]);
