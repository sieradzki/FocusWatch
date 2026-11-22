import { contextBridge, ipcRenderer } from 'electron';
import type { Correction } from './contract.ts';
import type { Query } from './cli.ts';

ipcRenderer.send('report:preload-state', { sandboxed: process.sandboxed, contextIsolated: process.contextIsolated });
// No ipcRenderer, endpoints, filesystem, generic message or shell API reaches the renderer.
contextBridge.exposeInMainWorld('focuswatch', Object.freeze({
  initialQuery: () => ipcRenderer.invoke('report:initial'),
  report: (query: Query) => ipcRenderer.invoke('report:read', query),
  correct: (correction: Correction) => ipcRenderer.invoke('report:correct', correction),
}));
