// Existing user with a JSONC config that has comments and main:display=both.
// Verify we hide the maid, back up the original text, and never corrupt JSON.
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, readdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const home = mkdtempSync(join(tmpdir(), 'nexus-existing-'));
const root = join(home, 'dsh-pet');
mkdirSync(root, { recursive: true });

const ORIGINAL = `{
  // 用户自己写的注释，必须能找回
  "pets": [
    {
      "id": "main",
      "name": "蓝毛小女仆",
      "size": 462,
      "display": "both",   // 默认显示
      "position": { "corner": "top-right", "marginX": 24, "marginY": 100 }
    }
  ],
  /* 全局偏好 */
  "clickSoundEnabled": true,
  "notificationsEnabled": true
}
`;
writeFileSync(join(root, 'main-config.jsonc'), ORIGINAL, 'utf8');
process.env.DSH_HOME = home;

const { apply } = await import(new URL('../index.js', import.meta.url).href);
const logs = [];
apply({ logger: { info: (m) => logs.push(m), warn: (m) => logs.push('WARN ' + m) } });
console.log(logs.find((l) => l.includes('maid')) || '(no maid line)');

const cfgPath = join(root, 'main-config.jsonc');
const after = JSON.parse(readFileSync(cfgPath, 'utf8'));
console.log('\nmain after:', JSON.stringify(after.pets[0]));
console.log('global prefs preserved:', after.clickSoundEnabled, after.notificationsEnabled);

const backup = cfgPath + '.dsh-nexus-before-hide';
console.log('original backed up:', existsSync(backup));
if (existsSync(backup)) {
  console.log('backup still has comments:', readFileSync(backup, 'utf8').includes('用户自己写的注释'));
}

// Idempotent second run
const before2 = readFileSync(cfgPath, 'utf8');
apply({ logger: { info: () => {}, warn: () => {} } });
console.log('second run changed file:', readFileSync(cfgPath, 'utf8') !== before2);
