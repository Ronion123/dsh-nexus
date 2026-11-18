# Changelog

## 1.4.3

- Make the form-change item respond within about a second. Measured against
  dsh-pet 0.4.9, `/menu/events` does not wake when a click arrives: a parked
  `wait=10000` request stays open the full ten seconds (`delivered` is always
  false) and the queued label is only readable when the request finally
  returns. So the wait window was the latency. It is now 1500ms, which lands a
  click on the pet in ~1s instead of ~10s.
- Re-register automatically when dsh-pet answers `unknown-owner`: the registry
  is in-memory and disappears whenever dsh-pet reloads, and the old loop would
  spin forever against a dead owner without ever restoring the item.

## 1.4.2

- Fix the form-change menu doing nothing. Two independent bugs:
  1. The pet routes were built from a guessed port (`DSH_WEB_PORT`, else
     `127.0.0.1:3000`). The Host binds a fresh random port each launch, so every
     request failed and the item silently did nothing. The origin now comes from
     `ctx.webServer.getOrigin()`.
  2. The menu payload used `items: [{ label }]`; dsh-pet's contract is
     `{ owner, labels: string[], target? }`. The registration was rejected with
     `invalid-labels`, so 更多 never showed the item. A rejection is now logged.
- The click listener holds `/menu/events?wait=10000` open instead of polling on a
  fixed interval, so a click that lands between polls is not missed.

## 1.4.1

- Fix the blue form's assets being unreachable. dsh-pet resolves clips as
  `pet/<asset-root>-animation/<clip>.webm`, where the asset root is the config
  file prefix — it never searches a shared directory. 1.4.0 installed every
  clip into `nexus-animation/`, so all 36 blue clips answered 404 while the
  configs still validated. The installer now writes per-root directories
  (`nexus-*` and `nexus-blue-*`) and the bundle's own layout mirrors that.

## 1.4.0

- Add the Blue Youth form as a second pet pack (`nexus-blue`): five poses
  (standing, battle, beam, beam-arrow, flight), a 9-frame idle loop, and nine
  action clips — 36 clips and 5 stickers in total.
- One-way transformation red -> blue, exposed as a third-party menu item
  (更多 -> dsh-nexus -> 变成蓝色青年形态). The switch plays the red form's
  `形态切换` clip and waits for `/playback?wait=ended` to report it finished
  before hiding red and showing blue, so the transformation runs to its end and
  blue appears standing where red was. No cross-fade, no two pets at once.
  `wait` is capped at 10000ms by dsh-pet and must be paired with `timeout`;
  the maximum is requested and a non-`ended` reply is treated as failure, so a
  rejected request can never be mistaken for an instant finish.
- The blue pack deliberately ships no form-shift clip: the change is
  one-directional, matching the source material.
- `tools/validate_pack.py` now validates every `*-config.json` in the pack
  rather than a single red config, and reports orphan assets across both.

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
