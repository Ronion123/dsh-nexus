// The definitive test: apply() in a fresh process, click once, observe the swap.
// Uses only what a real click does; no competing pollers.
const ORIGIN = 'http://127.0.0.1:50474';
const BASE = ORIGIN + '/dsh-pet-7340';
const OWNER = 'dsh-nexus';

const post = (p, b) => fetch(BASE + p, {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b),
}).then(r => r.json().catch(() => ({})));
const get = (p) => fetch(BASE + p).then(r => r.json().catch(() => ({})));
const vis = (cfg) => {
  const o = {};
  for (const c of Object.values(cfg)) for (const p of c.pets ?? []) o[p.id] = p.display;
  return o;
};

// hard reset: no registration, no queued events, red visible
await fetch(`${BASE}/menu/item?owner=${OWNER}`, { method: 'DELETE' });
await get(`/menu/events?owner=${OWNER}&wait=0`);
await post('/pet-display', { id: 'nexus', display: 'both' });
await post('/pet-display', { id: 'nexus-blue', display: 'none' });
console.log('reset:', JSON.stringify(vis(await get('/config'))));

const { apply } = await import('file:///C:/Users/Ronin/Desktop/桌宠设计/dsh-nexus/index.js');
const cleanups = [];
apply({
  webServer: { getOrigin: () => ORIGIN },
  logger: { info: (s) => console.log(' [i]', s.slice(0, 90)), warn: (s) => console.log(' [w]', s) },
  effect: (fn) => { const c = fn(); cleanups.push(c); return c; },
  on: () => () => {},
});

// let the listener register and park
await new Promise((r) => setTimeout(r, 2500));
console.log('registered:', JSON.stringify(
  ((await get('/state')).sections?.menu?.data?.items ?? []).filter((i) => i.owner === OWNER)));

console.log('\nclick once...');
await post('/menu/click', { owner: OWNER, label: '变成蓝色青年形态' });

let ok = false;
for (let i = 0; i < 14; i++) {
  await new Promise((r) => setTimeout(r, 500));
  const v = vis(await get('/config'));
  console.log(`  t=${((i + 1) * 0.5).toFixed(1)}s nexus=${v.nexus} blue=${v['nexus-blue']}`);
  if (v.nexus === 'none' && v['nexus-blue'] === 'both') { ok = true; break; }
}

console.log('\nRESULT:', ok ? 'PASS' : 'FAIL');
for (const c of cleanups) { try { if (typeof c === 'function') c(); } catch {} }
await fetch(`${BASE}/menu/item?owner=${OWNER}`, { method: 'DELETE' });
process.exit(ok ? 0 : 1);
