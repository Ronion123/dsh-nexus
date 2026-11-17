# Changelog

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
