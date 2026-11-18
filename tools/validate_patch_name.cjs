// Verify the bundle's patch `name` resolves from a profile root, the way the
// loader imports it. This is the exact failure reported on the other device.
const { readFileSync } = require('node:fs');
const { join } = require('node:path');

const BUNDLE = 'C:/Users/Ronin/Desktop/桌宠设计/dsh-nexus';
const patch = readFileSync(join(BUNDLE, 'cordis.patch.yml'), 'utf8');
console.log('--- cordis.patch.yml ---');
console.log(patch.trim());

const m = patch.match(/name:\s*'([^']+)'/);
if (!m) {
  console.log('\nFAIL: no name field');
  process.exit(1);
}
const name = m[1];
console.log('\nname in patch:', name);
console.log('package name :', JSON.parse(readFileSync(join(BUNDLE, 'package.json'), 'utf8')).name);
console.log('match:', name === JSON.parse(readFileSync(join(BUNDLE, 'package.json'), 'utf8')).name);

// Would this name resolve from the profile root?
const { createRequire } = require('node:module');
const requireFromProfile = createRequire(
  'C:/Users/Ronin/.dsh/profiles/desktop/package.json'
);
try {
  const resolved = requireFromProfile.resolve(name);
  console.log('resolves from profile root: YES ->', resolved);
} catch (e) {
  console.log('resolves from profile root: NO ->', e.code);
}
