// Verify menu registration with the CORRECT payload shape, then the full click path.
const ORIGIN = 'http://127.0.0.1:50474';
const BASE = ORIGIN + '/dsh-pet-7340';
const OWNER = 'dsh-nexus';
const LABEL = '变成蓝色青年形态';

async function j(path, init) {
  const res = await fetch(BASE + path, init);
  const body = await res.json().catch(() => ({}));
  return { status: res.status, body };
}

const post = (path, payload) => j(path, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json; charset=utf-8' },
  body: JSON.stringify(payload),
});

function visibility(cfg) {
  const out = {};
  for (const conf of Object.values(cfg)) for (const p of conf.pets ?? []) out[p.id] = p.display;
  return out;
}

console.log('=== 1. 注册菜单项（正确 payload） ===');
const reg = await post('/menu/item', { owner: OWNER, labels: [LABEL], target: 'both' });
console.log('  ', JSON.stringify(reg.body));
if (reg.body.ok !== true) { console.log('FAIL: registration rejected'); process.exit(1); }

console.log('\n=== 2. 确认菜单快照里能看到它 ===');
const state = await j('/state');
const items = state.body?.sections?.menu?.data?.items ?? [];
console.log('   items:', JSON.stringify(items.filter(i => i.owner === OWNER)));
if (!items.some(i => i.owner === OWNER && i.label === LABEL)) {
  console.log('FAIL: item not in menu snapshot'); process.exit(1);
}

console.log('\n=== 3. 模拟点击 ===');
const click = await post('/menu/click', { owner: OWNER, label: LABEL });
console.log('  ', JSON.stringify(click.body));

console.log('\n=== 4. 读取事件（插件轮询的同一接口） ===');
const ev = await j(`/menu/events?owner=${encodeURIComponent(OWNER)}&wait=0`);
console.log('  ', JSON.stringify(ev.body));

// reset to red and run the hand-off
const cfg = await j('/config');
let v = visibility(cfg.body);
if (v['nexus-blue'] !== 'none') {
  await post('/pet-display', { id: 'nexus', display: 'both' });
  await post('/pet-display', { id: 'nexus-blue', display: 'none' });
}
console.log('\n=== 5. 执行形态转换 ===');
const anim = await post('/anim?pet=nexus&surface=any', { name: '形态切换' });
const pb = anim.body.playbackId;
const t0 = Date.now();
const done = await j(`/playback/${encodeURIComponent(pb)}?wait=ended&timeout=10000`);
console.log('   shift status:', done.body.playback?.status, '| waited', ((Date.now() - t0) / 1000).toFixed(2) + 's');
await post('/pet-display', { id: 'nexus-blue', display: 'both' });
await post('/pet-display', { id: 'nexus', display: 'none' });

v = visibility((await j('/config')).body);
console.log('   after:', 'nexus=' + v.nexus, 'nexus-blue=' + v['nexus-blue']);
const ok = v.nexus === 'none' && v['nexus-blue'] === 'both';
console.log('\nRESULT:', ok ? 'PASS - 切换成功' : 'FAIL');

await post('/pet-display', { id: 'nexus', display: 'both' });
await post('/pet-display', { id: 'nexus-blue', display: 'none' });
console.log('(restored to red)');
process.exit(ok ? 0 : 1);
