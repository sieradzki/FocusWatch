import { app, BrowserWindow, ipcMain, Menu, type IpcMainInvokeEvent } from 'electron';
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { parseArgs, validateQuery } from './cli.ts';
import { validateCorrection, validateEnvelope, validateReport, type Result } from './contract.ts';
import { AgentError, requestAgent } from './transport.ts';
import { runSmoke } from './smoke.ts';

let options: ReturnType<typeof parseArgs>;
try { options = parseArgs(process.argv.slice(app.isPackaged ? 1 : 2)); }
catch { process.stderr.write('Usage: focuswatch-report --endpoint <local pipe/socket> [--date YYYY-MM-DD --zone IANA] [--profile <absolute directory>]\n'); app.exit(2); throw new Error('invalid_arguments'); }
if (options.profile) { mkdirSync(options.profile, { recursive: true, mode: 0o700 }); app.setPath('userData', options.profile); }
else app.setPath('userData', path.join(app.getPath('appData'), 'FocusWatch', 'Report'));
app.setAppUserModelId('FocusWatch.Report');
for (const flag of ['disable-background-networking', 'disable-component-update', 'disable-domain-reliability', 'disable-breakpad']) app.commandLine.appendSwitch(flag);
app.commandLine.appendSwitch('disable-features', 'MediaRouter');
app.enableSandbox();

let window: BrowserWindow | undefined;
let inFlight = false;
let preloadSecurity: { sandboxed?: boolean; contextIsolated?: boolean } = {};
const indexUrl = pathToFileURL(path.join(__dirname, 'index.html')).href;
const allowedUrls = new Set(['index.html', 'report.js', 'report.css'].map(file => pathToFileURL(path.join(__dirname, file)).href));
function trusted(event: Pick<IpcMainInvokeEvent, 'sender' | 'senderFrame'>) {
  return window && !window.isDestroyed() && event.sender === window.webContents && event.senderFrame === event.sender.mainFrame && event.senderFrame.url === indexUrl;
}
ipcMain.on('report:preload-state', (event, value: unknown) => {
  if (trusted(event) && value && typeof value === 'object') {
    const raw = value as Record<string, unknown>;
    preloadSecurity = { sandboxed: raw.sandboxed === true, contextIsolated: raw.contextIsolated === true };
  }
});
async function call(event: IpcMainInvokeEvent, work: () => Promise<Result<unknown>>): Promise<Result<unknown>> {
  if (!trusted(event)) return { version: 1, ok: false, error: 'invalid_role' };
  if (inFlight) return { version: 1, ok: false, error: 'busy' };
  inFlight = true;
  try { return await work(); }
  catch (error) { return { version: 1, ok: false, error: error instanceof AgentError ? error.code : 'agent_error' }; }
  finally { inFlight = false; }
}
ipcMain.handle('report:initial', event => {
  if (!trusted(event)) throw new Error('invalid_role');
  return { date: options.date, zone: options.zone };
});
ipcMain.handle('report:read', (event, query: unknown) => call(event, async () => {
  const checked = validateQuery(query);
  const result = validateEnvelope(await requestAgent(options.endpoint, { version: 1, role: 'report', command: 'report', ...checked }));
  if (!result.ok) return result;
  const report = validateReport(result.data, checked);
  if (options.smokeOutput && (report.intervals.some(row => row.quality !== 'synthetic') || report.aggregates.some(row => row.quality !== 'synthetic'))) throw new AgentError('smoke_requires_synthetic_data');
  return { version: 1, ok: true, data: report };
}));
ipcMain.handle('report:correct', (event, correction: unknown) => call(event, async () => {
  const checked = validateCorrection(correction);
  return validateEnvelope(await requestAgent(options.endpoint, { version: 1, role: 'report', command: 'correct', ...checked }));
}));

app.whenReady().then(async () => {
  if (options.smokeOutput) app.setAccessibilitySupportEnabled(true);
  Menu.setApplicationMenu(null);
  window = new BrowserWindow({ title: 'FocusWatch · Daily report', width: 1180, height: 850, minWidth: 480, minHeight: 480, useContentSize: true,
    show: false, backgroundColor: '#f5f6f8', webPreferences: { preload: path.join(__dirname, 'preload.cjs'), sandbox: true, contextIsolation: true,
      nodeIntegration: false, webSecurity: true, allowRunningInsecureContent: false, devTools: false, spellcheck: false, partition: 'focuswatch-report' } });
  const contents = window.webContents;
  contents.session.webRequest.onBeforeRequest((details, callback) => callback({ cancel: !allowedUrls.has(details.url) }));
  contents.session.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  contents.session.setPermissionCheckHandler(() => false);
  contents.setWindowOpenHandler(() => ({ action: 'deny' }));
  contents.on('will-navigate', event => event.preventDefault());
  contents.on('will-frame-navigate', event => event.preventDefault());
  contents.on('will-attach-webview', event => event.preventDefault());
  contents.on('render-process-gone', () => app.exit(1));
  window.once('ready-to-show', () => { window?.show(); });
  await window.loadFile(path.join(__dirname, 'index.html'));
  if (options.smokeOutput) {
    try { await runSmoke(window, options, preloadSecurity); app.exit(0); }
    catch (error) { process.stderr.write(`Report smoke failed: ${error instanceof AgentError ? error.code : 'assertion_failed'}\n`); app.exit(1); }
  }
}).catch(() => { process.stderr.write('Report could not start.\n'); app.exit(1); });
app.on('window-all-closed', () => app.quit());
