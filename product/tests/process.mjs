// Independent consumer of the versioned wire protocol and the packaged agent.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {mkdtemp, readFile, rm} from 'node:fs/promises';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import {setTimeout as sleep} from 'node:timers/promises';

const [binary, gui] = process.argv.slice(2);
if (!binary) throw Error('usage: node tests/process.mjs <agent executable> [packaged report executable]');
const work = await mkdtemp(path.join(os.tmpdir(), 'focuswatch-p0-test-'));
const state = path.join(work,'state');
const endpoint = process.platform === 'win32' ? '\\\\.\\pipe\\focuswatch-p0-'+randomUUID() : path.join(state,'report.sock');
const children = new Set();
function start(file,args) {
  const proc = spawn(file,args,{stdio:['ignore','pipe','pipe'],windowsHide:true});
  const exit = once(proc,'exit');
  children.add(proc);
  proc.once('exit',() => children.delete(proc));
  proc.stderr.on('data',chunk=>process.stderr.write(chunk));
  return {proc,exit};
}
async function agent() {
  const {proc,exit} = start(binary,['--state',state,'--endpoint',endpoint]);
  await Promise.race([
    (async()=>{ for await(const chunk of proc.stdout) { if(chunk.toString().includes('READY')) return; } throw Error('agent did not become ready'); })(),
    exit.then(([code])=>{throw Error('agent exited before READY: '+code);}),
    sleep(30000,undefined,{ref:false}).then(()=>{throw Error('agent start timeout');}),
  ]);
  return async () => { proc.kill(); await exit; };
}
async function request(cmd) {
  const client = net.createConnection(endpoint);
  client.setTimeout(10000,()=>client.destroy(Error('response timeout')));
  try {
    await once(client,'connect');
    const bytes = Buffer.from(JSON.stringify({version:1,role:'report',...cmd}));
    const prefix=Buffer.alloc(4);
    prefix.writeUInt32LE(bytes.length);
    client.write(Buffer.concat([prefix,bytes]));
    const chunks=[];
    let size=0;
    for await(const chunk of client) {
      chunks.push(chunk); size+=chunk.length;
      assert.ok(size<=4*1024*1024+4);
    }
    const data=Buffer.concat(chunks);
    assert.equal(data.readUInt32LE(),data.length-4);
    const response=JSON.parse(data.subarray(4));
    assert.equal(response.version,1);
    return response;
  } finally { client.destroy(); }
}
const report = () => request({command:'report',date:'2026-11-17',zone:'UTC'});
const cmd = {command:'correct',id:'synthetic-555',category:'learning',expected_revision:0,command_id:randomUUID()};
async function guiRun(extra) {
  const profile=await mkdtemp(path.join(work,'profile-'));
  const output=path.join(work,'smoke-'+randomUUID());
  const {proc,exit}=start(gui,['--endpoint',endpoint,'--date','2026-11-17','--zone','UTC','--profile',profile,'--smoke-output',output,...extra]);
  proc.stdout.on('data',chunk=>process.stdout.write(chunk));
  const [code]=await Promise.race([exit,sleep(90000,undefined,{ref:false}).then(()=>{throw Error('GUI timeout');})]);
  const evidence = await readFile(path.join(output,'smoke.json'),'utf8').then(JSON.parse).catch(()=>null);
  console.log('Synthetic GUI check:', JSON.stringify({status:evidence?.status,mode:evidence?.mode,failure:evidence?.failure}));
  assert.equal(code,0,'GUI smoke failed');
  assert.equal(evidence?.status,'pass');
}
try {
  let stop=await agent();
  const twin=start(binary,['--state',state,'--endpoint',endpoint]);
  assert.notEqual((await twin.exit)[0],0,'duplicate state writer accepted');
  assert.equal((await request({version:2,command:'report'})).error,'unsupported_version');
  assert.equal((await request({role:'watcher',command:'report'})).error,'invalid_role');
  const initial = await report();
  assert.equal(initial.ok,true);
  assert.equal(initial.data.intervals.length,1440);
  const minutes = (r,category)=>r.data.category_totals.find(x=>x.category===category).duration_ms/60000;
  assert.equal(minutes(initial,'learning'),552);
  if (gui) {
    await guiRun([]);
  } else {
    assert.equal((await request(cmd)).ok,true);
    const retry=await request(cmd);
    assert.equal(retry.ok,true);
    assert.equal(retry.data.replayed,true);
  }
  assert.equal((await request({...cmd,category:'different',command_id:randomUUID()})).error,'conflict');
  const before=await report();
  assert.equal(minutes(before,'learning'),553);
  assert.equal(minutes(before,'unclassified'),383);
  assert.equal(before.data.intervals.find(x=>x.id==='synthetic-555').category,'learning');
  await stop(); stop=await agent();
  assert.deepEqual(await report(),before,'report changed across agent restart');
  if (gui) await guiRun(['--smoke-expect-category','learning']);
  await stop();
  console.log('PASS – local IPC, one writer, revision conflict, SQLite restart'+(gui?', native report correction and reopen':' and idempotent retry'));
} finally {
  for (const proc of children) { const exit=once(proc,'exit'); proc.kill(); await exit; }
  await rm(work,{recursive:true,force:true,maxRetries:4,retryDelay:250});
}
