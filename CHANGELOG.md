# Changelog

## 1.3.1

- Fix the bundle patch: `name` was the bare `dsh-nexus` while the package is
  `@roninxr/dsh-nexus`. The loader imports `name` from the profile root, so a
  registry install added the package but the row never mounted
  (`fiberPhase: null`), and none of the effects ran. It only worked when a
  stale unscoped `node_modules/dsh-nexus` happened to exist.
- Stop writing through hard links: dsh-pet's `assets/logo.png` and
  `assets/sound/click-duck.wav` are normally links into pnpm's
  content-addressable store, so replacing them in place rewrote the shared
  blob and changed what every other project installing that dsh-pet version
  received. The files are now unlinked before the write, leaving the store
  intact; the original is still backed up beside the file.
- Read the marker version from `package.json` instead of a hard-coded copy,
  which had drifted to `2.0.0`.
- `tools/validate_bundle.py` now checks that the patch name equals the
  package name, which is what would have caught the 1.3.0 bug.

## 1.3.0

- Notification icons now go into dsh-pet's user layer (`$DSH_HOME/dsh-pet/pic/`)
  instead of being written into the dsh-pet package. dsh-pet 0.4.9 reads that
  directory before its bundled assets specifically so custom icons survive a
  plugin upgrade, so reinstalling or upgrading dsh-pet no longer reverts them.
  Only `assets/logo.png` (tray badge and window icon, which the Electron helper
  reads straight off disk) and `assets/sound/click-duck.wav` still need the
  package swap, and those are re-applied on every boot.
- Fix `findDshPet()` for scoped installs: a package at
  `node_modules/@scope/dsh-nexus` has `dsh-pet` two levels up, not one, so the
  lookup silently failed and no branding was applied on a normal npm install.

## 1.2.2

- Effects now also run on `app-boot/config-reload`, not only when the plugin
  is first mounted. Installing the bundle activates it without restarting the
  process, so before this change the war cry, icons and the hidden maid only
  landed on the next DSH start. Every step is content-hash compared, so a
  redundant run costs a few file reads. The listener goes through
  `ctx.effect`, so unloading the plugin removes it.

## 1.2.1

- Fix: installing this plugin on a machine that had never edited dsh-pet's
  config left the bundled blue maid visible, so two pets appeared. The Host
  half now sets that pet's `display` to `none` itself: it creates a minimal
  `main-config.jsonc` when none exists, and when one does exist it parses
  the JSONC, changes only `display`, keeps every other field, and backs the
  original text up as `main-config.jsonc.dsh-nexus-before-hide` so user
  comments stay recoverable. `main` is never deleted, because dsh-pet falls
  back to its built-in defaults (the maid) when that entry is missing.

## 1.2.0

- Rebrand every icon seat that dsh-pet serves from its own package, which a
  pet pack cannot supply: the plugin logo (settings avatar, tray badge,
  window and taskbar icon) plus all six system-notification icons. The Host
  half backs the originals up once and re-applies on every boot, so a
  dsh-pet reinstall cannot silently revert them.
- The bundled 'blue maid' pet is hidden (display=none) so only Nexus shows.
  The entry is kept because dsh-pet falls back to its built-in defaults and
  would bring the maid back if `main` were deleted.

## 1.1.0

- Click sound is now the character's war cry instead of dsh-pet's stock
  duck quack. dsh-pet codes that URL as a client constant and its /sound
  route serves only the package directory, and DSH's webServer rejects a
  duplicate route registration, so the Host half swaps the package wav at
  boot (backing the original up once) and re-applies it after any dsh-pet
  reinstall.
- Dragging, throwing and ceiling bounces all use the flight pose, and the
  sprite points the way the cursor moves: a leftward drag shows the
  left-facing flight clip, a rightward drag the right-facing one. New
  `client.js` half watches pointer motion and drives `facing` through
  `/anim`, which previously stayed at whatever the pet last faced.
- Two new directional flight clips (36 total).

## 1.0.2

- Republish so the README shown on npmjs.com carries the v1.0.1 index URL
  (1.0.1 was packed before that tag existed).
- No runtime changes.

## 1.0.1

- Fix the index URL shipped in the published README: point at
  raw.githubusercontent (200, no redirect) instead of the stale jsDelivr URL,
  and correct the npm scope shown in install instructions.
- No runtime changes; the pet pack and Host half are byte-identical to 1.0.0.

## 1.0.0 — first release

- Ships the Nexus desktop pet as a dsh-pet character pack.
- Idle animation is the supplied 12-frame transparent loop GIF, encoded to
  VP9-alpha without re-timing so the artist's cadence is preserved.
- The nine-pose action sheet becomes nine point-playable actions in the
  right-click menu (`起手式` … `展翼式`).
- Five transparent high-resolution pose illustrations become the five form
  clips, the pose stickers, and the plugin avatar.
- Persona and all dialogue use the character's classic lines from `台词.md`.
- Host half installs the pack idempotently (content-hash comparison) and keeps
  a byte-stable marker so later releases can retire clips the user never added.
