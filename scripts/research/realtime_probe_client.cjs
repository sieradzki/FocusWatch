// Separate synthetic clients: their memory/CPU is excluded from server metrics.
// Node 22 built-in WebSocket. One monotonic clock timestamps send/peer receipt.
const [port, countText, secondsText] = process.argv.slice(2);
const count = Number(countText), seconds = Number(secondsText);
const sockets = [], sequences = Array(count).fill(0), pending = new Map();
const latencies = {initial: [], steady: [], burst: []};
let failures = [], received = 0;
const payload = 'synthetic-editor+background-media:' + 'x'.repeat(256);
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const emit = value => process.stdout.write(JSON.stringify(value) + '\n');
function message(index, data) {
  try {
    const value = JSON.parse(data), publisher = value.account * 2 + value.device;
    if (publisher !== (index ^ 1) || value.payload !== payload) throw Error('wrong recipient or payload');
    const key = `${publisher}:${value.seq}`, expected = pending.get(key);
    if (!expected || expected.stamp !== value.stamp_ns) throw Error('unexpected/duplicate/stale delivery');
    pending.delete(key); received++;
    latencies[expected.phase].push(Number(process.hrtime.bigint() - BigInt(value.stamp_ns)) / 1e6);
  } catch (e) { failures.push(String(e)); }
}
function send(index, phase) {
  const stamp = process.hrtime.bigint().toString(), seq = ++sequences[index];
  pending.set(`${index}:${seq}`, {stamp, phase});
  sockets[index].send(JSON.stringify({account: index >> 1, device: index & 1, seq, stamp_ns: stamp, payload}));
}
async function drain() {
  const until = Date.now() + 5000;
  while (pending.size && Date.now() < until) await sleep(5);
  if (pending.size) throw Error(`${pending.size} undelivered messages`);
  if (failures.length) throw Error(failures.join(';'));
}
function distribution(values) {
  values.sort((a,b) => a-b);
  const at = p => values[Math.min(values.length-1, Math.ceil(values.length*p)-1)];
  return {count: values.length, p50_ms: at(.5), p95_ms: at(.95), p99_ms: at(.99), max_ms: at(1)};
}
(async () => {
  emit({phase: 'connecting'});
  for (let start=0; start<count; start+=50) {
    await Promise.all(Array.from({length: Math.min(50,count-start)}, (_,offset) => new Promise((resolve,reject) => {
      const index = start+offset, ws = new WebSocket(`ws://127.0.0.1:${port}/ws/${index>>1}/${index&1}`);
      sockets[index] = ws;
      ws.addEventListener('open', resolve, {once:true});
      ws.addEventListener('error', () => reject(Error('websocket error')), {once:true});
      ws.addEventListener('message', event => message(index,event.data));
    })));
  }
  // HTTP upgrade can reach the client before the server's callback registers its peer.
  for (let attempt=0; ; attempt++) {
    const state=await (await fetch(`http://127.0.0.1:${port}/metrics`)).json();
    if (state.connections===count) break;
    if (attempt>100) throw Error('not all server peers registered');
    await sleep(20);
  }
  for (let i=0; i<count; i++) send(i,'initial');
  await drain();
  emit({phase:'idle', connections:count}); await sleep(5000);
  emit({phase:'steady'});
  // Staggered 30-second period, observed for `seconds` (<30); not an accelerated rate.
  const scheduled=[];
  for (let i=0; i<count; i++) {
    const delay = i * 30000/count;
    if (delay < seconds*1000) scheduled.push(sleep(delay).then(() => send(i,'steady')));
  }
  await sleep(seconds*1000); await Promise.all(scheduled); await drain();
  emit({phase:'burst'});
  // 100 distinct publishers at once, only one peer per publisher (no global fanout).
  for (let i=0; i<Math.min(100,count); i++) send(i,'burst');
  await drain();
  // Duplicate and older sequence must not create extra deliveries.
  const duplicate={account:0,device:0,seq:sequences[0],stamp_ns:'rejected',payload};
  sockets[0].send(JSON.stringify(duplicate));
  sockets[0].send(JSON.stringify({...duplicate,seq:sequences[0]-1}));
  await sleep(500); await drain();
  emit({phase:'done', result:{connections:count, received, failures,
    latency:Object.fromEntries(Object.entries(latencies).map(([k,v])=>[k,distribution(v)]))}});
  for (const ws of sockets) ws.close();
})().catch(error => { emit({phase:'error',error:String(error)}); process.exitCode=1; for(const ws of sockets) ws?.close(); });
