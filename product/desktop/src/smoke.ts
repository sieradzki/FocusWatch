import type { BrowserWindow } from 'electron';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import type { Options } from './cli.ts';

async function until(window: BrowserWindow, expression: string, description: string): Promise<unknown> {
  const end = Date.now() + 15000;
  while (Date.now() < end) {
    if (window.isDestroyed()) throw new Error('window_closed');
    const result: unknown = await window.webContents.executeJavaScript(expression);
    if (result) return result;
    await new Promise(resolve => setTimeout(resolve, 50));
  }
  throw new Error(`Timeout: ${description}`);
}
function key(window: BrowserWindow, keyCode: string, modifiers?: Array<'control' | 'meta' | 'shift'>) {
  window.webContents.sendInputEvent({ type: 'keyDown', keyCode, modifiers });
  window.webContents.sendInputEvent({ type: 'keyUp', keyCode, modifiers });
}
export async function runSmoke(window: BrowserWindow, options: Options, security: { sandboxed?: boolean; contextIsolated?: boolean }) {
  const output = options.smokeOutput!;
  await mkdir(output, { recursive: true, mode: 0o700 });
  const id = 'synthetic-555';
  const evidence: Record<string, unknown> = { status: 'running', date: options.date, zone: options.zone, observation_id: id,
    method: 'Real Electron window, renderer text readback, webContents input events scoped to this window; own capturePage surface only. No physical keyboard or screen-reader claim.', versions: process.versions };
  try {
    await until(window, `document.querySelector('main')?.dataset.reportState === 'ready' && document.querySelector('main')?.getAttribute('aria-busy') === 'false'`, 'report loaded');
    assert.equal(security.sandboxed, true); assert.equal(security.contextIsolated, true);
    const globals: unknown = await window.webContents.executeJavaScript(`({node: typeof window.require, process: typeof window.process, api: Object.keys(window.focuswatch).sort()})`);
    assert.deepEqual(globals, { node: 'undefined', process: 'undefined', api: ['correct', 'initialQuery', 'report'] });
    window.show(); window.focus(); window.webContents.focus();
    await window.webContents.executeJavaScript(`document.querySelector('#observation-filter').focus()`);
    await window.webContents.insertText(id);
    await until(window, `!!document.querySelector('[data-edit-id="${id}"]')`, 'synthetic interval present');
    await window.webContents.executeJavaScript(`document.querySelector('[data-edit-id="${id}"]').focus()`);
    key(window, 'Enter');
    await until(window, `document.activeElement?.id === 'category'`, 'keyboard selection focuses category input');
    const read = `({id: document.querySelector('#selected-observation')?.dataset.selectedId, category: document.querySelector('#selected-observation')?.dataset.selectedCategory, revision: Number(document.querySelector('#selected-observation')?.dataset.correctionRevision), selected_text: document.querySelector('#selected-category')?.textContent, coverage_text: document.querySelector('#observed-coverage')?.textContent, range_text: document.querySelector('#displayed-range')?.textContent, totals: [...document.querySelectorAll('#category-totals [data-category]')].map(x => ({category:x.dataset.category, duration_ms:Number(x.dataset.durationMs)})), status: document.querySelector('#report-status')?.textContent, error: document.querySelector('#report-error')?.textContent ?? ''})`;
    const before = await window.webContents.executeJavaScript(read);
    evidence.before = before;
    assert.equal(before.id, id);
    assert.equal(before.error, '');
    if (process.platform === 'win32') {
      const handle = window.getNativeWindowHandle().readBigUInt64LE(0).toString();
      await promisify(execFile)('powershell.exe', ['-NoProfile', '-NonInteractive', '-File', path.join(__dirname, 'probe-uia.ps1'), '-Handle', handle, '-ExpectedProcessId', String(process.pid), '-OutputFile', path.join(output, 'uia.json')], { timeout: 20000, windowsHide: true, maxBuffer: 65536 });
      evidence.windows_uia = 'pass; see uia.json';
    } else evidence.windows_uia = 'not_run: requires Windows; native Linux accessibility is separate';
    await writeFile(path.join(output, 'before.png'), (await window.webContents.capturePage()).toPNG());
    if (options.smokeExpectCategory) {
      assert.equal(before.category, options.smokeExpectCategory);
      assert.ok(before.revision >= 1);
      assert.match(before.selected_text, /manual correction/);
      evidence.mode = 'restart-readback';
    } else {
      assert.equal(before.category, 'unclassified');
      key(window, 'A', [process.platform === 'darwin' ? 'meta' : 'control']);
      await window.webContents.insertText('learning');
      key(window, 'Tab');
      await until(window, `document.activeElement?.id === 'save-category'`, 'tab reaches Save category');
      key(window, 'Enter');
      await until(window, `document.querySelector('#selected-observation')?.dataset.selectedCategory === 'learning' && document.querySelector('main')?.getAttribute('aria-busy') === 'false' && document.querySelector('#report-status')?.textContent.startsWith('Saved category')`, 'durable correction reloaded');
      const after = await window.webContents.executeJavaScript(read);
      evidence.after = after;
      assert.equal(after.category, 'learning'); assert.equal(after.error, '');
      assert.equal(after.revision, before.revision + 1);
      assert.match(after.selected_text, /manual correction/);
      const total = (value: typeof before, category: string): number => value.totals.find((row: { category: string }) => row.category === category)?.duration_ms ?? 0;
      assert.equal(total(after, 'learning') - total(before, 'learning'), 60000);
      assert.equal(total(before, 'unclassified') - total(after, 'unclassified'), 60000);
      assert.equal(after.coverage_text, before.coverage_text);
      evidence.mode = 'keyboard-correction';
    }
    await writeFile(path.join(output, 'after.png'), (await window.webContents.capturePage()).toPNG());
    evidence.window = { visible: window.isVisible(), client_size: window.getContentSize(), sandbox: security.sandboxed, context_isolation: security.contextIsolated, renderer_node_globals: false };
    evidence.status = 'pass';
  } catch (error) {
    evidence.status = 'fail'; evidence.failure = error instanceof Error ? error.message : 'unknown_failure';
    throw error;
  } finally { await writeFile(path.join(output, 'smoke.json'), JSON.stringify(evidence, null, 2)); }
}
