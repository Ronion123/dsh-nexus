// Simulate a brand-new user: no main-config.jsonc at all, dsh-pet defaults apply.
// Verify installPetPack + hideBundledMaid leave only Nexus visible.
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const home = mkdtempSync(join(tmpdir(), 'nexus-fresh-'));
process.env.DSH_HOME = home;
const { apply } = await import(new URL('../index.js', import.meta.url).href);

const logs = [];
apply({ logger: { info: (m) => logs.push(m), warn: (m) => logs.push('WARN ' + m) } });
for (const l of logs) console.log(l);

const cfgPath = join(home, 'dsh-pet', 'main-config.jsonc');
console.log('\n--- written user config exists:', existsSync(cfgPath));
if (existsSync(cfgPath)) {
  const parsed = JSON.parse(readFileSync(cfgPath, 'utf8'));
  console.log('pets:');
  for (const p of parsed.pets) {
    console.log('  id=%s name=%s display=%s', p.id, p.name, p.display);
  }
}

// Second run must not rewrite (idempotency).
const before = readFileSync(cfgPath, 'utf8');
logs.length = 0;
apply({ logger: { info: (m) => logs.push(m), warn: (m) => logs.push('WARN ' + m) } });
const after = readFileSync(cfgPath, 'utf8');
console.log('\nsecond run changed file:', before !== after);
console.log(logs.find((l) => l.includes('maid')) || '(no maid line)');
