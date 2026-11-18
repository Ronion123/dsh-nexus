// Verify swapFile breaks a hard link instead of writing through it.
import { mkdtempSync, writeFileSync, readFileSync, statSync, linkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const { swapFile } = await import('../index.js');

const dir = mkdtempSync(join(tmpdir(), 'swapfile-test-'));
const storeBlob = join(dir, 'store-blob.png');   // simulates pnpm content store
const pkgFile = join(dir, 'package-logo.png');   // simulates node_modules file
const ORIGINAL = Buffer.from('ORIGINAL-DSH-PET-LOGO');
const REPLACEMENT = Buffer.from('NEXUS-LOGO');

writeFileSync(storeBlob, ORIGINAL);
linkSync(storeBlob, pkgFile);                    // hard link, like pnpm

console.log('before: pkgFile nlink =', statSync(pkgFile).nlink);

const summary = { ok: true, applied: 0, failed: [] };
swapFile(pkgFile, REPLACEMENT, summary, 'logo.png');

console.log('after : pkgFile nlink =', statSync(pkgFile).nlink);
console.log('summary:', JSON.stringify(summary));
console.log('package file content:', readFileSync(pkgFile, 'utf8'));
console.log('STORE blob content :', readFileSync(storeBlob, 'utf8'));
console.log(
  readFileSync(storeBlob, 'utf8') === ORIGINAL.toString()
    ? 'PASS: store blob untouched'
    : 'FAIL: store blob was modified',
);

// Idempotency: second call must not rewrite.
const before = readFileSync(pkgFile, 'utf8');
swapFile(pkgFile, REPLACEMENT, summary, 'logo.png');
console.log('second call changed file:', readFileSync(pkgFile, 'utf8') !== before);
console.log('backup created:', readFileSync(pkgFile + '.dsh-nexus-original', 'utf8') === ORIGINAL.toString());
