// Investigate why the shift clip reports cancelled at the 10s cap.
// A cue that never starts (no visible pet rendering it) stays in accepted.
const BASE = 'http://127.0.0.1:50474/dsh-pet-7340';

async function jp(path, init) {
  const res = await fetch(BASE + path, init);
  return { status: res.status, body: await res.json().catch(() => ({})) };
}
const post = (p, b) => jp(p, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json; charset=utf-8' },
  body: JSON.stringify(b),
});

// ensure red is the visible one, so something renders the cue
await post('/pet-display', { id: 'nexus', display: 'both' });
await post('/pet-display', { id: 'nexus-blue', display: 'none' });
console.log('visible: nexus = both');

console.log('\n-- play 形态切换 and poll its status --');
const anim = await post('/anim?pet=nexus&surface=any', { name: '形态切换' });
console.log('  anim:', JSON.stringify(anim.body));
const pb = anim.body.playbackId;

for (let i = 0; i < 8; i++) {
  await new Promise((r) => setTimeout(r, 400));
  const q = await jp(`/playback/${encodeURIComponent(pb)}`);
  console.log('  t=%.1fs status=%s', (i + 1) * 0.4, q.body.status);
  if (q.body.status === 'ended') break;
}

console.log('\n-- with wait=ended&timeout=10000 --');
const anim2 = await post('/anim?pet=nexus&surface=any', { name: '形态切换' });
const pb2 = anim2.body.playbackId;
const t0 = Date.now();
const done = await jp(`/playback/${encodeURIComponent(pb2)}?wait=ended&timeout=10000`);
console.log('  result:', JSON.stringify(done.body));
console.log('  elapsed: %.2fs', (Date.now() - t0) / 1000);
