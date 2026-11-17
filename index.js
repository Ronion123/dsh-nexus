/**
 * Host half of the "Nexus" pet-pack bundle.
 *
 * This bundle ships no pet engine of its own. It installs a dsh-pet "pet pack"
 * (config + VP9-alpha animations + pose stickers + avatar + character sheet) into
 * dsh-pet's user data root; dsh-pet then renders it with its full feature set:
 * drag/throw physics, the right-click action menu, work-status linkage to session
 * events, whisper/chat bubbles, balance animations, sleeping and multi-pet support.
 *
 * Installation is content-addressed and idempotent: a file is written only when its
 * bytes differ, so a user's hand-edited pack config survives every Host boot. A
 * byte-stable marker records the bundle version and the clips it installed, which is
 * what lets a later version remove clips it no longer ships without touching files
 * the user added.
 */
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { homedir } from 'node:os';

const PACKAGE_DIR = dirname(fileURLToPath(import.meta.url));
const PACK_DATA_DIR = join(PACKAGE_DIR, 'pet-pack');
const MARKER_NAME = '.dsh-nexus.json';
const BUNDLE_VERSION = '2.0.0';

/** dsh-pet resolves its data root as join(resolveDshHome(), 'dsh-pet'). */
function resolveDshHome() {
  const explicit = process.env.DSH_HOME;
  if (explicit && explicit.trim() !== '') return explicit.trim();
  return join(homedir(), '.dsh');
}

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

/** Copy a directory tree, writing only changed files. Mutates the summary. */
function installTree(srcDir, destDir, summary) {
  if (!existsSync(srcDir)) return;
  mkdirSync(destDir, { recursive: true });
  for (const entry of readdirSync(srcDir, { withFileTypes: true })) {
    const src = join(srcDir, entry.name);
    const dest = join(destDir, entry.name);
    if (entry.isDirectory()) {
      installTree(src, dest, summary);
      continue;
    }
    if (!entry.isFile()) continue;
    const bytes = readFileSync(src);
    if (existsSync(dest) && statSync(dest).isFile() && sha256(readFileSync(dest)) === sha256(bytes)) {
      summary.unchanged += 1;
      continue;
    }
    writeFileSync(dest, bytes);
    summary.written += 1;
  }
}

/** Remove clips a previous version installed but this version no longer ships. */
function removeStaleClips(animDir, previous, current) {
  if (!previous || !Array.isArray(previous.clips)) return 0;
  const keep = new Set(current);
  let removed = 0;
  for (const name of previous.clips) {
    if (keep.has(name)) continue;
    const target = resolve(animDir, name);
    if (dirname(target) !== resolve(animDir)) continue; // never leave the pack directory
    try {
      if (existsSync(target)) {
        rmSync(target);
        removed += 1;
      }
    } catch {
      // A file locked by a decoder is harmless; the next boot retries.
    }
  }
  return removed;
}

function listClips(dir) {
  if (!existsSync(dir)) return [];
  return readdirSync(dir).filter((name) => name.endsWith('.webm')).sort();
}

/** Install the pet pack into dsh-pet's user data directory. */
function installPetPack() {
  const userRoot = join(resolveDshHome(), 'dsh-pet');
  const petDir = join(userRoot, 'pet');
  const animDir = join(petDir, 'nexus-animation');
  const memeDir = join(petDir, 'nexus-memes');
  const markerPath = join(petDir, MARKER_NAME);

  let previous;
  try {
    previous = JSON.parse(readFileSync(markerPath, 'utf8'));
  } catch {
    previous = undefined;
  }

  const summary = { ok: true, written: 0, unchanged: 0, removed: 0, root: userRoot };
  try {
    mkdirSync(petDir, { recursive: true });
    mkdirSync(animDir, { recursive: true });
    mkdirSync(memeDir, { recursive: true });

    installTree(join(PACK_DATA_DIR, 'config'), petDir, summary);
    installTree(join(PACK_DATA_DIR, 'animation'), animDir, summary);
    installTree(join(PACK_DATA_DIR, 'memes'), memeDir, summary);

    const clips = listClips(animDir);
    summary.removed = removeStaleClips(animDir, previous, clips);

    // No timestamp: a byte-stable marker keeps repeated boots fully idempotent.
    const marker = JSON.stringify({ version: BUNDLE_VERSION, bundle: 'dsh-nexus', clips }, null, 2) + '\n';
    if (!existsSync(markerPath) || readFileSync(markerPath, 'utf8') !== marker) {
      writeFileSync(markerPath, marker);
      summary.written += 1;
    }
  } catch (error) {
    summary.ok = false;
    summary.reason = error instanceof Error ? error.message : String(error);
  }
  return summary;
}

/**
 * Locate the installed dsh-pet package from this plugin's own node_modules
 * (both live under the same profile), then fall back to the profile root.
 */
function findDshPet() {
  const candidates = [
    join(PACKAGE_DIR, '..', 'dsh-pet'),
    process.env.DSH_PROFILE_DIR ? join(process.env.DSH_PROFILE_DIR, 'node_modules', 'dsh-pet') : '',
  ].filter((p) => p !== '');
  for (const dir of candidates) {
    if (existsSync(join(dir, 'assets'))) return dir;
  }
  return null;
}

/**
 * Replace dsh-pet's built-in click sound with this pack's war cry.
 *
 * Why this is a file replacement rather than a pet-pack feature: dsh-pet codes
 * the sound URL as a constant on the client and its `/sound` route serves only
 * the package directory ("no user-directory override"), and DSH's webServer
 * rejects duplicate route registrations, so a plugin cannot shadow that route.
 * We therefore swap the package file itself, which is the only supported channel.
 *
 * Idempotent and self-healing: the original is backed up once, and every Host
 * boot re-applies the wav if a dsh-pet reinstall/upgrade restored the original.
 */
function installClickSound(dshPet) {
  const summary = { ok: true, applied: false, reason: undefined };
  const wavSrc = join(PACK_DATA_DIR, 'sound', 'click-duck.wav');
  if (!existsSync(wavSrc)) {
    summary.ok = false;
    summary.reason = 'bundled wav missing';
    return summary;
  }

  const target = dshPet ? join(dshPet, 'assets', 'sound', 'click-duck.wav') : null;
  if (!target || !existsSync(dirname(target))) {
    summary.ok = false;
    summary.reason = 'dsh-pet assets/sound not found';
    return summary;
  }

  try {
    const wav = readFileSync(wavSrc);
    const backup = target + '.dsh-nexus-original';
    const currentSame = existsSync(target) && sha256(readFileSync(target)) === sha256(wav);
    if (currentSame) {
      summary.applied = true; // already ours
      return summary;
    }
    // Keep the stock file once so the user can restore it.
    if (!existsSync(backup) && existsSync(target)) writeFileSync(backup, readFileSync(target));
    writeFileSync(target, wav);
    summary.applied = true;
  } catch (error) {
    summary.ok = false;
    summary.reason = error instanceof Error ? error.message : String(error);
  }
  return summary;
}

/**
 * Replace dsh-pet's shared artwork with this character's icons.
 *
 * Three seats all read package files that dsh-pet serves without any user-dir
 * override, so a pet pack cannot supply them:
 *   assets/logo.png          /logo  -> settings avatar, tray badge, window and
 *                                     taskbar icon (taskbar/window read the file
 *                                     directly in the Electron helper)
 *   assets/pic/notify-*.png  /pic/* -> system notification icons
 *
 * Same idempotent, self-healing contract as the click sound: back up once, then
 * re-apply on every boot so a dsh-pet reinstall cannot silently revert them.
 */
const BRAND_FILES = [
  ['logo.png', ['assets', 'logo.png']],
  ['notify-done.png', ['assets', 'pic', 'notify-done.png']],
  ['notify-error.png', ['assets', 'pic', 'notify-error.png']],
  ['notify-truncated.png', ['assets', 'pic', 'notify-truncated.png']],
  ['notify-approval.png', ['assets', 'pic', 'notify-approval.png']],
  ['notify-question.png', ['assets', 'pic', 'notify-question.png']],
  ['notify-test.png', ['assets', 'pic', 'notify-test.png']],
];

function installBranding(dshPet) {
  const summary = { ok: true, applied: 0, failed: [] };
  if (!dshPet) {
    summary.ok = false;
    summary.failed.push('dsh-pet not found');
    return summary;
  }
  for (const [srcName, relParts] of BRAND_FILES) {
    const src = join(PACK_DATA_DIR, 'icon', srcName);
    const target = join(dshPet, ...relParts);
    if (!existsSync(src)) {
      summary.failed.push(srcName + ': bundled file missing');
      continue;
    }
    try {
      const bytes = readFileSync(src);
      if (existsSync(target) && sha256(readFileSync(target)) === sha256(bytes)) {
        summary.applied += 1; // already ours
        continue;
      }
      const backup = target + '.dsh-nexus-original';
      if (!existsSync(backup) && existsSync(target)) writeFileSync(backup, readFileSync(target));
      writeFileSync(target, bytes);
      summary.applied += 1;
    } catch (error) {
      summary.failed.push(srcName + ': ' + (error instanceof Error ? error.message : String(error)));
    }
  }
  if (summary.failed.length > 0) summary.ok = false;
  return summary;
}

/**
 * Hide dsh-pet's bundled "blue maid" so only this character shows.
 *
 * dsh-pet ships with `pets: [{ id: 'main', name: '蓝毛小女仆', display: 'both' }]`
 * and, for a user who never edited `main-config.jsonc`, that maid appears
 * alongside this pack's pet. The pet-pack format has no "hide the default"
 * switch, so the only lever is the user config's `display` field.
 *
 * Two hard constraints shape this function:
 *  1. `main-config.jsonc` is JSONC: it may hold `//` and block comments the user
 *     wrote. We therefore edit the parsed value and re-serialise only when the
 *     parsed shape actually changed, keeping a one-time backup of the original
 *     text so the user can always get their comments back.
 *  2. `main` must keep existing. Deleting the entry makes dsh-pet fall back to
 *     its built-in defaults, which brings the maid back — so we set
 *     `display: 'none'` instead of removing anything.
 *
 * Idempotent: once display is 'none' the file is left untouched on later boots.
 */
function hideBundledMaid(userRoot) {
  const summary = { ok: true, applied: false, reason: undefined };
  const configPath = join(userRoot, 'main-config.jsonc');
  const legacyPath = join(userRoot, 'main-config.json');
  let target = existsSync(configPath) ? configPath : existsSync(legacyPath) ? legacyPath : configPath;

  // No user config at all: the maid would run on dsh-pet's defaults, so write a
  // minimal one that keeps `main` present but hidden.
  let current = null;
  if (existsSync(target)) {
    try {
      current = parseJsonc(readFileSync(target, 'utf8'));
    } catch (error) {
      summary.ok = false;
      summary.reason = 'user config unparsable, left untouched: ' +
        (error instanceof Error ? error.message : String(error));
      return summary;
    }
  }
  if (!current || typeof current !== 'object') current = {};
  const pets = Array.isArray(current.pets) ? current.pets : [];

  let main = pets.find((p) => p && p.id === 'main');
  let dirty = false;
  if (!main) {
    // No main entry: dsh-pet synthesises one from its defaults (the maid, shown).
    main = {
      id: 'main',
      name: '（已停用）蓝毛小女仆',
      size: 462,
      balanceEnabled: true,
      whisperEnabled: true,
      workStatusEnabled: true,
      fixedEnabled: false,
      display: 'none',
      position: { corner: 'top-right', marginX: 24, marginY: 100 },
    };
    current.pets = [...pets, main];
    dirty = true; // the file must be written even though `main` already reads none
  }

  if (main.display !== 'none') {
    main.display = 'none';
    dirty = true;
  }
  if (typeof main.name === 'string' && !main.name.startsWith('（已停用）')) {
    main.name = '（已停用）' + main.name;
    dirty = true;
  }

  // Already hidden and present in the file: nothing to write.
  if (!dirty && existsSync(target)) {
    summary.applied = true;
    return summary;
  }

  try {
    // Keep the user's original text once, so JSONC comments are recoverable.
    const backup = target + '.dsh-nexus-before-hide';
    if (existsSync(target) && !existsSync(backup)) {
      writeFileSync(backup, readFileSync(target));
    }
    writeFileSync(target, JSON.stringify(current, null, 2) + '\n');
    summary.applied = true;
  } catch (error) {
    summary.ok = false;
    summary.reason = error instanceof Error ? error.message : String(error);
  }
  return summary;
}

/** Minimal JSONC reader: strips // and block comments outside strings. */
function parseJsonc(text) {
  let out = '';
  let i = 0;
  let inString = false;
  const n = text.length;
  while (i < n) {
    const c = text[i];
    if (inString) {
      out += c;
      if (c === '\\' && i + 1 < n) {
        out += text[i + 1];
        i += 2;
        continue;
      }
      if (c === '"') inString = false;
      i += 1;
      continue;
    }
    if (c === '"') {
      inString = true;
      out += c;
      i += 1;
      continue;
    }
    if (c === '/' && i + 1 < n && text[i + 1] === '/') {
      while (i < n && text[i] !== '\n') i += 1;
      continue;
    }
    if (c === '/' && i + 1 < n && text[i + 1] === '*') {
      i += 2;
      while (i + 1 < n && !(text[i] === '*' && text[i + 1] === '/')) i += 1;
      i += 2;
      continue;
    }
    out += c;
    i += 1;
  }
  return JSON.parse(out);
}

export const inject = [];

/**
 * Apply every one-shot effect. Safe to call repeatedly: each step compares content
 * hashes and skips work that is already applied.
 *
 * @param {object} [ctx] Host context; only `logger` is used, and only for reporting.
 * @returns {object} A summary of each step, for logging.
 */
function applyAll(ctx) {
  const result = installPetPack();
  // Resolve the dsh-pet data root the same way installPetPack does.
  const userRoot = join(resolveDshHome(), 'dsh-pet');
  const maid = hideBundledMaid(userRoot);
  const dshPet = findDshPet();
  const sound = installClickSound(dshPet);
  const branding = installBranding(dshPet);
  try {
    const info = ctx?.logger?.info;
    const warn = ctx?.logger?.warn;
    if (typeof info === 'function') {
      if (result.ok) info(`[dsh-nexus] pet pack ready: ${JSON.stringify(result)}`);
      info(`[dsh-nexus] bundled maid hidden: ${JSON.stringify(maid)}`);
      info(`[dsh-nexus] click sound: ${JSON.stringify(sound)}`);
      info(`[dsh-nexus] branding: ${JSON.stringify(branding)}`);
    }
    if (typeof warn === 'function') {
      // Non-fatal: the Host must keep booting even when a dsh-pet dir is read-only.
      if (!result.ok) warn(`[dsh-nexus] pet pack install failed: ${result.reason}`);
      if (!maid.ok) warn(`[dsh-nexus] could not hide the bundled maid: ${maid.reason}`);
      if (!sound.ok) warn(`[dsh-nexus] click sound not applied: ${sound.reason}`);
      if (!branding.ok) warn(`[dsh-nexus] branding incomplete: ${branding.failed.join('; ')}`);
    }
  } catch {
    // A Host without a usable logger still works; the pack is simply not installed.
  }
  return { result, maid, sound, branding };
}

export function apply(ctx) {
  applyAll(ctx);

  // Installing or updating this bundle reconciles the profile without restarting
  // the process, so a plugin activated that way can mount long after boot — and may
  // mount while dsh-pet's files have already been served once. Re-apply on every
  // config reconciliation so a fresh install takes effect immediately instead of
  // waiting for the next DSH start. `applyAll` is idempotent: a redundant run only
  // costs a few file hashes.
  //
  // Registered through ctx.effect so unloading the plugin removes the listener
  // (ctx.on returns a disposer, the same contract dsh-pet relies on).
  try {
    if (typeof ctx?.on === 'function') {
      ctx.effect(() => {
        const off = ctx.on('app-boot/config-reload', () => {
          try {
            applyAll(ctx);
          } catch {
            // Never let a reconciler listener break the Host.
          }
        });
        return typeof off === 'function' ? off : () => {};
      }, 'dsh-nexus: reapply on config reload');
    }
  } catch {
    // Older Host without this event: the boot-time run is enough.
  }

  // All effects are one-shot file writes; nothing else to dispose.
  return () => {};
}
