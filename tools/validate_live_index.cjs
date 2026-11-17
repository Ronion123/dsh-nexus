// Validate the LIVE index downloaded from jsDelivr with DSH's own parser.
const fs = require('node:fs');
const m = require('C:/Ronin/software/DeepSeek Harness/resources/app.asar/dsh/node_modules/@deepseek-ai/dsh-plugin-market-index/lib/index.js');

const raw = JSON.parse(fs.readFileSync('C:/Users/Ronin/Desktop/桌宠设计/_live_index.json', 'utf8'));
const INDEX_URL = 'https://cdn.jsdelivr.net/gh/Ronion123/dsh-nexus@release-1.0.0/site/index.json';
const out = m.parseMarketIndex(raw, INDEX_URL);

console.log('LIVE INDEX VALID');
console.log('  plugins:', out.plugins.length);
for (const p of out.plugins) {
  console.log('  name    :', p.name);
  console.log('  icon    :', p.icon);
  console.log('  repo    :', p.repository && p.repository.url);
  console.log('  category:', p.metadata.category);
  for (const v of p.versions) {
    const t = m.marketInstallTarget(p.name, v);
    console.log('  version :', v.version, '| engines', JSON.stringify(v.engines));
    console.log('  install :', t.spec);
  }
}
// Confirm the icon URL that the client will actually request
const iconUrl = out.plugins[0].icon;
console.log('\n  icon URL resolves to that absolute address above; verify it is reachable.');
