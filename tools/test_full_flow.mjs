// Full plugin-equivalent flow: register menu -> click -> long-poll -> transform.
// Verifies the exact sequence apply() performs, against the live host.
const ORIGIN = 'http://127.0.0.1:50474';
const BASE = ORIGIN + '/dsh-pet-7340';
const OWNER = 'dsh-nexus';
const LABEL = '变成蓝色青年形态';

async function jp(path, init) {
  const res = await fetch(BASE + path, init);
  return { status: res.status, body: await res.json().catch(() => ({})) };
}
const post = (p, b) => jp(p, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json; charset=utf-8' },
  body: JSON.stringify(b),
});

function vis(cfg) {
  const o = {};
  for (const c of Object.values(cfg)) for (const p of c.pets ?? []) o[p.id] = p.display;
  return o;
}

// reset to red
let v = vis((await jp('/config')).body);
if (v['nexus-blue'] !== 'none' || v.nexus === 'none') {
  await post('/pet-display', { id: 'nexus', display: 'both' });
  await post('/pet-display', { id: 'nexus-blue', display: 'none' });
}
v = vis((await jp('/config')).body);
console.log('start  :', 'nexus=' + v.nexus, 'nexus-blue=' + v['nexus-blue']);

// 1. register (what apply does)
const reg = await post('/menu/item', { owner: OWNER, labels: [LABEL], target: 'both' });
console.log('register:', JSON.stringify(reg.body));

// 2. park a long-poll, then click (what a user does)
const parked = jp(`/menu/events?owner=${encodeURIComponent(OWNER)}&wait=10000`);
await new Promise((r) => setTimeout(r, 250));
const click = await post('/menu/click', { owner: OWNER, label: LABEL });
console.log('click   :', JSON.stringify(click.body));

const ev = await parked;
console.log('events  :', JSON.stringify(ev.body));

const clicked = ev.body?.events && Object.keys(ev.body.events).includes(LABEL);
console.log('seen    :', clicked ? 'YES' : 'NO');

// 3. transform (what the plugin does on seeing the label)
if (clicked) {
  const anim = await post('/anim?pet=nexus&surface=any', { name: '形态切换' });
  const pb = anim.body.playbackId;
  const t0 = Date.now();
  const done = await jp(`/playback/${encodeURIComponent(pb)}?wait=ended&timeout=10000`);
  const st = done.body.playback?.status ?? done.body.status;
  console.log('shift   :', st, ((Date.now() - t0) / 1000).toFixed(2) + 's');
  await post('/pet-display', { id: 'nexus-blue', display: 'both' });
  await post('/pet-display', { id: 'nexus', display: 'none' });
  v = vis((await jp('/config')).body);
  console.log('after   :', 'nexus=' + v.nexus, 'nexus-blue=' + v['nexus-blue']);
}

const ok = clicked && v.nexus === 'none' && v['nexus-blue'] === 'both';
console.log('\nRESULT:', ok ? 'PASS' : 'FAIL');

// leave red visible for normal use
await post('/pet-display', { id: 'nexus', display: 'both' });
await post('/pet-display', { id: 'nexus-blue', display: 'none' });
await jp(`/menu/item?owner=${encodeURIComponent(OWNER)}`, { method: 'DELETE' });
console.log('(restored to red, menu entry cleared)');
process.exit(ok ? 0 : 1);
