import test from 'node:test';
import assert from 'node:assert/strict';
import net, { type Socket } from 'node:net';
import os from 'node:os';
import path from 'node:path';
import { mkdtemp, rm } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';
import { encodeFrame, MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES, requestAgent, validateEndpoint } from '../src/transport.ts';

async function withServer(action: (socket: Socket, body: unknown) => void, run: (endpoint: string) => Promise<void>) {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'focuswatch-transport-test-'));
  const endpoint = process.platform === 'win32' ? `\\\\.\\pipe\\focuswatch-test-${randomUUID()}` : path.join(directory, 'report.sock');
  const peers = new Set<Socket>();
  const server = net.createServer(socket => {
    peers.add(socket); socket.on('close', () => peers.delete(socket)); socket.on('error', () => {});
    let buffer = Buffer.alloc(0), handled = false;
    socket.on('data', chunk => {
      if (handled || typeof chunk === 'string') return;
      buffer = Buffer.concat([buffer, chunk]);
      if (buffer.length >= 4 && buffer.length >= buffer.readUInt32LE(0) + 4) { handled = true; action(socket, JSON.parse(buffer.subarray(4).toString('utf8'))); }
    });
  });
  try {
    await new Promise<void>((resolve, reject) => { server.once('error', reject); server.listen(endpoint, resolve); });
    await run(endpoint);
  } finally {
    for (const peer of peers) peer.destroy();
    if (server.listening) await new Promise<void>(resolve => server.close(() => resolve()));
    await rm(directory, { recursive: true, force: true });
  }
}
const reportRequest = { version: 1, role: 'report', command: 'report', date: '2026-11-17', zone: 'UTC' };
const response = { version: 1, ok: true, data: { text: 'Zażółć · λ' } };
function frame(value: unknown) { const body = Buffer.from(JSON.stringify(value)); const header = Buffer.alloc(4); header.writeUInt32LE(body.length); return Buffer.concat([header, body]); }

test('local endpoints exclude TCP, remote Windows pipes and NUL', () => {
  assert.equal(validateEndpoint('\\\\.\\pipe\\focuswatch-p0-test', 'win32'), '\\\\.\\pipe\\focuswatch-p0-test');
  for (const endpoint of ['http://localhost', '\\\\remote\\pipe\\focuswatch', '\\\\.\\pipe\\x\\nested', '']) assert.throws(() => validateEndpoint(endpoint, 'win32'));
  assert.equal(validateEndpoint('/tmp/private/report.sock', 'linux'), '/tmp/private/report.sock');
  assert.throws(() => validateEndpoint('localhost:123', 'linux'));
  assert.throws(() => validateEndpoint('/tmp/a\0b', 'linux'));
});
test('request frame has a little-endian UTF-8 length and a separate 4096-byte limit', () => {
  const encoded = encodeFrame(reportRequest);
  assert.equal(encoded.readUInt32LE(0), encoded.length - 4);
  assert.deepEqual(JSON.parse(encoded.subarray(4).toString('utf8')), reportRequest);
  assert.throws(() => encodeFrame('x'.repeat(MAX_REQUEST_BYTES)));
});
test('fragmented header/body and Unicode decode correctly over the real local transport', async () => {
  await withServer((socket, request) => {
    assert.deepEqual(request, reportRequest);
    const bytes = frame(response);
    socket.write(bytes.subarray(0, 2));
    setTimeout(() => { socket.write(bytes.subarray(2, 9)); socket.end(bytes.subarray(9)); }, 10);
  }, async endpoint => assert.deepEqual(await requestAgent(endpoint, reportRequest), response));
});
for (const [name, bytes] of [
  ['zero length', Buffer.alloc(4)],
  ['oversize declared length', (() => { const header = Buffer.alloc(4); header.writeUInt32LE(MAX_RESPONSE_BYTES + 1); return header; })()],
  ['truncated body', Buffer.from([10, 0, 0, 0, 123])],
  ['truncated header', Buffer.from([10, 0])],
  ['invalid UTF-8', Buffer.from([1, 0, 0, 0, 255])],
  ['invalid JSON', Buffer.from([1, 0, 0, 0, 123])],
  ['extra bytes', Buffer.concat([frame(response), Buffer.from([0])])],
] as const) test(`rejects ${name}`, async () => {
  await withServer(socket => socket.end(bytes), async endpoint => { await assert.rejects(requestAgent(endpoint, reportRequest)); });
});
test('stalled peer is bounded by a timeout and closed', async () => {
  await withServer(() => {}, async endpoint => { await assert.rejects(requestAgent(endpoint, reportRequest, 80), /agent_timeout/); });
});
