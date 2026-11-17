// Run dsh-pet's REAL config reader against our pack, and smoke-test the installer.
import { mkdtempSync, mkdirSync, copyFileSync, readdirSync, writeFileSync, cpSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SRC = 'C:/Users/Ronin/.dsh/profiles/desktop/node_modules/dsh-pet/src';
const BUNDLE = fileURLToPath(new URL('..', import.meta.url));

// ---------- 1. installer idempotency ----------
const home = mkdtempSync(join(tmpdir(), 'nexus-install-'));
process.env.DSH_HOME = home;
const { apply } = await import(new URL('../index.js', import.meta.url).href);
const logs = [];
const ctx = { logger: { info: (m) => logs.push(m), warn: (m) => logs.push('WARN ' + m) } };
apply(ctx);
apply(ctx); // second run must write 0 files
console.log('install logs:');
for (const l of logs) console.log('  ' + l);

const petDir = join(home, 'dsh-pet', 'pet');
console.log('installed:', readdirSync(petDir).sort().join(', '));
console.log('clips:', readdirSync(join(petDir, 'nexus-animation')).length,
            'memes:', readdirSync(join(petDir, 'nexus-memes')).length);
const marker = JSON.parse(readFileSync(join(petDir, '.dsh-nexus.json'), 'utf8'));
console.log('marker:', marker.version, marker.bundle, 'clips=' + marker.clips.length);

// ---------- 2. dsh-pet's real merge ----------
const tmp = mkdtempSync(join(tmpdir(), 'nexus-merge-'));
cpSync(SRC, join(tmp, 'src'), { recursive: true });
const read = await import('file:///' + join(tmp, 'src/host/config/read.ts').replace(/\\/g, '/'));
const shared = await import('file:///' + join(tmp, 'src/shared/config.ts').replace(/\\/g, '/'));

const userRoot = join(tmp, 'user', 'dsh-pet');
const realPetDir = join(userRoot, 'pet');
mkdirSync(realPetDir, { recursive: true });
for (const f of readdirSync(join(BUNDLE, 'pet-pack', 'config'))) {
  copyFileSync(join(BUNDLE, 'pet-pack', 'config', f), join(realPetDir, f));
}
writeFileSync(join(userRoot, 'main-config.jsonc'), JSON.stringify({
  pets: [{ id: 'main', name: 'main', size: 462, balanceEnabled: true, whisperEnabled: true,
           workStatusEnabled: true, fixedEnabled: false, display: 'none',
           position: { corner: 'top-right', marginX: 24, marginY: 100 } }]
}, null, 2));

const merged = read.readAllConfig({
  defaultFile: join(SRC, '../assets/config.jsonc'),
  userFile: join(userRoot, 'main-config.jsonc'),
  petDir: realPetDir,
});
console.log('\nmerge entries:', Object.keys(merged));
const found = read.findPetInstance(merged, 'nexus');
console.log('found:', found ? { entry: found.entry, name: found.pet.name, display: found.pet.display } : null);
console.log('idle:', JSON.stringify(found?.conf.animations?.idle));
console.log('categories:', found?.conf.animations?.categories?.map(c => c.id + '=' + c.weight));
console.log('workStatus:', JSON.stringify(found?.conf.animations?.events?.workStatus));
console.log('persona has 宿命:', String(found?.conf.whisperPrompt ?? '').includes('宿命'));
const flat = shared.flattenConfigPets(merged);
const n = flat.find(p => p.id === 'nexus');
console.log('flattened:', flat.map(p => p.id + '(' + p.assetRoot + ',extra=' + p.extra + ')'));
console.log('animations attached:', Array.isArray(n?.animations?.idle), 'memes:', Object.keys(n?.memes ?? {}).length);
console.log('workStatusTexts groups:', n?.workStatusTexts?.length);
