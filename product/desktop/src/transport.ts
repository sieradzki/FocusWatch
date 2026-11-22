import net from 'node:net';
import path from 'node:path';

export const MAX_REQUEST_BYTES = 4096;
export const MAX_RESPONSE_BYTES = 4 * 1024 * 1024;
export const REQUEST_TIMEOUT_MS = 8000;

export class AgentError extends Error {
  constructor(readonly code: string) { super(code); }
}

export function validateEndpoint(endpoint: string, platform = process.platform): string {
  // No TCP, remote named pipes, URLs or renderer-selected endpoints.
  if (endpoint.includes('\0') || endpoint.length > 1024) throw new AgentError('invalid_endpoint');
  if (platform === 'win32') {
    if (!/^\\\\\.\\pipe\\[A-Za-z0-9._-]+$/.test(endpoint)) throw new AgentError('invalid_endpoint');
  } else if (!path.posix.isAbsolute(endpoint)) throw new AgentError('invalid_endpoint');
  return endpoint;
}

export function encodeFrame(request: unknown): Buffer {
  const body = Buffer.from(JSON.stringify(request), 'utf8');
  if (!body.length || body.length > MAX_REQUEST_BYTES) throw new AgentError('frame_too_large');
  const frame = Buffer.allocUnsafe(body.length + 4);
  frame.writeUInt32LE(body.length, 0);
  body.copy(frame, 4);
  return frame;
}

/** A single bounded request and response. The agent remains the only database owner. */
export function requestAgent(endpoint: string, request: unknown, timeoutMs = REQUEST_TIMEOUT_MS): Promise<unknown> {
  validateEndpoint(endpoint);
  const frame = encodeFrame(request);
  return new Promise((resolve, reject) => {
    const socket = net.createConnection(endpoint);
    let settled = false;
    const header = Buffer.alloc(4);
    let headerBytes = 0;
    let body: Buffer | undefined;
    let bodyBytes = 0;
    let size: number | undefined;
    const timer = setTimeout(() => finish(new AgentError('agent_timeout')), timeoutMs);
    const finish = (error?: Error, value?: unknown) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      socket.destroy();
      if (error) reject(error); else resolve(value);
    };
    socket.once('connect', () => socket.write(frame));
    socket.on('error', () => finish(new AgentError('agent_unavailable')));
    socket.on('end', () => finish(new AgentError('truncated_response')));
    socket.on('close', () => finish(new AgentError('truncated_response')));
    socket.on('data', chunk => {
      if (typeof chunk === 'string') return finish(new AgentError('invalid_response'));
      if (settled) return;
      let offset = 0;
      if (headerBytes < 4) {
        const take = Math.min(4 - headerBytes, chunk.length);
        chunk.copy(header, headerBytes, 0, take);
        headerBytes += take;
        offset += take;
        if (headerBytes < 4) return;
        size = header.readUInt32LE(0);
        if (!size || size > MAX_RESPONSE_BYTES) return finish(new AgentError('invalid_frame_length'));
        body = Buffer.allocUnsafe(size);
      }
      if (size === undefined || !body) return;
      if (bodyBytes + chunk.length - offset > size) return finish(new AgentError('unexpected_response_bytes'));
      chunk.copy(body, bodyBytes, offset);
      bodyBytes += chunk.length - offset;
      if (bodyBytes < size) return;
      let value: unknown;
      try {
        value = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(body));
      } catch { return finish(new AgentError('invalid_response')); }
      finish(undefined, value);
    });
  });
}
