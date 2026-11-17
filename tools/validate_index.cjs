const path = require('node:path');
const fs = require('node:fs');
const m = require('C:/Ronin/software/DeepSeek Harness/resources/app.asar/dsh/node_modules/@deepseek-ai/dsh-plugin-market-index/lib/index.js');
const raw = JSON.parse(fs.readFileSync('C:/Users/Ronin/Desktop/桌宠设计/dsh-nexus/site/index.json', 'utf8'));
const out = m.parseMarketIndex(raw, 'https://example.github.io/dsh-nexus/index.json');
console.log('VALID - plugins:', out.plugins.length);
for (const p of out.plugins) {
  console.log('  name:', p.name);
  console.log('  title:', JSON.stringify(p.title));
  console.log('  icon:', p.icon);
  console.log('  repository:', JSON.stringify(p.repository));
  console.log('  category:', p.metadata.category, '| labels:', p.metadata.labels.join(','));
  console.log('  keywords:', p.metadata.keywords.length);
  console.log('  versions:');
  for (const v of p.versions) {
    console.log('    ', v.version, '| ts', v.publishTimestamp, '| source', JSON.stringify(v.source), '| engines', JSON.stringify(v.engines));
    const target = m.marketInstallTarget(p.name, v);
    console.log('      install spec:', target.spec, '| registry:', target.registry ?? '(default)');
  }
}
console.log('index title:', JSON.stringify(out.title));
console.log('categories:', Object.keys(out.metadata.categories).join(','));
console.log('labels:', Object.keys(out.metadata.labels).join(','));
