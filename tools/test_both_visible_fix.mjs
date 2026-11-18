// Verify the fix end to end: create the "both visible" bug state, then let the
// plugin's menu path repair it.
const ORIGIN = 'http://127.0.0.1:63047';
const BASE = ORIGIN + '/dsh-pet-7340';
const OWNER = 'dsh-nexus';
const LABEL = '变成蓝色青年形态';

const post = (p, b) => fetch(BASE + p, {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b),
}).then(r => r.json().catch(() => ({})));
const get = (p) => fetch(BASE + p).then(r => r.json().catch(() => ({})));
const vis = (cfg) => {
  const o = {};
  for (const c of Object.values(cfg)) for (const p of c.pets ?? []) o[p.id] = p.display;
  return o;
};
const only = (v) => Object.fromEntries(Object.entries(v).filter(([k]) => k.includes('nexus')));

// 1. manufacture the bug: both forms on the desktop
await fetch(`${BASE}/menu/item?owner=${OWNER}`, { method: 'DELETE' });
await get(`/menu/events?owner=${OWNER}&wait=0`);
await post('/pet-display', { id: 'nexus', display: 'desktop' });
await post('/pet-display', { id: 'nexus-blue', display: 'desktop' });
await new Promise(r => setTimeout(r, 600));
console.log('1. bug state   :', JSON.stringify(only(vis(await get('/config')))));

// 2. run the plugin's apply() in this process so its menu listener is live
const { apply } = await import('file:///C:/Users/Ronin/Desktop/桌宠设计/dsh-nexus/index.js');
const cleanups = [];
const warns = [];
apply({
  webServer: { getOrigin: () => ORIGIN },
  logger: { info: () => {}, warn: (s) => warns.push(s) },
  effect: (fn) => { const c = fn(); cleanups.push(c); return c; },
  on: () => () => {},
});
await new Promise(r => setTimeout(r, 2500));

const items = ((await get('/state')).sections?.menu?.data?.items ?? []).filter(i => i.owner === OWNER);
console.log('2. menu        :', JSON.stringify(items));

// 3. click once
console.log('3. clicking...');
await post('/menu/click', { owner: OWNER, label: LABEL });

let fixed = null;
for (let i = 0; i < 16; i++) {
  await new Promise(r => setTimeout(r, 400));
  const v = only(vis(await get('/config')));
  if (v.nexus === 'none' && v['nexus-blue'] !== 'none') {
    fixed = v;
    console.log(`4. repaired @ ${((i + 1) * 0.4).toFixed(1)}s :`, JSON.stringify(v));
    break;
  }
}

if (!fixed) {
  console.log('4. after       :', JSON.stringify(only(vis(await get('/config')))));
  console.log('   warnings    :', warns);
}
console.log('\nRESULT:', fixed ? 'PASS - 红色已关闭，只剩蓝色' : 'FAIL');

for (const c of cleanups) { try { if (typeof c === 'function') c(); } catch {} }
await fetch(`${BASE}/menu/item?owner=${OWNER}`, { method: 'DELETE' });
process.exit(fixed ? 0 : 1);
