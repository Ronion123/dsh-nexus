// Validate the LIVE raw.githubusercontent index with DSH's own parser.
const fs = require('node:fs');
const m = require('C:/Ronin/software/DeepSeek Harness/resources/app.asar/dsh/node_modules/@deepseek-ai/dsh-plugin-market-index/lib/index.js');

const INDEX_URL = 'https://raw.githubusercontent.com/Ronion123/dsh-nexus/v1.0.0/site/index.json';
const raw = JSON.parse(fs.readFileSync('C:/Users/Ronin/Desktop/桌宠设计/_live2.json', 'utf8'));
const out = m.parseMarketIndex(raw, INDEX_URL);

console.log('LIVE RAW INDEX VALID');
for (const p of out.plugins) {
  console.log('  name :', p.name);
  console.log('  icon :', p.icon);
  console.log('  repo :', p.repository && p.repository.url);
  for (const v of p.versions) {
    const t = m.marketInstallTarget(p.name, v);
    console.log('  ver  :', v.version, '| ts', v.publishTimestamp, '| engines', JSON.stringify(v.engines));
    console.log('  inst :', t.spec);
  }
}
