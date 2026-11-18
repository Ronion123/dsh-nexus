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
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, unlinkSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { homedir } from 'node:os';

const PACKAGE_DIR = dirname(fileURLToPath(import.meta.url));
const PACK_DATA_DIR = join(PACKAGE_DIR, 'pet-pack');
const MARKER_NAME = '.dsh-nexus.json';

/**
 * Marker version, read from the manifest so it can never drift from the release
 * the user actually installed (a hard-coded copy went stale once already).
 */
const BUNDLE_VERSION = (() => {
  try {
    return String(JSON.parse(readFileSync(join(PACKAGE_DIR, 'package.json'), 'utf8')).version ?? '0.0.0');
  } catch {
    return '0.0.0';
  }
})();

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

    // Assets are grouped per asset root, and the root is the config FILE PREFIX:
    // `/thumb/<root>/<clip>` only searches `pet/<root>-animation/`, never a shared
    // directory. The blue form therefore needs its own `-animation` and `-memes`
    // directories, or its clips 404 while the configs still look valid.
    installTree(join(PACK_DATA_DIR, 'config'), petDir, summary);
    for (const [srcDir, destDir] of [
      ['animation', 'nexus-animation'],
      ['memes', 'nexus-memes'],
      ['blue-animation', 'nexus-blue-animation'],
      ['blue-memes', 'nexus-blue-memes'],
    ]) {
      const dest = join(petDir, destDir);
      mkdirSync(dest, { recursive: true });
      installTree(join(PACK_DATA_DIR, srcDir), dest, summary);
    }

    const animDir = join(petDir, 'nexus-animation');
    const clips = listClips(animDir);
    summary.removed = removeStaleClips(animDir, previous, clips);

    // No timestamp: a byte-stable marker keeps repeated boots fully idempotent.
    const marker = JSON.stringify({
      version: BUNDLE_VERSION,
      bundle: 'dsh-nexus',
      clips,
      blueClips: listClips(join(petDir, 'nexus-blue-animation')),
    }, null, 2) + '\n';
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
 * Locate the installed dsh-pet package.
 *
 * A scoped install puts this plugin at `<profile>/node_modules/@scope/dsh-nexus`,
 * so the sibling directory is one level up and then `dsh-pet` — not `..` + name.
 * Try every plausible anchor and keep the first directory that owns `assets/`.
 */
function findDshPet() {
  const candidates = [
    // unscoped: <profile>/node_modules/dsh-nexus -> <profile>/node_modules/dsh-pet
    join(PACKAGE_DIR, '..', 'dsh-pet'),
    // scoped:   <profile>/node_modules/@scope/dsh-nexus -> .../node_modules/dsh-pet
    join(PACKAGE_DIR, '..', '..', 'dsh-pet'),
    process.env.DSH_PROFILE_DIR ? join(process.env.DSH_PROFILE_DIR, 'node_modules', 'dsh-pet') : '',
    process.env.DSH_PROFILE_DIR ? join(process.env.DSH_PROFILE_DIR, 'node_modules', '@deepseek-ai', 'dsh-pet') : '',
  ].filter((p) => p !== '');
  for (const dir of candidates) {
    if (existsSync(join(dir, 'assets'))) return dir;
  }
  return null;
}

/**
 * Install this character's icons.
 *
 * dsh-pet 0.4.9 gives these two asset families different override rules, and the
 * difference decides whether an icon survives a dsh-pet upgrade:
 *
 *   /pic/<file>  -> `$DSH_HOME/dsh-pet/pic/` wins over the package directory,
 *                   explicitly so custom icons outlive a plugin upgrade.
 *                   Notification icons therefore go there and are never written
 *                   into the dsh-pet package.
 *
 *   /logo, /sound -> package directory only (no user-layer lookup), and the
 *                   Electron helper reads `assets/logo.png` straight off disk for
 *                   the tray badge and window icon. Those two files must be
 *                   replaced in the package, backed up once and re-applied on
 *                   every boot so a reinstall cannot silently revert them.
 */
const NOTIFY_ICONS = [
  'notify-done.png',
  'notify-error.png',
  'notify-truncated.png',
  'notify-approval.png',
  'notify-question.png',
  'notify-test.png',
];

/** Files inside the dsh-pet package that must be swapped (no user-layer option). */
const PACKAGE_ASSETS = [
  ['logo.png', ['assets', 'logo.png']],
  ['click-duck.wav', ['assets', 'sound', 'click-duck.wav']],
];

/**
 * Copy `bytes` onto `target` once, keeping the original beside it.
 *
 * A package file under `node_modules` is normally a hard link into pnpm's
 * content-addressable store, so writing through it rewrites the shared blob and
 * silently changes what every other project installing the same version gets.
 * When the link count shows more than one, drop the link first and write a fresh
 * file, which leaves the store untouched.
 */
export function swapFile(target, bytes, summary, label) {
  try {
    const existed = existsSync(target);
    const current = existed ? readFileSync(target) : null;
    if (current !== null && sha256(current) === sha256(bytes)) {
      summary.applied += 1; // already ours
      return;
    }
    const backup = target + '.dsh-nexus-original';
    if (!existsSync(backup) && current !== null) writeFileSync(backup, current);

    if (existed) {
      let links = 1;
      try {
        links = statSync(target).nlink || 1;
      } catch {
        // Unreadable metadata: assume a single link and write in place.
      }
      if (links > 1) {
        try {
          unlinkSync(target);
        } catch {
          // Locked (e.g. the running Electron helper holds the logo): fall back
          // to an in-place write rather than leaving branding unapplied.
        }
      }
    }
    try {
      writeFileSync(target, bytes);
    } catch (error) {
      // A failed unlink+write must not leave the file missing; restore the backup.
      if (!existsSync(target) && existsSync(backup)) writeFileSync(target, readFileSync(backup));
      throw error;
    }
    summary.applied += 1;
  } catch (error) {
    summary.failed.push(label + ': ' + (error instanceof Error ? error.message : String(error)));
  }
}

function installBranding(dshPet, userRoot) {
  const summary = { ok: true, applied: 0, failed: [] };

  // --- notification icons: user layer, survives dsh-pet upgrades ------------
  const picDir = join(userRoot, 'pic');
  try {
    mkdirSync(picDir, { recursive: true });
  } catch (error) {
    summary.failed.push('pic dir: ' + (error instanceof Error ? error.message : String(error)));
  }
  for (const name of NOTIFY_ICONS) {
    const src = join(PACK_DATA_DIR, 'icon', name);
    if (!existsSync(src)) {
      summary.failed.push(name + ': bundled file missing');
      continue;
    }
    swapFile(join(picDir, name), readFileSync(src), summary, name);
  }

  // --- logo + click sound: package layer only -------------------------------
  if (!dshPet) {
    summary.failed.push('dsh-pet package not found (logo/sound not applied)');
  } else {
    for (const [srcName, relParts] of PACKAGE_ASSETS) {
      const src = join(PACK_DATA_DIR, srcName === 'click-duck.wav' ? 'sound' : 'icon', srcName);
      if (!existsSync(src)) {
        summary.failed.push(srcName + ': bundled file missing');
        continue;
      }
      swapFile(join(dshPet, ...relParts), readFileSync(src), summary, srcName);
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

/* ------------------------------------------------------------------------- *
 * One-way form change: red youth -> blue youth.
 *
 * dsh-pet derives a pet's asset root from its config FILE NAME, so one instance
 * cannot swap art sets at runtime. The two forms are therefore two pets, and the
 * switch is a timed hand-off between them:
 *
 *   1. play the red form's shift clip,
 *   2. wait for it to FINISH on the rendering side (/playback?wait=ended),
 *   3. hide red and show blue at the same spot, in that order and in one tick.
 *
 * Step 3 is what keeps the motion continuous: the blue pet appears only after the
 * transformation animation has run to its end, so the user sees "the shift plays,
 * and blue is standing where red was" rather than a cross-fade or a double pet.
 *
 * The hand-off is one-way by construction: nothing ever shows red again, and the
 * blue pack ships no form-shift clip. A user who wants red back reselects it in
 * Settings, which we do not intercept.
 * ------------------------------------------------------------------------- */

/** Clips and pets that describe this transition. */
const FORM = {
  redPet: 'nexus',
  bluePet: 'nexus-blue',
  shiftClip: '形态切换',
  // Margin after the clip ends: lets the last frame settle before the swap so the
  // blue idle does not appear to start mid-motion.
  settleMs: 60,
};

/** In-flight switch, so a double click cannot start two hand-offs. */
let switching = false;

/**
 * Origin of the running Host's HTTP server, discovered once on first use.
 *
 * The pet routes live on whatever port the Host bound (a fresh random port each
 * launch), so this must come from `ctx.webServer.getOrigin()` — never from a guess.
 * Guessing a port makes every call fail silently and the menu item does nothing.
 */
let cachedOrigin = null;

/** @param {object} [ctx] Host context providing `webServer`. */
async function petsBaseUrl(ctx) {
  if (cachedOrigin !== null) return cachedOrigin + '/dsh-pet-7340';
  const webServer = ctx?.webServer ?? (typeof ctx?.get === 'function' ? ctx.get('webServer') : undefined);
  if (webServer && typeof webServer.getOrigin === 'function') {
    cachedOrigin = webServer.getOrigin().replace(/\/$/, '');
    return cachedOrigin + '/dsh-pet-7340';
  }
  throw new Error('webServer.getOrigin() unavailable: cannot locate dsh-pet routes');
}

/** Read the merged config so we can see what is currently displayed. */
async function readConfig(base) {
  const res = await fetch(`${base}/config`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`config ${res.status}`);
  return res.json();
}

/** Which of the two pets is visible right now, according to the config. */
function visibleForm(cfg) {
  const shown = (entry, id) => {
    const pets = cfg?.[entry]?.pets;
    if (!Array.isArray(pets)) return false;
    const p = pets.find((x) => x && x.id === id);
    return Boolean(p) && p.display !== 'none';
  };
  if (shown('nexus-blue', FORM.bluePet)) return 'blue';
  if (shown('nexus', FORM.redPet)) return 'red';
  return 'none';
}

/** Play a clip on one pet and resolve when the renderer reports it ended. */
async function playAndWait(base, petId, clip) {
  const started = await fetch(`${base}/anim?pet=${encodeURIComponent(petId)}&surface=any`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify({ name: clip }),
  });
  if (!started.ok) throw new Error(`anim ${started.status}`);
  const body = await started.json();
  if (!body?.ok || !body.playbackId) throw new Error(body?.reason ?? 'anim rejected');

  // `wait=ended` blocks until the renderer reports the cue finished, so the swap
  // happens after the animation rather than on a guessed timer.
  //
  // dsh-pet requires `wait` and `timeout` together, and caps the timeout at
  // 10000ms (a larger value is answered with bad-request, which would look like an
  // instant finish and swap mid-animation). Ask for the maximum and treat a
  // timeout reply as "not finished" rather than as success.
  const done = await fetch(
    `${base}/playback/${encodeURIComponent(body.playbackId)}?wait=ended&timeout=10000`,
    { cache: 'no-store' },
  );
  if (!done.ok) throw new Error(`playback ${done.status}`);
  const settled = await done.json();
  const status = settled?.playback?.status ?? settled?.status;
  if (status !== 'ended') {
    throw new Error(`shift clip not finished (status ${status ?? 'unknown'})`);
  }
  return body.playbackId;
}

/** Show one form and hide the other, writing both before either is rendered. */
async function setForm(base, form) {
  const show = form === 'blue' ? FORM.bluePet : FORM.redPet;
  const hide = form === 'blue' ? FORM.redPet : FORM.bluePet;
  // Order matters: reveal first, then hide, so a failed second call still leaves
  // exactly one pet visible instead of none.
  for (const [petId, display] of [[show, 'both'], [hide, 'none']]) {
    const res = await fetch(`${base}/pet-display`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
      // dsh-pet's body takes `id` (the pet instance), not `pet`.
      body: JSON.stringify({ id: petId, display }),
    });
    if (!res.ok) throw new Error(`pet-display ${petId} ${res.status}`);
    const out = await res.json();
    if (out?.ok === false) throw new Error(out.reason ?? 'pet-display rejected');
  }
}

/**
 * Perform the one-way red -> blue transformation.
 *
 * @returns {Promise<{ok: boolean, reason?: string, from?: string}>}
 */
async function transformToBlue(ctx) {
  if (switching) return { ok: false, reason: 'already-switching' };
  switching = true;
  try {
    const base = await petsBaseUrl(ctx);
    const cfg = await readConfig(base);
    const current = visibleForm(cfg);
    if (current === 'blue') return { ok: false, reason: 'already-blue' };
    if (current !== 'red') return { ok: false, reason: 'red-not-visible' };

    await playAndWait(base, FORM.redPet, FORM.shiftClip);
    await new Promise((r) => setTimeout(r, FORM.settleMs));
    await setForm(base, 'blue');
    return { ok: true, from: 'red' };
  } catch (error) {
    return { ok: false, reason: error instanceof Error ? error.message : String(error) };
  } finally {
    switching = false;
  }
}

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
  // Branding covers both layers: notification icons in the user directory, and
  // the logo + click sound inside the package (dsh-pet offers no user-layer
  // override for those two, and the Electron helper reads the logo off disk).
  const branding = installBranding(dshPet, userRoot);
  try {
    const info = ctx?.logger?.info;
    const warn = ctx?.logger?.warn;
    if (typeof info === 'function') {
      if (result.ok) info(`[dsh-nexus] pet pack ready: ${JSON.stringify(result)}`);
      info(`[dsh-nexus] bundled maid hidden: ${JSON.stringify(maid)}`);
      info(`[dsh-nexus] branding: ${JSON.stringify(branding)}`);
    }
    if (typeof warn === 'function') {
      // Non-fatal: the Host must keep booting even when a dsh-pet dir is read-only.
      if (!result.ok) warn(`[dsh-nexus] pet pack install failed: ${result.reason}`);
      if (!maid.ok) warn(`[dsh-nexus] could not hide the bundled maid: ${maid.reason}`);
      if (!branding.ok) warn(`[dsh-nexus] branding incomplete: ${branding.failed.join('; ')}`);
    }
  } catch {
    // A Host without a usable logger still works; the pack is simply not installed.
  }
  return { result, maid, branding };
}

export function apply(ctx) {
  applyAll(ctx);

  // Register the one-way form change in dsh-pet's third-party context menu.
  // dsh-pet owns the menu; a plugin contributes items under its own owner name and
  // learns about clicks by polling /menu/events with that same owner.
  try {
    if (ctx?.timer && typeof ctx.timer.interval === 'function') {
      ctx.effect(() => {
        let stopped = false;
        void (async () => {
          let base;
          try {
            base = await petsBaseUrl(ctx);
          } catch (error) {
            // No webServer origin: dsh-pet's routes are unreachable, so there is
            // nothing to register. Log it rather than failing silently.
            try {
              ctx?.logger?.warn?.(
                `[dsh-nexus] form-change menu unavailable: ${error instanceof Error ? error.message : String(error)}`,
              );
            } catch {
              /* logger unusable */
            }
            return;
          }
          // The label is what the user clicks in 更多 -> dsh-nexus.
          try {
            // dsh-pet's register payload is { owner, labels: string[], target? }.
            // `labels` is a flat string array (not objects); sending anything else
            // is answered with invalid-labels and the item never appears in 更多.
            const reg = await fetch(`${base}/menu/item`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json; charset=utf-8' },
              body: JSON.stringify({
                owner: 'dsh-nexus',
                labels: ['变成蓝色青年形态'],
                target: 'both',
              }),
            });
            const regBody = await reg.json().catch(() => ({}));
            if (regBody?.ok === false) {
              ctx?.logger?.warn?.(
                `[dsh-nexus] menu item rejected: ${regBody.reason ?? 'unknown'}`,
              );
              return;
            }
          } catch {
            return; // dsh-pet absent: nothing to contribute to
          }

          // dsh-pet delivers a click to whichever `/menu/events` request is parked.
          // A short fixed interval misses clicks that land between two polls, so
          // hold the request open instead: the server parks it and answers as soon
          // as a click arrives (or after its own wait cap).
          const poll = async () => {
            while (!stopped) {
              try {
                const res = await fetch(
                  `${base}/menu/events?owner=dsh-nexus&wait=10000`,
                  { cache: 'no-store' },
                );
                if (!res.ok) {
                  await new Promise((r) => setTimeout(r, 1000));
                  continue;
                }
                const body = await res.json();
                // `events` is a label -> payload map; a null value still means the
                // item was clicked (the registry only records the label).
                const events = body?.events;
                if (events && typeof events === 'object') {
                  for (const label of Object.keys(events)) {
                    if (label === '变成蓝色青年形态') {
                      void transformToBlue(ctx);
                    }
                  }
                }
              } catch {
                // dsh-pet went away; back off briefly, keep waiting.
                await new Promise((r) => setTimeout(r, 2000));
              }
            }
          };
          void poll();
          return () => {
            stopped = true;
            // Best effort: leave no stale menu entry behind.
            void fetch(`${base}/menu/item?owner=dsh-nexus`, { method: 'DELETE' }).catch(() => {});
          };
        })();
        return () => { stopped = true; };
      }, 'dsh-nexus: form change menu');
    }
  } catch {
    // Older Host without a timer service: the menu entry is simply not offered.
  }

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
